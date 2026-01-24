import { encodeWav } from './wav.js';

export function encodePCMToWav(pcmInt16, sampleRate = 44100, numChannels = 1) {
  // Simple wrapper for encoding PCM to WAV using existing encodeWav
  return encodeWav(pcmInt16, sampleRate, numChannels);
}

export async function downloadWavFromPCM(pcmInt16, sampleRate = 44100, numChannels = 1, filename = null) {
  const blob = encodePCMToWav(pcmInt16, sampleRate, numChannels);
  // Reuse existing downloader
  // Note: this function assumes you can access a blob downloader; propose to call from background/recorder when needed
  // For now, just return the blob so caller can handle download
  return blob;
}
