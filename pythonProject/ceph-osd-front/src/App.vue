<template>
  <div id="app">
    <!-- 导航栏 -->
    <el-header style="background-color: #409EFF; color: white; height: 60px;">
      <h1>Ceph 集群管理系统</h1>
    </el-header>

    <!-- 主内容区 -->
    <el-main>
      <!-- 引入树形组件 -->
      <tree-view />
    </el-main>

    <!-- 页脚 -->
    <el-footer style="text-align: center; padding: 20px;">
      © 2023 Ceph Manager
    </el-footer>
  </div>
</template>

<script>
import TreeView from '@/components/TreeView.vue'

export default {
  name: 'App',
  components: {
    TreeView
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.el-header, .el-footer {
  line-height: 60px;
}

.el-main {
  flex: 1;
  padding: 20px;
}
</style>