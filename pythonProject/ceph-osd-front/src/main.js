import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp(App)

// 全局配置
app.config.globalProperties.$ELEMENT = {
  size: 'small',
  zIndex: 3000
}

// 使用插件
app.use(ElementPlus)
app.mount('#app')