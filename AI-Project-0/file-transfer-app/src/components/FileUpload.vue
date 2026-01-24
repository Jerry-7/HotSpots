<template>
  <div class="file-upload">
    <div 
      class="drop-zone"
      :class="{ 'drag-over': isDragOver }"
      @drop="handleDrop"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
      @dragenter.prevent
    >
      <input 
        ref="fileInput"
        type="file" 
        multiple 
        @change="handleFileSelect"
        style="display: none"
      >
      <div class="upload-content">
        <i class="upload-icon">📁</i>
        <p>拖拽文件到此处或 <button @click="selectFiles">选择文件</button></p>
      </div>
    </div>
    
    <div v-if="files.length" class="file-list">
      <div v-for="file in files" :key="file.id" class="file-item">
        <span>{{ file.name }}</span>
        <span>{{ formatFileSize(file.size) }}</span>
        <div class="progress-bar">
          <div class="progress" :style="{ width: file.progress + '%' }"></div>
        </div>
        <button @click="removeFile(file.id)">删除</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useFileStore } from '@/stores/fileStore'

const fileStore = useFileStore()
const fileInput = ref<HTMLInputElement>()
const isDragOver = ref(false)
const files = ref<any[]>([])

const selectFiles = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    addFiles(Array.from(target.files))
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  if (event.dataTransfer?.files) {
    addFiles(Array.from(event.dataTransfer.files))
  }
}

const addFiles = (newFiles: File[]) => {
  newFiles.forEach(file => {
    const fileObj = {
      id: Date.now() + Math.random(),
      name: file.name,
      size: file.size,
      file,
      progress: 0
    }
    files.value.push(fileObj)
    uploadFile(fileObj)
  })
}

const uploadFile = async (fileObj: any) => {
  // 模拟上传进度
  const interval = setInterval(() => {
    fileObj.progress += 10
    if (fileObj.progress >= 100) {
      clearInterval(interval)
      fileStore.addFile(fileObj)
    }
  }, 200)
}

const removeFile = (id: number) => {
  files.value = files.value.filter(f => f.id !== id)
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style scoped>
.drop-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  transition: all 0.3s;
}

.drag-over {
  border-color: #007bff;
  background-color: #f8f9fa;
}

.upload-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.file-list {
  margin-top: 20px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 8px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: #007bff;
  transition: width 0.3s;
}
</style>