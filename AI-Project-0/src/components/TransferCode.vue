<template>
  <div class="transfer-code">
    <div v-if="!session" class="generate-section">
      <button 
        @click="generateCode" 
        :disabled="!canGenerate"
        class="btn-primary btn-large"
      >
        <span class="icon">🔗</span>
        生成传输码
      </button>
      <p class="hint">完成文件上传后可生成传输码</p>
    </div>

    <div v-else class="code-display">
      <div class="code-card">
        <div class="code-header">
          <h3>传输码已生成</h3>
          <div class="code-status">
            <span class="status-badge">有效期24小时</span>
          </div>
        </div>
        
        <div class="code-main">
          <div class="code-value" @click="copyCode">
            <span class="code-text">{{ session.code }}</span>
            <button class="copy-btn" title="复制">📋</button>
          </div>
          
          <div class="code-info">
            <div class="info-item">
              <span class="label">文件数量:</span>
              <span class="value">{{ session.files.length }} 个</span>
            </div>
            <div class="info-item">
              <span class="label">总大小:</span>
              <span class="value">{{ formatFileSize(totalSize) }}</span>
            </div>
            <div class="info-item">
              <span class="label">下载次数:</span>
              <span class="value">{{ session.downloads }} / {{ session.maxDownloads }}</span>
            </div>
            <div class="info-item">
              <span class="label">过期时间:</span>
              <span class="value">{{ formatExpireTime(session.expiresAt) }}</span>
            </div>
          </div>
        </div>
        
        <div class="code-actions">
          <button @click="shareCode" class="btn-secondary">
            <span class="icon">📤</span>
            分享
          </button>
          <button @click="resetCode" class="btn-danger">
            <span class="icon">🔄</span>
            重新生成
          </button>
        </div>
      </div>
      
      <div class="qr-section">
        <div class="qr-placeholder">
          <p>二维码</p>
          <small>扫码快速获取传输码</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFileStore } from '@/stores/fileStore'
import { formatFileSize } from '@/utils/fileUtils'

const fileStore = useFileStore()

const session = computed(() => fileStore.currentSession)
const canGenerate = computed(() => fileStore.completedFiles.length > 0)
const totalSize = computed(() => 
  session.value?.files.reduce((sum, file) => sum + file.size, 0) || 0
)

const generateCode = () => {
  fileStore.createTransferSession()
}

const copyCode = async () => {
  if (session.value) {
    try {
      await navigator.clipboard.writeText(session.value.code)
      // 这里可以添加复制成功的提示
      alert('传输码已复制到剪贴板')
    } catch (err) {
      console.error('复制失败:', err)
    }
  }
}

const shareCode = () => {
  if (session.value) {
    const shareText = `文件传输码: ${session.value.code}\n包含 ${session.value.files.length} 个文件，总大小 ${formatFileSize(totalSize.value)}`
    
    if (navigator.share) {
      navigator.share({
        title: '文件传输码',
        text: shareText
      })
    } else {
      // 降级到复制
      copyCode()
    }
  }
}

const resetCode = () => {
  if (confirm('确定要重新生成传输码吗？原传输码将失效。')) {
    fileStore.createTransferSession()
  }
}

const formatExpireTime = (date: Date) => {
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟后`
  } else if (minutes > 0) {
    return `${minutes}分钟后`
  } else {
    return '即将过期'
  }
}
</script>

<style scoped>
.transfer-code {
  width: 100%;
}

.generate-section {
  text-align: center;
  padding: 40px 20px;
}

.btn-large {
  padding: 16px 32px;
  font-size: 18px;
  border-radius: 12px;
}

.btn-primary {
  background: #007bff;
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-2px);
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.hint {
  margin-top: 16px;
  color: #666;
  font-size: 14px;
}

.code-display {
  display: grid;
  gap: 24px;
}

.code-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.status-badge {
  background: #28a745;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
}

.code-main {
  margin-bottom: 24px;
}

.code-value {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  background: #f8f9fa;
  border: 2px dashed #007bff;
  border-radius: 8px;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.code-value:hover {
  background: #e3f2fd;
}

.code-text {
  font-size: 32px;
  font-weight: bold;
  color: #007bff;
  letter-spacing: 4px;
  font-family: 'Courier New', monospace;
}

.copy-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.copy-btn:hover {
  background: rgba(0,0,0,0.1);
}

.code-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}

.label {
  color: #666;
  font-size: 14px;
}

.value {
  font-weight: 500;
  color: #333;
}

.code-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-secondary, .btn-danger {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.qr-section {
  display: flex;
  justify-content: center;
}

.qr-placeholder {
  width: 200px;
  height: 200px;
  border: 2px dashed #ccc;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  color: #666;
}

.icon {
  font-size: 16px;
}
</style>