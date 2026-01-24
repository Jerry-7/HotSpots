/**
 * PCM Int16 均为一维 Int16Array。
 * @param {Int16Array} pcmInt16 - 采集到的 PCM 数据
 * @param {number} sampleRate - 采样率
 * @param {number} numChannels - 声道数
 * @returns {Blob} - WAV 格式音频文件(Blob)
 */
export function encodeWav(pcmInt16, sampleRate = 44100, numChannels = 1) {
  // 检查输入参数
  if (!pcmInt16 || typeof pcmInt16.length !== "number") throw new Error("encodeWav: invalid pcmInt16 buffer");

  const bytesPerSample = 2;
  const dataSize = pcmInt16.length * bytesPerSample;
  const blockAlign = numChannels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  let offset = 0;

  function writeString(s) {
    for (let i = 0; i < s.length; i++) {
      view.setUint8(offset++, s.charCodeAt(i));
    }
  }
  function writeUint32(v) {
    view.setUint32(offset, v, true); // Little endian
    offset += 4;
  }
  function writeUint16(v) {
    view.setUint16(offset, v, true); // Little endian
    offset += 2;
  }

  // --- RIFF Header ---
  writeString('RIFF');
  writeUint32(36 + dataSize); // file size - 8
  writeString('WAVE');

  // --- fmt chunk ---
  writeString('fmt ');
  writeUint32(16);            // Subchunk1Size (16 for PCM)
  writeUint16(1);             // AudioFormat (1 = PCM)
  writeUint16(numChannels);   // NumChannels
  writeUint32(sampleRate);    // SampleRate
  writeUint32(byteRate);      // ByteRate
  writeUint16(blockAlign);    // BlockAlign
  writeUint16(16);            // BitsPerSample

  // --- data chunk ---
  writeString('data');
  writeUint32(dataSize);

  // --- PCM data ---
  for (let i = 0; i < pcmInt16.length; i++) {
    view.setInt16(offset, pcmInt16[i], true);
    offset += 2;
  }

  return new Blob([buffer], { type: 'audio/wav' });
}

/**
 * 兼容背景导出接口（实际直接调用 encodeWav）
 */
export function exportWav(pcmInt16, sampleRate = 44100, numChannels = 1) {
  return encodeWav(pcmInt16, sampleRate, numChannels);
}

/**
 * 下载 WAV 文件，确保 blob 释放时机。
 * @param {Blob} blob
 * @param {string?} filename
 */
export async function downloadWav(blob, filename = null) {
  if (!blob) return;
  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  const name = filename || `tab-audio-${ts}.wav`;

  const url = URL.createObjectURL(blob);

  let downloadId = null;
  let revoked = false;
  function revokeUrl() {
    if (revoked) return;
    revoked = true;
    URL.revokeObjectURL(url);
  }

  function onChanged(delta) {
    if (!downloadId || delta.id !== downloadId) return;
    if (
      delta.state &&
      (delta.state.current === "complete" || delta.state.current === "interrupted")
    ) {
      chrome.downloads.onChanged.removeListener(onChanged);
      revokeUrl();
    }
  }

  try {
    downloadId = await chrome.downloads.download({
      url,
      filename: name,
      saveAs: true,
    });
    chrome.downloads.onChanged.addListener(onChanged);
  } catch (e) {
    chrome.downloads.onChanged.removeListener(onChanged);
    revokeUrl();
    throw e;
  }
}
