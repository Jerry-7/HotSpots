import { exportWav } from "./wav.js";

// 保持与 content.js, popup.js, recorder-worklet.js 协议、处理同步

class Recorder {
  constructor(stream) {
    this.stream = stream;
    this.audioCtx = null;
    this.source = null;
    this.workletNode = null;
    this.buffer = []; // Int16 PCM 缓冲，一维交错型
    this.sampleRate = 44100; // AudioContext实际值会覆盖
    this.numChannels = 0; // 由 worklet 动态得出
    this.isRunning = false;
  }

  async init() {
    if (this.audioCtx) return;

    console.log("[Caption][recorder] init()");
    this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    this.sampleRate = this.audioCtx.sampleRate;
    console.log("[Caption][recorder] AudioContext sampleRate=", this.sampleRate, "state=", this.audioCtx.state);

    // 创建 Source
    this.source = this.audioCtx.createMediaStreamSource(this.stream);

    // 确保 worklet 路径兼容 extension/offscreen
    const workletUrl = (typeof chrome !== "undefined" && chrome?.runtime?.getURL)
      ? chrome.runtime.getURL('recorder-worklet.js')
      : 'recorder-worklet.js';
    console.log("[Caption][recorder] addModule", workletUrl);
    await this.audioCtx.audioWorklet.addModule(workletUrl);
    console.log("[Caption][recorder] addModule ok");

    // 以2通道要求申请，最终以设备实际为准
    this.workletNode = new AudioWorkletNode(this.audioCtx, 'recorder-processor', {
      numberOfInputs: 1,
      numberOfOutputs: 1,
      channelCount: 2,
      outputChannelCount: [2]
    });

    // 通道数等待实际 worklet 上报
    this.numChannels = 0;
    this.buffer = [];

    this.workletNode.port.onmessage = (ev) => {
      const msg = ev.data;
      if (msg && msg.type === 'pcm') {
        // 修正：以首次收到的数据通道为主，后续忽略
        if (!this.numChannels && typeof msg.channels === 'number') {
          this.numChannels = Math.max(1, msg.channels);
        }
        this._collectPCM(msg);
      }
    };

    this.source.connect(this.workletNode);
    // 若不想录音漏音频，可不接到 destination，但有的实现连接 destination 可激活上下文
    this.workletNode.connect(this.audioCtx.destination);

    this.isRunning = false;
    this.buffer = [];
  }

  _collectPCM(msg) {
    // 保持与 recorder-worklet.js 协议同步：msg.data = Array<channel>[Float32Array]
    const channels = msg.channels || 1;
    const frames = msg.frames || (msg.data?.[0]?.length ?? 0);
    // 按 interleave 方式打平为一维 int16: [L0,R0,L1,R1,...]
    for (let i = 0; i < frames; ++i) {
      for (let ch = 0; ch < channels; ++ch) {
        const sample = msg.data?.[ch]?.[i] ?? 0;
        // 限幅 & float32 PCM->int16 PCM
        const s = Math.max(-1, Math.min(1, sample));
        const int16 = s < 0 ? s * 32768 : s * 32767;
        this.buffer.push(int16 < 0 ? Math.ceil(int16) : Math.floor(int16));
      }
    }
  }

  async start() {
    await this.init();
    if (this.audioCtx.state === 'suspended') {
      console.log("[Caption][recorder] AudioContext suspended, resume()");
      await this.audioCtx.resume();
    }
    this.buffer = [];
    this.isRunning = true;
    console.log("[Caption][recorder] start() ok, ctx.state=", this.audioCtx.state);
  }

  async stop() {
    console.log("[Caption][recorder] stop() begin");
    // 先断开工作节点，防止残留回调
    try { if (this.workletNode) this.workletNode.disconnect(); } catch(e){}
    try { if (this.source) this.source.disconnect(); } catch(e){}
    const blob = await this._exportWav();
    if (this.audioCtx) {
      try { await this.audioCtx.close(); } catch(_) {}
      this.audioCtx = null;
    }
    this.isRunning = false;
    console.log("[Caption][recorder] stop() ok. blob=", !!blob, "size=", blob?.size);
    return blob;
  }

  async _exportWav() {
    try {
      // 注意buffer为int16 interleave, numChannels应准确
      const channels = this.numChannels || 2;
      const flat = new Int16Array(this.buffer);
      // 使用 wav.js 的 exportWav(PCM, sampleRate, numChannels)
      return exportWav(flat, this.sampleRate, channels);
    } catch (err) {
      console.error('Recorder: WAV 编码失败', err);
      // 兜底返回原始缓冲(不严格标准)
      const fallback = new Blob([new Int16Array(this.buffer).buffer], { type: 'audio/wav' });
      return fallback;
    }
  }

  destroy() {
    // 全面断开/关闭防止泄漏
    try {
      if (this.workletNode) { try {this.workletNode.disconnect();} catch{} }
      if (this.source) { try {this.source.disconnect();} catch{} }
      if (this.audioCtx && this.audioCtx.state !== 'closed') {
        this.audioCtx.close();
      }
    } catch (e) {
      console.error('Recorder destroy error', e);
    } finally {
      this.audioCtx = null;
      this.source = null;
      this.workletNode = null;
      this.buffer = [];
      this.isRunning = false;
      this.numChannels = 0;
    }
  }
}

export { Recorder };
