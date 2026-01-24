document.addEventListener('DOMContentLoaded', async () => {
  const DEBUG = true;
  const log = (...args) => DEBUG && console.log("[Caption][popup]", ...args);
  const subtitleBtn = document.getElementById('subtitleBtn');
  const recordBtn = document.getElementById('recordBtn');
  const toggle = document.getElementById('toggle-enabled');
  const videoList = document.getElementById('video-list');
  const progress = document.getElementById('record-progress');
  const progressBar = document.getElementById('record-bar');
  const timeLabel = document.getElementById('time-label');

  // 初始状态
  const state = (await chrome.storage.local.get('captionState')).captionState || { enabled: true, subtitleOn: false, recordingOn: false, recordingStartedAt: 0 };
  toggle.checked = !!state.enabled;
  subtitleBtn.textContent = state.subtitleOn ? '字幕已开' : '字幕未开';
  recordBtn.textContent = state.recordingOn ? '停止录音' : '开始录音';
  let startTime = state.recordingOn && state.recordingStartedAt ? state.recordingStartedAt : 0;
  let timer = null;
  let busy = false;

  // ========= WAV.JS 同步 & 错误修复相关 begin ==========

  function formatDuration(ms) {
    // 确保和 wav.js、其他前端逻辑格式一致
    const totalSec = Math.max(0, Math.floor(ms / 1000));
    const hh = Math.floor(totalSec / 3600);
    const mm = Math.floor((totalSec % 3600) / 60);
    const ss = totalSec % 60;
    const pad = (n) => String(n).padStart(2, '0');
    if (hh > 0) return `${pad(hh)}:${pad(mm)}:${pad(ss)}`;
    return `${pad(mm)}:${pad(ss)}`;
  }

  function renderProgress(ms) {
    timeLabel.textContent = formatDuration(ms);
  }
  function startProgress() {
    if (!startTime) startTime = Date.now();
    progressBar.classList.add('recording');
    if (timer) clearInterval(timer);
    timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      renderProgress(elapsed);
    }, 200);
  }
  function stopProgress() {
    if (timer) { clearInterval(timer); timer = null; }
    renderProgress(0);
    progressBar.classList.remove('recording');
    progress.style.display = 'none';
  }

  // ========= WAV.JS 同步 & 错误修复相关 end ==========

  // 启用开关变更
  toggle.addEventListener('change', async () => {
    const enabled = toggle.checked;
    // 直接同步状态
    state.enabled = enabled;
    await chrome.storage.local.set({ captionState: { ...state } });
    // 重新初始化状态
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.id) chrome.tabs.sendMessage(tab.id, { type: 'INIT_CAPTION' });
    } catch (err) {
      log("INIT_CAPTION send fail", err);
    }
  });

  // 字幕按钮
  subtitleBtn.addEventListener('click', async () => {
    state.subtitleOn = !state.subtitleOn;
    await chrome.storage.local.set({ captionState: { ...state } });
    chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
      if (tab && tab.id) chrome.tabs.sendMessage(tab.id, { type: 'TOGGLE_SUBTITLE' });
    });
    subtitleBtn.textContent = state.subtitleOn ? '字幕已开' : '字幕未开';
  });

  // 录音按钮
  recordBtn.addEventListener('click', async () => {
    log("record button clicked");
    if (busy) return;
    busy = true;
    recordBtn.disabled = true;

    const wasRecording = state.recordingOn;
    log("wasRecording=", wasRecording);

    try {
      // UI 乐观更新，保持和 wav.js 记录同步
      if (!wasRecording) {
        state.recordingOn = true;
        state.recordingStartedAt = Date.now();
        recordBtn.textContent = '停止录音';
        progress.style.display = 'block';
        startTime = state.recordingStartedAt;
        renderProgress(0);
        startProgress();
      } else {
        state.recordingOn = false;
        state.recordingStartedAt = 0;
        recordBtn.textContent = '开始录音';
        stopProgress();
      }

      // 向 background 请求录音状态
      let response = null;
      if (!wasRecording) {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab?.id) throw new Error('No active tab');
        log("getting streamId for tab", tab.id);
        const streamId = await chrome.tabCapture.getMediaStreamId({ targetTabId: tab.id });
        log("got streamId length=", String(streamId || '').length);
        // 修复: START_RECORDING 请求接口结构保持和 background/wav.js 逻辑一致
        response = await chrome.runtime.sendMessage({ type: 'START_RECORDING', streamId, tabId: tab.id });
      } else {
        response = await chrome.runtime.sendMessage({ type: 'STOP_RECORDING' });
      }
      log("background response:", response);

      // 校验 background 返回（同步和出错时保持一致）
      if (!response?.success && !wasRecording) {
        state.recordingOn = false;
        state.recordingStartedAt = 0;
        recordBtn.textContent = '开始录音';
        stopProgress();
      }
    } catch (err) {
      console.error('Failed to toggle recording:', err);
      // 回滚UI
      if (!wasRecording) {
        state.recordingOn = false;
        state.recordingStartedAt = 0;
        recordBtn.textContent = '开始录音';
        stopProgress();
      }
    } finally {
      setTimeout(() => { busy = false; recordBtn.disabled = false; }, 300);
    }
  });

  // 监听后台的录音进度与状态，和 wav.js 结构同步
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg?.type === 'RECORDING_STATE') {
      if (msg.active) {
        progress.style.display = 'block';
        startTime = msg.startedAt || Date.now();
        renderProgress(Date.now() - startTime);
        startProgress();
        state.recordingOn = true;
        state.recordingStartedAt = startTime;
        recordBtn.textContent = '停止录音';
      } else {
        stopProgress();
        if (typeof msg.durationMs === 'number') {
          renderProgress(msg.durationMs);
        }
        state.recordingOn = false;
        state.recordingStartedAt = 0;
        recordBtn.textContent = '开始录音';
      }
    }
  });

  // storage 变更同步
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local') return;
    if (!changes.captionState) return;
    const next = changes.captionState.newValue;
    if (!next) return;
    state.enabled = next.enabled;
    state.subtitleOn = next.subtitleOn;
    state.recordingOn = next.recordingOn;
    state.recordingStartedAt = next.recordingStartedAt || 0;
    toggle.checked = !!state.enabled;
    subtitleBtn.textContent = state.subtitleOn ? '字幕已开' : '字幕未开';
    recordBtn.textContent = state.recordingOn ? '停止录音' : '开始录音';
    if (state.recordingOn) {
      progress.style.display = 'block';
      startTime = state.recordingStartedAt || Date.now();
      renderProgress(Date.now() - startTime);
      startProgress();
    } else {
      stopProgress();
    }
  });

  // 视频信息加载
  async function loadVideoInfo() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) return;
    const key = `videos_tab_${tab.id}`;
    const data = await chrome.storage.local.get(key);
    const info = data[key];
    if (!info || Date.now() - info.timestamp > 30000) {
      videoList.innerHTML = '<div class="empty">暂无数据（正在尝试刷新...）</div>';
      // 请求刷新
      try { chrome.tabs.sendMessage(tab.id, { type: 'INIT_CAPTION' }); } catch (_) {}
      return;
    }
    const videos = info.videos || [];
    if (videos.length === 0) {
      videoList.innerHTML = '<div class="empty">当前页面未检测到视频</div>';
      return;
    }
    videoList.innerHTML = videos.map((v, i) => `
      <div class="video-item">
        <div class="video-url">视频 ${i + 1}: ${v.src}</div>
        <div class="video-info">
          时间: ${v.currentTime?.toFixed?.(1) ?? '?'}s / ${v.duration > 0 ? v.duration.toFixed(1) : '?'}s |
          状态: ${v.paused ? '暂停' : '播放中'} |
          分辨率: ${v.videoWidth}×${v.videoHeight || 'N/A'}
        </div>
      </div>
    `).join('');
  }

  loadVideoInfo();
  setInterval(loadVideoInfo, 2000);

  // 打开弹窗时主动同步录音状态，和 wav.js/其他面板保持一致
  async function refreshRecordingState() {
    const result = await chrome.storage.local.get('captionState');
    const s = result.captionState || { enabled: true, subtitleOn: false, recordingOn: false, recordingStartedAt: 0 };
    if (s.recordingOn && s.recordingStartedAt) {
      state.recordingOn = true;
      state.recordingStartedAt = s.recordingStartedAt;
      recordBtn.textContent = '停止录音';
      progress.style.display = 'block';
      startTime = s.recordingStartedAt;
      renderProgress(Date.now() - startTime);
      startProgress();
    } else {
      stopProgress();
    }
    toggle.checked = !!s.enabled;
    subtitleBtn.textContent = s.subtitleOn ? '字幕已开' : '字幕未开';
    recordBtn.textContent = s.recordingOn ? '停止录音' : '开始录音';
  }
  refreshRecordingState();

  // 初始发送 INIT_CAPTION，让 content/wav.js 状态同步
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.id) chrome.tabs.sendMessage(tab.id, { type: 'INIT_CAPTION' });
  } catch (err) {
    log("INIT_CAPTION failed", err);
  }
});
