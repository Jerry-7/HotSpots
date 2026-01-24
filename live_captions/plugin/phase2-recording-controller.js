// Phase 2: RecordingController placeholder (to be used by Patch 2)
// This module will encapsulate recording lifecycle: start/stop, streams, errors, durations

export class RecordingController {
  constructor() {
    this.isRecording = false;
    this.startedAt = 0;
  }

  async start(streamId) {
    // Placeholder for real implementation in Patch 2
    this.isRecording = true;
    this.startedAt = Date.now();
    return { success: true };
  }

  async stop() {
    // Placeholder for real implementation in Patch 2
    this.isRecording = false;
    const durationMs = this.startedAt ? Date.now() - this.startedAt : 0;
    this.startedAt = 0;
    return { success: true, durationMs };
  }
}
