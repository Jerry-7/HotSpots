// Background: Central message bus and recording lifecycle controller (Phase 1)

let isRecording = false;
let recordingStartedAt = 0;

const DEBUG = true;
const log = (...args) => DEBUG && console.log("[Caption][bg]", ...args);
const warn = (...args) => DEBUG && console.warn("[Caption][bg]", ...args);
const errLog = (...args) => console.error("[Caption][bg]", ...args);

// Robust Offscreen document readiness with exponential backoff
async function ensureOffscreenDocument() {
  const url = chrome.runtime.getURL("offscreen.html");
  const MAX_ATTEMPTS = 5;
  let attempt = 0;
  let delay = 100;
  while (attempt < MAX_ATTEMPTS) {
    let exists = false;
    try {
      const maybePromise = chrome.offscreen.hasDocument?.();
      if (maybePromise && typeof maybePromise.then === "function") {
        exists = await maybePromise;
      } else if (typeof chrome.offscreen.hasDocument === 'function') {
        exists = await new Promise(resolve => chrome.offscreen.hasDocument(r => resolve(!!r)));
      } else {
        exists = false;
      }
    } catch (_) {
      exists = false;
    }
    if (exists) return;

    log("Offscreen document not found, attempting creation (attempt", attempt + 1, ")", url);
    try {
      await chrome.offscreen.createDocument({
        url,
        reasons: ["AUDIO_PLAYBACK"],
        justification: "Record tab audio using WebAudio (AudioWorklet) in MV3.",
      });
      log("Offscreen document created.");
      return;
    } catch (e) {
      log("Offscreen createDocument failed:", e);
    }
    attempt++;
    await new Promise(r => setTimeout(r, delay));
    delay = Math.min(delay * 2, 2000);
  }
  log("Failed to ensure Offscreen document after max retries.");
}

async function startRecording() {
  await ensureOffscreenDocument();
  // slight wait for offscreen to initialize
  await new Promise(r => setTimeout(r, 100));

  try {
    const pingResult = await chrome.runtime.sendMessage({ type: "OFFSCREEN_PING" });
    if (!pingResult?.ok) throw new Error("Offscreen document not ready");
  } catch (e) {
    warn("Offscreen ping failed, continuing anyway:", e);
  }

  chrome.runtime.sendMessage({ type: "OFFSCREEN_START_RECORDING" }).catch(err => {
    errLog("Failed to send OFFSCREEN_START_RECORDING:", err);
    setRecordingState(false);
  });
}

async function stopRecording() {
  await ensureOffscreenDocument();
  log("Sending OFFSCREEN_STOP_RECORDING");
  chrome.runtime.sendMessage({ type: "OFFSCREEN_STOP_RECORDING" }).catch(err => {
    errLog("Failed to send OFFSCREEN_STOP_RECORDING:", err);
  });
}

async function startRecordingWithStreamId(streamId) {
  await ensureOffscreenDocument();
  await new Promise(r => setTimeout(r, 10));
  log("Sending OFFSCREEN_START_RECORDING with streamId length=", String(streamId || "").length);
  chrome.runtime.sendMessage({ type: "OFFSCREEN_START_RECORDING", streamId }).catch(err => {
    errLog("Failed to send OFFSCREEN_START_RECORDING(streamId):", err);
    setRecordingState(false);
  });
}

async function setRecordingState(active, durationMs = 0) {
  isRecording = !!active;
  if (active && !recordingStartedAt) {
    recordingStartedAt = Date.now();
  }
  if (!active) {
    recordingStartedAt = 0;
  }

  log("setRecordingState", { active: !!active, durationMs, recordingStartedAt });

  // Update UI icons
  chrome.action.setIcon({ path: active ? "icons/start-icon.png" : "icons/stop-icon.png" });

  // Persist state for content/popup
  const result = await chrome.storage.local.get("captionState");
  let prev = result.captionState;
  if (!prev) {
    prev = { enabled: true, subtitleOn: false, recordingOn: false, recordingStartedAt: 0 };
  }
  const next = {
    ...prev,
    recordingOn: !!active,
    recordingStartedAt
  };
  await chrome.storage.local.set({ captionState: next });

  // Broadcast to all listeners
  chrome.runtime.sendMessage({ type: "RECORDING_STATE", active: !!active, durationMs, startedAt: recordingStartedAt });
}

// Central dispatch for background messages (Phase 1: MSG BUS)
const MESSAGE_TYPES = {
  VIDEO_DETECTED: 'VIDEO_DETECTED',
  RECORDING_STATE: 'RECORDING_STATE',
  RECORDING_ERROR: 'RECORDING_ERROR',
  START_RECORDING: 'START_RECORDING',
  STOP_RECORDING: 'STOP_RECORDING',
  INIT_CAPTION: 'INIT_CAPTION',
  OFFSCREEN_PING: 'OFFSCREEN_PING',
  OFFSCREEN_START_RECORDING: 'OFFSCREEN_START_RECORDING',
  OFFSCREEN_STOP_RECORDING: 'OFFSCREEN_STOP_RECORDING'
};

const HANDLERS = {
  [MESSAGE_TYPES.VIDEO_DETECTED]: async (payload, sender) => {
    const tabId = sender?.tab?.id;
    if (!tabId) return;
    const key = `videos_tab_${tabId}`;
    chrome.storage.local.set({
      [key]: {
        url: sender?.url,
        videos: payload?.videos,
        timestamp: Date.now()
      }
    });
  },
  [MESSAGE_TYPES.RECORDING_STATE]: async (payload) => {
    const active = payload?.active;
    if (active) {
      if (payload?.startedAt) recordingStartedAt = payload.startedAt; else recordingStartedAt = Date.now();
    } else {
      recordingStartedAt = 0;
    }
    await setRecordingState(!!active, payload?.durationMs || 0);
  },
  [MESSAGE_TYPES.RECORDING_ERROR]: async (payload) => {
    errLog("RECORDING_ERROR:", payload?.error);
    await setRecordingState(false);
  },
  [MESSAGE_TYPES.START_RECORDING]: async (payload, sender, sendResponse) => {
    if (isRecording) {
      if (typeof sendResponse === 'function') sendResponse({ success: true });
      return;
    }
    log("START_RECORDING requested", { tabId: sender?.tab?.id, hasStreamId: !!payload?.streamId });
    isRecording = true;
    await setRecordingState(true);
    try {
      await startRecordingWithStreamId(payload?.streamId);
      if (typeof sendResponse === 'function') sendResponse({ success: true });
    } catch (e) {
      errLog("startRecordingWithStreamId failed", e);
      isRecording = false;
      await setRecordingState(false);
      if (typeof sendResponse === 'function') sendResponse({ success: false, error: String(e?.message || e) });
    }
  },
  [MESSAGE_TYPES.STOP_RECORDING]: async (_payload, _sender, sendResponse) => {
    if (!isRecording) {
      if (typeof sendResponse === 'function') sendResponse({ success: true });
      return;
    }
    log("STOP_RECORDING requested");
    isRecording = false;
    await stopRecording();
    if (typeof sendResponse === 'function') sendResponse({ success: true });
  },
  [MESSAGE_TYPES.INIT_CAPTION]: async (_payload, _sender, sendResponse) => {
    const result = await chrome.storage.local.get("captionState");
    if (typeof sendResponse === 'function') sendResponse(result.captionState || {});
  }
};

chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
  if (DEBUG && message?.type) {
    log("onMessage", message.type, "from", sender?.url || sender?.origin || sender?.tab?.id || "unknown");
  }
  const type = message?.type;
  const handler = HANDLERS[type];
  if (handler) {
    try {
      const res = handler(message, sender, sendResponse);
      if (res && typeof res.then === 'function') {
        return res.then(() => true).catch((e) => { errLog('handler error', e); if (typeof sendResponse === 'function') sendResponse({ success: false, error: String(e?.message || e) }); return true; });
      }
      return true;
    } catch (e) {
      errLog('handler exception', e);
      if (typeof sendResponse === 'function') sendResponse({ success: false, error: String(e?.message || e) });
      return true;
    }
  }
  // Unknown type: ignore
  return;
});

