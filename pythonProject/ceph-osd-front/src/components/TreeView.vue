<template>
  <div class="ceph-tree-container">
    <!-- 查询操作区 -->
    <div class="query-panel">
      <el-button
          type="primary"
          @click="fetchTreeData"
          :loading="loading"
          :disabled="showTree"
      >
        <el-icon>
          <Refresh/>
        </el-icon>
        查询树结构
      </el-button>

      <el-button
          v-if="showReset"
          @click="resetTree"
      >
        <el-icon>
          <Delete/>
        </el-icon>
        重置
      </el-button>
    </div>

    <!-- 空状态提示 -->
    <div v-if="!showTree" class="empty-state">
      <el-empty description="点击查询按钮加载树结构"/>
    </div>

    <!-- 树形展示区 -->
    <div v-if="showTree" class="tree-wrapper">
      <el-tree
          ref="treeRef"
          :data="treeData"
          :props="treeProps"
          node-key="id"
          draggable
          :allow-drop="allowDrop"
          @node-drop="handleNodeDrop"
          highlight-current
          default-expand-all
      >
        <template #default="{ node, data }">
          <span class="node-label">
            {{ data.label }}
            <span class="node-type-badge" :class="data.type">
              {{ typeLabels[data.type] }}
            </span>
          </span>
          <div class="node-actions">
            <el-button
                v-if="canAddChild(data)"
                size="small"
                type="success"
                @click.stop="showAddDialog(data)"
            >
              <el-icon>
                <Plus/>
              </el-icon>
            </el-button>
            <el-button
                v-if="data.type !== 'root' && data.type !== 'osd'"
                size="small"
                type="danger"
                @click.stop="handleDelete(data)"
            >
              <el-icon>
                <Delete/>
              </el-icon>
            </el-button>
          </div>
        </template>
      </el-tree>
    </div>

    <!-- 添加节点对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="400px">
      <el-form :model="newNodeForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="newNodeForm.name"/>
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select
              v-model="newNodeForm.type"
              placeholder="选择节点类型"
              :disabled="selectedParentNode?.type === 'root'"
          >
            <el-option
                v-for="type in allowedChildTypes"
                :key="type.value"
                :label="type.label"
                :value="type.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAddNode">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import {defineComponent, ref, reactive, computed} from 'vue';
import {ElMessage} from 'element-plus';
import {Refresh, Delete, Plus} from '@element-plus/icons-vue';

export default defineComponent({
  name: 'CephTree',
  components: {Refresh, Delete, Plus},
  setup() {
    // 节点类型定义
    const NODE_TYPES = {
      ROOT: 'root',
      DATACENTER: 'datacenter',
      RACK: 'rack',
      HOST: 'host',
      OSD: 'osd'
    };

    // 类型层级关系
    const TYPE_HIERARCHY = {
      [NODE_TYPES.ROOT]: [NODE_TYPES.DATACENTER, NODE_TYPES.RACK, NODE_TYPES.HOST, NODE_TYPES.OSD],
      [NODE_TYPES.DATACENTER]: [NODE_TYPES.RACK, NODE_TYPES.HOST, NODE_TYPES.OSD],
      [NODE_TYPES.RACK]: [NODE_TYPES.HOST, NODE_TYPES.OSD],
      [NODE_TYPES.HOST]: [NODE_TYPES.OSD],
      [NODE_TYPES.OSD]: [] // OSD 不能有子节点
    };

    // 类型显示标签
    const TYPE_LABELS = {
      [NODE_TYPES.ROOT]: '根节点',
      [NODE_TYPES.DATACENTER]: '数据中心',
      [NODE_TYPES.RACK]: '机架',
      [NODE_TYPES.HOST]: '主机',
      [NODE_TYPES.OSD]: 'OSD'
    };

    // 状态管理
    const loading = ref(false);
    const showTree = ref(false);
    const showReset = ref(false);
    const treeData = ref([]);
    const treeRef = ref(null);
    const dialogVisible = ref(false);
    const selectedParentNode = ref(null);
    const error = ref(null);

    const newNodeForm = reactive({
      name: '',
      type: NODE_TYPES.DATACENTER
    });

    // 数据处理 - 确保所有children都是数组
    const processTreeData = (apiData) => {
      const convertNode = (node) => {
        const baseNode = {
          id: node.id,
          label: node.name,
          type: node.type,
          children: [] // 默认空数组
        };

        if (Array.isArray(node.children)) {
          baseNode.children = node.children.map(convertNode);
        }

        return baseNode;
      };

      // 返回包含根节点的数组
      return [{
        id: 'root',
        label: apiData.cluster_name || 'Ceph Cluster',
        type: NODE_TYPES.ROOT,
        children: Array.isArray(apiData.nodes)
            ? apiData.nodes.map(convertNode)
            : []
      }];
    };

    // 模拟API请求
    const fetchTreeData = async () => {
      try {
        loading.value = true;
        error.value = null;

        // 模拟API请求
        await new Promise(resolve => setTimeout(resolve, 800));

        // 模拟API返回数据 - 确保所有节点都有children数组
        const mockData = {
          cluster_name: "My Ceph Cluster",
          nodes: [
            {
              id: "dc-1",
              name: "Beijing DC",
              type: NODE_TYPES.DATACENTER,
              children: [
                {
                  id: "rack-1",
                  name: "Rack A",
                  type: NODE_TYPES.RACK,
                  children: [
                    {
                      id: "host-1",
                      name: "Node-1",
                      type: NODE_TYPES.HOST,
                      children: [
                        {
                          id: "osd-1",
                          name: "OSD-1",
                          type: NODE_TYPES.OSD,
                          children: [] // OSD节点也要有children数组
                        },
                        {
                          id: "osd-2",
                          name: "OSD-2",
                          type: NODE_TYPES.OSD,
                          children: [] // OSD节点也要有children数组
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        };

        treeData.value = processTreeData(mockData);
        showTree.value = true;
        showReset.value = true;
        ElMessage.success('树结构加载成功');
      } catch (err) {
        error.value = err;
        ElMessage.error('获取树结构失败');
      } finally {
        loading.value = false;
      }
    };

    // 重置树结构
    const resetTree = () => {
      treeData.value = [];
      showTree.value = false;
      showReset.value = false;
    };

    // 计算可用的子节点类型
    const allowedChildTypes = computed(() => {
      if (!selectedParentNode.value) {
        // 如果是根节点，可以添加所有类型的节点（除了 root 自身）
        return Object.values(NODE_TYPES)
            .filter(type => type !== NODE_TYPES.ROOT)
            .map(type => ({value: type, label: TYPE_LABELS[type]}));
      }

      // 否则返回当前节点允许添加的所有更低级别的节点类型
      return TYPE_HIERARCHY[selectedParentNode.value.type].map(type => ({
        value: type,
        label: TYPE_LABELS[type]
      }));
    });

    // 对话框标题
    const dialogTitle = computed(() => {
      if (!selectedParentNode.value) return '添加根节点';
      return `添加子节点到 ${selectedParentNode.value.label}`;
    });

    // 检查节点是否可以添加子节点
    const canAddChild = (node) => {
      return TYPE_HIERARCHY[node.type]?.length > 0;
    };

    // 显示添加对话框
    const showAddDialog = (parentNode) => {
      if (!canAddChild(parentNode)) {
        ElMessage.warning('当前节点不能添加子节点');
        return;
      }

      selectedParentNode.value = parentNode;
      newNodeForm.name = '';
      newNodeForm.type = allowedChildTypes.value[0]?.value || '';
      dialogVisible.value = true;
    };

    // 确认添加节点
    const confirmAddNode = () => {
      if (!newNodeForm.name.trim()) {
        ElMessage.error('请输入节点名称');
        return;
      }

      // 验证节点类型是否符合层级关系
      if (selectedParentNode.value) {
        const allowedTypes = TYPE_HIERARCHY[selectedParentNode.value.type] || [];
        if (!allowedTypes.includes(newNodeForm.type)) {
          ElMessage.error('不能添加此类型的子节点');
          return;
        }
      }

      const newNode = {
        id: `${newNodeForm.type}-${Date.now()}`,
        label: newNodeForm.name,
        type: newNodeForm.type,
        children: []
      };

      if (selectedParentNode.value) {
        if (!Array.isArray(selectedParentNode.value.children)) {
          selectedParentNode.value.children = [];
        }
        selectedParentNode.value.children.push(newNode);
        treeRef.value.updateKeyChildren(
            selectedParentNode.value.id,
            [...selectedParentNode.value.children]
        );
      } else {
        treeData.value[0].children.push(newNode);
      }

      dialogVisible.value = false;
      ElMessage.success('节点添加成功');
    };

    // 查找父节点
    const findParentNode = (nodes, nodeId, parent = null) => {
      if (!Array.isArray(nodes)) return null;

      for (const node of nodes) {
        if (node.id === nodeId) return parent;
        if (Array.isArray(node.children)) {
          const found = findParentNode(node.children, nodeId, node);
          if (found) return found;
        }
      }
      return null;
    };

    // 删除节点
    const handleDelete = (node) => {
      const parent = findParentNode(treeData.value, node.id);
      if (parent) {
        parent.children = (parent.children || []).filter(n => n.id !== node.id);
        ElMessage.success('节点删除成功');
      }
    };

    // 拖拽验证
    const allowDrop = (draggingNode, dropNode, type) => {
      const draggingType = draggingNode.data.type;
      const dropType = dropNode.data.type;

      // 不能拖拽到OSD节点下
      if (dropType === NODE_TYPES.OSD) return false;

      // 根据层级关系验证
      if (type === 'inner') {
        return TYPE_HIERARCHY[dropType].includes(draggingType);
      } else {
        const parent = findParentNode(treeData.value, dropNode.data.id);
        return parent ? TYPE_HIERARCHY[parent.type].includes(draggingType) : false;
      }
    };

    // 处理拖拽完成
    const handleNodeDrop = () => {
      ElMessage.success('节点移动成功');
    };

    return {
      // 状态
      loading,
      showTree,
      showReset,
      error,

      // 数据
      treeData,
      treeProps: {
        label: 'label',
        children: 'children'
      },
      typeLabels: TYPE_LABELS,

      // 方法
      fetchTreeData,
      resetTree,
      allowedChildTypes,
      canAddChild,
      showAddDialog,
      confirmAddNode,
      handleDelete,
      allowDrop,
      handleNodeDrop,

      // 模板引用
      treeRef,
      dialogVisible,
      dialogTitle,
      newNodeForm,
      selectedParentNode
    };
  }
});
</script>

<style scoped>
.ceph-tree-container {
  padding: 20px;
}

.query-panel {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  gap: 10px;
}

.empty-state {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 4px;
  border: 1px dashed #dcdfe6;
}

.tree-wrapper {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  background: #fff;
}

.node-label {
  margin-right: 10px;
}

.node-type-badge {
  display: inline-block;
  padding: 0 6px;
  font-size: 12px;
  line-height: 18px;
  border-radius: 3px;
  color: #fff;
}

.node-type-badge.root {
  background-color: #909399;
}

.node-type-badge.datacenter {
  background-color: #409EFF;
}

.node-type-badge.rack {
  background-color: #67C23A;
}

.node-type-badge.host {
  background-color: #E6A23C;
}

.node-type-badge.osd {
  background-color: #F56C6C;
}

.node-actions {
  display: inline-block;
  margin-left: 10px;
}

:deep(.el-tree-node__content) {
  height: 36px;
  padding: 5px 0;
}
</style>