// 该 AudioWorkletProcessor 与主录音 Recorder.js 通信协议需保持同步，确保发送原始 PCM float32 数据。
// 发送的数据结构为：{ type: 'pcm', channels, frames, data: Array<Array<number>> }

class RecorderProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    // 预留支持 future 配置
    this.port.onmessage = (event) => {
      // 目前暂不支持配置参数
    };
  }

  process(inputs, outputs, parameters) {
    // 只取第一个输入（通常 AudioWorklet 只有 inputs[0]）
    const input = inputs[0];
    if (!input || input.length === 0) {
      // 没有有效输入则直接跳过
      return true;
    }

    // input 是 channels 数组，每个 channel 是 Float32Array
    const channels = input.length;
    const frames = input[0].length;
    // 数据结构必须保证 channels 个数组，每个为 frames 帧
    // 注意：要复制数组数据，不能直接传递引用给主线程
    const data = [];
    for (let c = 0; c < channels; ++c) {
      // 避免 input[c] 为空或异常
      data.push(input[c] ? input[c].slice(0) : new Float32Array(frames));
    }
    // 不转 Int16，不压缩，浮点 PCM（后端再做转换）
    this.port.postMessage({
      type: 'pcm',
      channels,
      frames,
      data, // Array<Float32Array>
    });

    return true; // 持续处理
  }
}

// 确保 processor 名称和主线程注册一致
registerProcessor('recorder-processor', RecorderProcessor);
