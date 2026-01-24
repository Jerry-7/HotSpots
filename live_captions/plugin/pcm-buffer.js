/**
 * PCMBuffer: accumulate interleaved Int16 PCM samples
 * Data layout: interleaved samples for all channels: [L0,R0,L1,R1,...]
 */
export class PCMBuffer {
  constructor() {
    this.buffer = [];
  }

  // Append from Float32 data per channel (data: Array<Float32Array>)
  appendFromFloat32(channels, frames, data) {
    for (let i = 0; i < frames; ++i) {
      for (let ch = 0; ch < channels; ++ch) {
        const sample = data?.[ch]?.[i] ?? 0;
        const s = Math.max(-1, Math.min(1, sample));
        const int16 = s < 0 ? s * 32768 : s * 32767;
        this.buffer.push(int16 < 0 ? Math.ceil(int16) : Math.floor(int16));
      }
    }
  }

  toInt16Array() {
    return new Int16Array(this.buffer);
  }

  reset() {
    this.buffer = [];
  }
}
