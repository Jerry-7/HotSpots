/**
 * offscreen.js 的作用：
 *
 * 该文件作为 Chrome 扩展的“offscreen document”页面脚本，专门用于在后台环境中进行音频录制，不直接操作 DOM。
 * 主要职责：
 *  1. 接收后台/前端消息（如 OFFSCREEN_START_RECORDING、OFFSCREEN_STOP_RECORDING），通过 getUserMedia/tabCapture
 *     获取标签页音频流并录制，保证录音不中断、受页面生命周期影响最小。
 *  2. 管理录音状态，包括开始、结束录音，处理 stream track 的断开，自动通知录音状态变更。
 *  3. 录音结束后生成 wav 并触发下载；将当前录音状态和异常主动同步给后台脚本或 Popup 前端。
 *  4. 支持兼容新旧音频捕获约束（chromeMediaSourceId/mandatory），保证新版与旧版浏览器都能录制。
 * 
 * 注意：
 *   - 该脚本不直接与用户界面交互，只作为通信节点和稳定的录音后端。
 *   - 主要配合 manifest v3 下的 service worker 与 content script/popup 通信，实现对标签页内音频的稳定、无干扰捕获。
 */

import { Recorder } from "./recorder.js";
import { downloadWav } from "./wav.js";

// 录音器
let recorder = null;
// 音频流
let audioStream = null;
// 是否正在录音
let isRecording = false;
// 录音开始时间
let recordingStartTime = 0;
const DEBUG = true;
const log = (...args) => DEBUG && console.log("[Caption][offscreen]", ...args);
const warn = (...args) => DEBUG && console.warn("[Caption][offscreen]", ...args);
const errLog = (...args) => console.error("[Caption][offscreen]", ...args);

/**
 * 开始录音，支持新的 streamId 约束与旧的 tabCapture 兼容路径。
 * @param {string|null} streamId - chrome.tabCapture/queryTabId 获取的音频流 ID。
 */
async function startRecording(streamId = null) {
  if (isRecording) {
    log("Already recording, ignoring duplicate start.");
    return;
  }

  let stream = null;
  if (streamId) {
    try {
      log("getUserMedia start (new constraints). streamId length=", String(streamId || "").length);
      // 新版约束（较新版Chromium、manifest v3支持）
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { chromeMediaSource: "tab", chromeMediaSourceId: streamId },
        video: false,
      });
    } catch (err) {
      warn("getUserMedia new constraints failed, trying legacy format:", err);
      // 兼容旧版
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { mandatory: { chromeMediaSource: "tab", chromeMediaSourceId: streamId } },
        video: false,
      });
    }
  } else {
    log("tabCapture.capture start (legacy path)");
    stream = await new Promise((resolve, reject) => {
      chrome.tabCapture.capture({ audio: true, video: false }, (s) => {
        if (!s) reject(new Error("tabCapture.capture failed"));
        else resolve(s);
      });
    });
  }

  // 监听流断开，自动触发停止
  stream.getTracks().forEach(track => {
    log("Track acquired", { kind: track.kind, id: track.id, enabled: track.enabled, muted: track.muted, readyState: track.readyState });
    try {
      if (typeof track.getSettings === "function") {
        const settings = track.getSettings();
        if (settings) log("Track settings", settings);
      }
    } catch (_) {}
    
    // 下面的代码给音轨(track)对象添加了事件监听，用于跟踪音轨的状态变化：

    // 当音轨被静音时（例如标签页被切换、系统静音、外部原因等），会触发 onmute 事件
    track.onmute = () => warn("track.onmute", { id: track.id, readyState: track.readyState });

    // 当音轨从静音恢复时
    track.onunmute = () => warn("track.onunmute", { id: track.id, readyState: track.readyState });

    // 当音轨结束（如标签页关闭/切换），自动触发录音关闭
    track.onended = () => {
      warn("track.onended (stream ended)", { id: track.id, readyState: track.readyState });
      // 如果当前还在录音，则自动停止录音，并尝试保存录音文件
      if (isRecording) {
        stopRecording().then(({ blob, durationMs }) => {
          // 若有录音文件，执行自动下载
          if (blob) {
            downloadWav(blob).catch(err => console.error("Auto-save on track end failed:", err));
          }
          chrome.runtime.sendMessage({
            type: "RECORDING_STATE",
            active: false,
            durationMs
          }).catch(() => {});
        });
      }
    };
  });

  audioStream = stream;
  recordingStartTime = Date.now();
  log("Recorder start, recordingStartTime=", recordingStartTime);
  recorder = new Recorder(stream);
  await recorder.start();
  isRecording = true;
  log("Recording isRunning=", isRecording);
}

/**
 * 停止录音，并释放资源，返回录制得到的 blob 及录制时长
 * @returns {Promise<{blob: Blob|null, durationMs: number}>}
 */
async function stopRecording() {
  if (!isRecording) {
    log("stopRecording called but isRecording=false");
    return { blob: null, durationMs: 0 };
  }

  let blob = null;
  try {
    log("Stopping recorder...");
    if (recorder && typeof recorder.stop === "function") {
      blob = await recorder.stop();
    }
  } finally {
    try { if (recorder && typeof recorder.destroy === "function") recorder.destroy(); } catch (_) {}
    recorder = null;

    if (audioStream) {
      try { audioStream.getTracks().forEach((t) => t.stop()); } catch (_) {}
      audioStream = null;
    }
    isRecording = false;
    log("Stopped. isRecording=false");
  }

  const durationMs = recordingStartTime ? (Date.now() - recordingStartTime) : 0;
  recordingStartTime = 0;
  log("stopRecording durationMs=", durationMs, "blob=", !!blob, "blobSize=", blob?.size);
  return { blob, durationMs };
}

// 处理外界消息，实现录音控制与状态反馈
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    if (!message?.type) return;

    if (message.type === "OFFSCREEN_START_RECORDING") {
      try {
        log("OFFSCREEN_START_RECORDING received");
        await startRecording(message.streamId || null);
        // 兼容 popup.js 对 startedAt 字段的要求
        chrome.runtime.sendMessage({
          type: "RECORDING_STATE",
          active: true,
          startedAt: recordingStartTime
        }).catch(err => console.error("Failed to send RECORDING_STATE:", err));
        // 状态同步到 storage
        chrome.storage.local.get('captionState', (result) => {
          const s = result.captionState || {};
          chrome.storage.local.set({
            captionState: {
              ...s,
              recordingOn: true,
              recordingStartedAt: recordingStartTime
            }
          });
        });
      } catch (err) {
        errLog("startRecording failed:", err);
        chrome.runtime.sendMessage({ type: "RECORDING_ERROR", error: String(err?.message || err) }).catch(() => {});
        chrome.runtime.sendMessage({ type: "RECORDING_STATE", active: false }).catch(() => {});
        // 状态同步到 storage
        chrome.storage.local.get('captionState', (result) => {
          const s = result.captionState || {};
          chrome.storage.local.set({
            captionState: {
              ...s,
              recordingOn: false,
              recordingStartedAt: 0
            }
          });
        });
        throw err;
      }
    }

    if (message.type === "OFFSCREEN_STOP_RECORDING") {
      log("OFFSCREEN_STOP_RECORDING received");
      const { blob, durationMs } = await stopRecording();
      if (blob) {
        try {
          log("Downloading wav...");
          await downloadWav(blob);
        } catch (err) {
          errLog("downloadWav failed:", err);
          chrome.runtime.sendMessage({ type: "RECORDING_ERROR", error: String(err?.message || err) }).catch(() => {});
        }
      }
      chrome.runtime.sendMessage({
        type: "RECORDING_STATE",
        active: false,
        durationMs
      }).catch(err => console.error("Failed to send RECORDING_STATE:", err));
      // 状态同步到 storage
      chrome.storage.local.get('captionState', (result) => {
        const s = result.captionState || {};
        chrome.storage.local.set({
          captionState: {
            ...s,
            recordingOn: false,
            recordingStartedAt: 0
          }
        });
      });
    }

    if (message.type === "OFFSCREEN_PING") {
      log("OFFSCREEN_PING");
      sendResponse({ ok: true, isRecording });
      return;
    }
  })().catch((err) => {
    errLog("message handler error:", err);
    chrome.runtime.sendMessage({ type: "RECORDING_ERROR", error: String(err?.message || err) }).catch(() => {});
    chrome.runtime.sendMessage({ type: "RECORDING_STATE", active: false }).catch(() => {});
    // 状态同步到 storage
    chrome.storage.local.get('captionState', (result) => {
      const s = result.captionState || {};
      chrome.storage.local.set({
        captionState: {
          ...s,
          recordingOn: false,
          recordingStartedAt: 0
        }
      });
    });
  });

  // 重要：异步响应
  return true;
});
