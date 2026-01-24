// content.js - 与 popup.js 协作：负责页面视频检测、状态同步
// 仅在顶层页面运行：防止 iframe 环境重复注入、混淆数据
if (window.top !== window) {
  // 子 frame 不做任何操作
  return;
} else {
  console.log('[Caption] content.js loaded on:', location.href);
}

// 状态对象，与 popup.js 中定义字段保持一致
let currentCaptionState = {
  enabled: true,
  subtitleOn: false,
  recordingOn: false,
  recordingStartedAt: 0 // 保留与 popup.js 对齐
};
let videoObserver = null;    // MutationObserver 实例
let scanInterval = null;     // setInterval 定时器

/**
 * 从 chrome.storage.local 读取 captionState 状态。
 * @param {Function} cb - 读取完成回调
 */
function readCaptionState(cb) {
  chrome.storage.local.get(['captionState'], (result) => {
    // 需兼容 popup.js 可能扩展的字段
    const s = result.captionState || {
      enabled: true,
      subtitleOn: false,
      recordingOn: false,
      recordingStartedAt: 0
    };
    currentCaptionState = { ...s }; // 深拷贝保证不会引用污染
    if (typeof cb === 'function') cb(currentCaptionState);
  });
}

/**
 * 更新 chrome.storage.local 中的 captionState 状态并同步内存
 * @param {Object} partial - 新状态字段
 */
function setCaptionState(partial) {
  const next = Object.assign({}, currentCaptionState, partial);
  currentCaptionState = { ...next };
  chrome.storage.local.set({ captionState: next });
  // 不直接操作 DOM，由 popup/popup.js 负责 UI 层展示
}

/** 判断扩展上下文失效错误 */
function isExtensionContextInvalidatedError(e) {
  const msg = String(e?.message || e || '');
  return msg.includes('Extension context invalidated');
}

/**
 * 扫描页面所有 video 元素并通知后台，由后台带上 tabId 存储
 */
function scanVideos() {
  const videos = Array.from(document.querySelectorAll('video'));
  const data = videos.map(v => ({
    src: v.currentSrc || v.src || '',
    currentTime: v.currentTime,
    duration: v.duration,
    paused: v.paused,
    readyState: v.readyState,
    videoWidth: v.videoWidth,
    videoHeight: v.videoHeight
  }));
  try {
    if (!chrome?.runtime?.id) return;
    chrome.runtime.sendMessage({ type: 'VIDEO_DETECTED', videos: data }).catch(e => {
      if (isExtensionContextInvalidatedError(e)) stopVideoDetection();
    });
  } catch (e) {
    if (isExtensionContextInvalidatedError(e)) {
      stopVideoDetection();
      return;
    }
    throw e;
  }
}

/**
 * 启动视频探测（包含初次及后续 DOM/定时扫描）
 */
function initVideoDetection() {
  scanVideos();
  if (!videoObserver) {
    videoObserver = new MutationObserver(() => {
      try { scanVideos(); } catch (e) {
        if (isExtensionContextInvalidatedError(e)) stopVideoDetection();
      }
    });
    videoObserver.observe(document.documentElement, { childList: true, subtree: true });
  }
  if (!scanInterval) {
    scanInterval = setInterval(() => {
      try { scanVideos(); } catch (e) {
        if (isExtensionContextInvalidatedError(e)) stopVideoDetection();
      }
    }, 2000);
  }
}

/**
 * 停止视频探测
 */
function stopVideoDetection() {
  try { if (videoObserver) videoObserver.disconnect(); } catch (_) {}
  videoObserver = null;
  if (scanInterval) {
    try { clearInterval(scanInterval); } catch (_) {}
    scanInterval = null;
  }
}

/**
 * 初始化入口。根据 enabled 控制视频扫描启动与否。
 */
function init() {
  readCaptionState((state) => {
    // currentCaptionState 已在 readCaptionState 内赋值
    if (state.enabled) {
      initVideoDetection();
      try { scanVideos(); } catch (e) {}
    } else {
      stopVideoDetection();
    }
  });
}

// 启动入口（只在顶层页面启动）
init();

// 消息监听
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'TOGGLE_SUBTITLE') {
    // UI 按钮在 popup，content 只持久同步状态
    currentCaptionState.subtitleOn = !currentCaptionState.subtitleOn;
    setCaptionState({ subtitleOn: currentCaptionState.subtitleOn });
  } else if (message?.type === 'TOGGLE_AUDIO_RECORDING') {
    // popup 触发录音，交给 background 处理
    chrome.runtime.sendMessage({ type: 'TOGGLE_AUDIO_RECORDING' });
  } else if (message?.type === 'INIT_CAPTION') {
    // popup 刷新触发页面视频状态/录音状态同步
    init();
  }
  // 不直接对 sendResponse 处理响应（未用到）
});

// 监听来自 background 的录音状态同步指令
chrome.runtime.onMessage.addListener((m) => {
  if (m?.type === 'RECORDING_STATE') {
    if (typeof m.active === 'boolean') {
      currentCaptionState.recordingOn = m.active;
      setCaptionState({ recordingOn: m.active });
      // 与 popup 状态统一，无需其他 UI 处理
    }
    // 支持 future: 也可同步 m.recordingStartedAt
    if (typeof m.recordingStartedAt === 'number') {
      currentCaptionState.recordingStartedAt = m.recordingStartedAt;
      setCaptionState({ recordingStartedAt: m.recordingStartedAt });
    }
  }
});