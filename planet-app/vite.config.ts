import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    // 确保 .jsx 在解析扩展名列表中 (通常是默认的)
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json']
  }
})
