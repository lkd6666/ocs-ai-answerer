<template>
  <div class="config-panel">
    <el-card class="header-card">
      <div class="page-title">
        <el-icon class="page-title__icon"><Setting /></el-icon>
        <div>
          <h1>配置管理面板</h1>
          <p>在线管理 OCS AI Answerer 的通用运行配置</p>
        </div>
      </div>
    </el-card>

    <el-tabs v-model="activeTab" type="border-card" class="config-tabs">
      <!-- 首页 -->
      <el-tab-pane name="home">
        <template #label>
          <span class="tab-label">
            <el-icon><House /></el-icon>
            首页
          </span>
        </template>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header>
                <el-icon><Connection /></el-icon> 服务状态
              </template>
              <div class="status-item">
                <span>服务地址:</span>
                <el-tag>{{ apiBase }}</el-tag>
              </div>
              <div class="status-item">
                <span>已配置模型:</span>
                <el-tag type="success">{{ runtime.model_count }}</el-tag>
              </div>
              <div class="status-item">
                <span>已启用模型:</span>
                <el-tag :type="runtime.enabled_model_count > 0 ? 'success' : 'warning'">
                  {{ runtime.enabled_model_count }}
                </el-tag>
              </div>
              <div class="status-item">
                <span>图片模型:</span>
                <el-tag :type="runtime.has_multimodal_model ? 'success' : 'warning'">
                  {{ runtime.has_multimodal_model ? '已配置' : '未配置' }}
                </el-tag>
              </div>
              <div class="status-item">
                <span>整体状态:</span>
                <el-tag :type="runtime.can_answer_any ? 'success' : 'danger'">
                  {{ runtime.can_answer_any ? '可答题' : '未就绪' }}
                </el-tag>
              </div>
              <div v-if="runtime.init_error" class="status-item">
                <span>当前问题:</span>
                <el-tag type="danger">{{ runtime.init_error }}</el-tag>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header>
                <el-icon><Link /></el-icon> 快速导航
              </template>
              <el-space direction="vertical" :fill="true" style="width: 100%">
                <el-button type="primary" @click="$router.push('/viewer')" plain>
                  <el-icon><DataAnalysis /></el-icon> 答题记录
                </el-button>
                <el-button type="info" @click="$router.push('/models')" plain>
                  <el-icon><Grid /></el-icon> 模型管理
                </el-button>
                <el-button type="success" @click="$router.push('/docs')" plain>
                  <el-icon><Document /></el-icon> API文档
                </el-button>
                <el-button type="warning" @click="testConnection" plain>
                  <el-icon><Position /></el-icon> 连接测试
                </el-button>
              </el-space>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header>
                <el-icon><InfoFilled /></el-icon> 系统信息
              </template>
              <div class="status-item">
                <span>版本:</span>
                <el-tag type="info">v2.2</el-tag>
              </div>
              <div class="status-item">
                <span>监听端口:</span>
                <el-tag>{{ config.PORT || '5000' }}</el-tag>
              </div>
              <div class="status-item">
                <span>日志文件:</span>
                <el-tag>{{ config.CSV_LOG_FILE || 'ocs_answers_log.csv' }}</el-tag>
              </div>
              <div class="status-item">
                <span>可答题型:</span>
                <el-tag type="info">{{ readyQuestionTypesText }}</el-tag>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- AI参数 -->
      <el-tab-pane name="ai">
        <template #label>
          <span class="tab-label">
            <el-icon><Operation /></el-icon>
            AI参数
          </span>
        </template>
        <el-alert
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 20px"
        >
          模型是否支持思考、题型是否启用思考，请优先在模型管理页配置。这里保留通用生成参数和兼容思考策略，用于全局默认行为与旧逻辑兼容。
        </el-alert>
        <el-form :model="config" label-width="180px" label-position="left">
          <el-divider content-position="left">生成参数</el-divider>
          <el-form-item label="温度 (Temperature)">
            <el-slider v-model.number="config.TEMPERATURE" :min="0" :max="2" :step="0.1" show-input />
          </el-form-item>
          <el-form-item label="最大Token (普通)">
            <el-input-number v-model.number="config.MAX_TOKENS" :min="100" :max="8192" :step="100" />
          </el-form-item>
          <el-form-item label="最大Token (思考)">
            <el-input-number v-model.number="config.REASONING_MAX_TOKENS" :min="1000" :max="65536" :step="1000" />
          </el-form-item>
          <el-form-item label="Top P">
            <el-slider v-model.number="config.TOP_P" :min="0" :max="1" :step="0.05" show-input />
          </el-form-item>

          <el-divider content-position="left">兼容思考策略</el-divider>
          <el-alert
            type="warning"
            :closable="false"
            show-icon
            style="margin-bottom: 20px"
          >
            以下设置不会改变模型本身的能力声明，只会影响全局兼容逻辑。若已在模型管理中为题型开启思考，这里通常无需频繁修改。
          </el-alert>
          <el-form-item label="全局强制思考">
            <el-switch v-model="config.ENABLE_REASONING" active-value="true" inactive-value="false" />
            <el-text type="info" size="small" style="margin-left: 10px">对所有题型默认尝试启用思考模式</el-text>
          </el-form-item>
          <el-form-item label="默认思考强度">
            <el-radio-group v-model="config.REASONING_EFFORT">
              <el-radio value="low">低</el-radio>
              <el-radio value="medium">中</el-radio>
              <el-radio value="high">高</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="多选题自动启用">
            <el-switch v-model="config.AUTO_REASONING_FOR_MULTIPLE" active-value="true" inactive-value="false" />
            <el-text type="info" size="small" style="margin-left: 10px">在多选题上默认尝试思考模式</el-text>
          </el-form-item>
          <el-form-item label="图片题自动启用">
            <el-switch v-model="config.AUTO_REASONING_FOR_IMAGES" active-value="true" inactive-value="false" />
            <el-text type="info" size="small" style="margin-left: 10px">在含图题目上默认尝试思考模式</el-text>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 网络配置 -->
      <el-tab-pane name="network">
        <template #label>
          <span class="tab-label">
            <el-icon><Connection /></el-icon>
            网络配置
          </span>
        </template>
        <el-form :model="config" label-width="180px" label-position="left">
          <el-form-item label="HTTP 代理">
            <el-input v-model="config.HTTP_PROXY" placeholder="http://proxy:port" />
          </el-form-item>
          <el-form-item label="HTTPS 代理">
            <el-input v-model="config.HTTPS_PROXY" placeholder="https://proxy:port" />
          </el-form-item>
          <el-form-item label="请求超时 (秒)">
            <el-input-number v-model.number="config.TIMEOUT" :min="10" :max="3600" />
          </el-form-item>
          <el-form-item label="最大重试次数">
            <el-input-number v-model.number="config.MAX_RETRIES" :min="0" :max="10" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 系统配置 -->
      <el-tab-pane name="system">
        <template #label>
          <span class="tab-label">
            <el-icon><Tools /></el-icon>
            系统配置
          </span>
        </template>
        <el-form :model="config" label-width="180px" label-position="left">
          <el-form-item label="监听地址">
            <el-input v-model="config.HOST" placeholder="0.0.0.0" />
          </el-form-item>
          <el-form-item label="监听端口">
            <el-input-number v-model.number="config.PORT" :min="1000" :max="65535" />
          </el-form-item>
          <el-form-item label="调试模式">
            <el-switch v-model="config.DEBUG" active-value="true" inactive-value="false" />
          </el-form-item>
          <el-form-item label="日志级别">
            <el-select v-model="config.LOG_LEVEL">
              <el-option label="DEBUG" value="DEBUG" />
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
          </el-form-item>
          <el-form-item label="CSV日志文件">
            <el-input v-model="config.CSV_LOG_FILE" placeholder="ocs_answers_log.csv" />
          </el-form-item>
        </el-form>
        
        <!-- 安全设置 -->
        <el-divider content-position="left">
          <span class="divider-label">
            <el-icon><Lock /></el-icon>
            安全设置
          </span>
        </el-divider>
        <el-form :model="keyForm" label-width="180px" label-position="left">
          <el-alert
            title="修改访问密钥"
            type="warning"
            description="修改密钥后，所有已登录的设备需要重新输入新密钥。密钥长度至少8个字符。"
            :closable="false"
            style="margin-bottom: 20px"
          />
          <el-form-item label="当前密钥">
            <el-input
              v-model="keyForm.oldKey"
              type="password"
              placeholder="输入当前密钥"
              show-password
            />
          </el-form-item>
          <el-form-item label="新密钥">
            <el-input
              v-model="keyForm.newKey"
              type="password"
              placeholder="至少8个字符"
              show-password
            />
          </el-form-item>
          <el-form-item label="确认新密钥">
            <el-input
              v-model="keyForm.confirmKey"
              type="password"
              placeholder="再次输入新密钥"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button type="warning" @click="updateKey" :loading="keyLoading">
              <el-icon><Lock /></el-icon> 更新密钥
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <!-- 操作按钮 -->
    <el-card class="action-card">
      <el-space>
        <el-button type="primary" size="large" @click="saveConfig" :loading="saving">
          <el-icon><Check /></el-icon> 保存配置
        </el-button>
        <el-button type="success" size="large" @click="saveAndRestart" :loading="restarting">
          <el-icon><Refresh /></el-icon> 保存并重启
        </el-button>
        <el-button type="info" size="large" @click="loadConfig" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新配置
        </el-button>
        <el-button type="warning" size="large" @click="resetConfig">
          <el-icon><RefreshLeft /></el-icon> 重置为默认
        </el-button>
      </el-space>
    </el-card>
    
    <!-- 认证对话框（强制认证，不可关闭） -->
    <AuthDialog v-model="showAuthDialog" :closable="false" @success="onAuthSuccess" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axiosInstance from '../utils/axios'
import { hasApiKey, clearApiKey } from '../utils/auth'
import AuthDialog from './AuthDialog.vue'

// 使用认证的axios实例
const axios = axiosInstance

const activeTab = ref('home')
const loading = ref(false)
const saving = ref(false)
const restarting = ref(false)
const keyLoading = ref(false)
const showAuthDialog = ref(false)
const apiBase = window.location.origin

// 密钥表单
const keyForm = reactive({
  oldKey: '',
  newKey: '',
  confirmKey: ''
})

const runtime = reactive({
  model_count: 0,
  enabled_model_count: 0,
  ready_question_types: [],
  mapped_question_types: {},
  has_multimodal_model: false,
  can_answer_any: false,
  init_error: ''
})

const config = reactive({
  ENABLE_REASONING: 'false',
  REASONING_EFFORT: 'medium',
  AUTO_REASONING_FOR_MULTIPLE: 'true',
  AUTO_REASONING_FOR_IMAGES: 'true',
  TEMPERATURE: 0.1,
  MAX_TOKENS: 500,
  REASONING_MAX_TOKENS: 4096,
  TOP_P: 0.95,
  HTTP_PROXY: '',
  HTTPS_PROXY: '',
  TIMEOUT: 180,
  MAX_RETRIES: 3,
  HOST: '0.0.0.0',
  PORT: 5000,
  DEBUG: 'false',
  LOG_LEVEL: 'INFO',
  CSV_LOG_FILE: 'ocs_answers_log.csv'
})

const questionTypeNameMap = {
  single: '单选',
  multiple: '多选',
  judgement: '判断',
  completion: '填空',
  image: '图片'
}

const readyQuestionTypesText = computed(() => {
  const types = runtime.ready_question_types || []
  if (!types.length) return '无'
  return types.map(type => questionTypeNameMap[type] || type).join('、')
})

const loadConfig = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/config')
    const { _runtime, ...configData } = response.data
    Object.assign(config, configData)
    Object.assign(runtime, _runtime || {})
    
    // 转换数值类型
    config.TEMPERATURE = parseFloat(config.TEMPERATURE) || 0.1
    config.MAX_TOKENS = parseInt(config.MAX_TOKENS) || 500
    config.REASONING_MAX_TOKENS = parseInt(config.REASONING_MAX_TOKENS) || 4096
    config.TOP_P = parseFloat(config.TOP_P) || 0.95
    config.TIMEOUT = parseFloat(config.TIMEOUT) || 180
    config.MAX_RETRIES = parseInt(config.MAX_RETRIES) || 3
    config.PORT = parseInt(config.PORT) || 5000
    
    ElMessage.success('配置加载成功')
  } catch (error) {
    ElMessage.error('加载配置失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    // 转换为字符串
    const saveData = {
      ...config,
      TEMPERATURE: String(config.TEMPERATURE),
      MAX_TOKENS: String(config.MAX_TOKENS),
      REASONING_MAX_TOKENS: String(config.REASONING_MAX_TOKENS),
      TOP_P: String(config.TOP_P),
      TIMEOUT: String(config.TIMEOUT),
      MAX_RETRIES: String(config.MAX_RETRIES),
      PORT: String(config.PORT)
    }
    
    const { data } = await axios.post('/api/config', saveData)
    if (data && data.restart_required) {
      ElMessageBox.confirm(
        `配置已保存。其中 ${ (data.restart_keys || []).join('、') } 需要重启服务才能生效，是否立即重启？`,
        '部分配置需重启',
        {
          confirmButtonText: '立即重启',
          cancelButtonText: '稍后手动重启',
          type: 'warning',
        }
      ).then(() => {
        saveAndRestart(true)
      }).catch(() => {
        ElMessage.info('其余配置已即时生效；端口/调试等设置将在下次重启后生效')
      })
    } else {
      ElMessage.success('配置已保存并即时生效，无需重启服务')
    }
  } catch (error) {
    ElMessage.error('保存配置失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

// 保存并重启服务器
const saveAndRestart = async (skipConfirm = false) => {
  const proceed = () => {
    restarting.value = true
    return doSaveAndRestart()
  }
  if (skipConfirm === true) {
    return proceed()
  }
  ElMessageBox.confirm(
    '此操作将保存配置并重启服务器，大约需要 3-5 秒。确定继续吗？',
    '保存并重启',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(proceed).catch(() => {})
}

const doSaveAndRestart = async () => {
    try {
      // 1. 先保存配置
      const saveData = {
        ...config,
        TEMPERATURE: String(config.TEMPERATURE),
        MAX_TOKENS: String(config.MAX_TOKENS),
        REASONING_MAX_TOKENS: String(config.REASONING_MAX_TOKENS),
        TOP_P: String(config.TOP_P),
        TIMEOUT: String(config.TIMEOUT),
        MAX_RETRIES: String(config.MAX_RETRIES),
        PORT: String(config.PORT)
      }
      
      await axios.post('/api/config', saveData)
      ElMessage.success('配置已保存')
      
      // 2. 触发重启
      await axios.post('/api/restart')
      ElMessage.info('服务器正在重启...')
      
      // 3. 轮询检测服务器状态
      let attempts = 0
      const maxAttempts = 30 // 最多尝试30次（30秒）
      
      const checkHealth = async () => {
        try {
          const response = await axios.get('/api/health', { timeout: 2000 })
          if (response.status === 200) {
            restarting.value = false
            ElMessage.success('服务器重启成功')
            // 重新加载配置
            await loadConfig()
            return true
          }
        } catch (error) {
          // 连接失败，继续轮询
          return false
        }
      }
      
      // 等待2秒后开始轮询（给服务器时间关闭）
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const pollInterval = setInterval(async () => {
        attempts++
        
        if (attempts > maxAttempts) {
          clearInterval(pollInterval)
          restarting.value = false
          ElMessage.error('服务器重启超时，请手动检查')
          return
        }
        
        const isHealthy = await checkHealth()
        if (isHealthy) {
          clearInterval(pollInterval)
        } else {
          console.log(`轮询服务器状态... (${attempts}/${maxAttempts})`)
        }
      }, 1000) // 每秒检查一次
      
    } catch (error) {
      restarting.value = false
      if (error.code === 'ECONNABORTED' || error.message.includes('Network Error')) {
        // 服务器正在重启，这是预期行为
        ElMessage.info('服务器正在重启，请稍候...')
      } else {
        ElMessage.error('操作失败: ' + error.message)
      }
    }
}

const resetConfig = () => {
  ElMessageBox.confirm(
    '确定要重置所有配置为默认值吗？此操作不可撤销！',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    config.ENABLE_REASONING = 'false'
    config.REASONING_EFFORT = 'medium'
    config.AUTO_REASONING_FOR_MULTIPLE = 'true'
    config.AUTO_REASONING_FOR_IMAGES = 'true'
    config.TEMPERATURE = 0.1
    config.MAX_TOKENS = 500
    config.REASONING_MAX_TOKENS = 4096
    config.TOP_P = 0.95
    config.TIMEOUT = 180
    config.MAX_RETRIES = 3
    ElMessage.info('配置已重置为默认值')
  }).catch(() => {})
}

const testConnection = async () => {
  try {
    const start = Date.now()
    await axios.head(`/?t=${start}`)
    const latency = Date.now() - start
    ElMessage.success(`连接成功！延迟: ${latency}ms`)
  } catch (error) {
    ElMessage.error('连接失败: ' + error.message)
  }
}

// 更新访问密钥
const updateKey = async () => {
  // 验证表单
  if (!keyForm.oldKey) {
    ElMessage.warning('请输入当前密钥')
    return
  }
  if (!keyForm.newKey) {
    ElMessage.warning('请输入新密钥')
    return
  }
  if (keyForm.newKey.length < 8) {
    ElMessage.warning('新密钥长度至少8个字符')
    return
  }
  if (keyForm.newKey !== keyForm.confirmKey) {
    ElMessage.warning('两次输入的新密钥不一致')
    return
  }
  
  keyLoading.value = true
  try {
    const response = await axios.post('/api/auth/update-key', {
      old_key: keyForm.oldKey,
      new_key: keyForm.newKey
    })
    
    if (response.data.success) {
      ElMessage.success('密钥更新成功，请使用新密钥重新登录')
      
      // 清除表单
      keyForm.oldKey = ''
      keyForm.newKey = ''
      keyForm.confirmKey = ''
      
      // 清除本地存储的密钥
      clearApiKey()
      
      // 3秒后刷新页面
      setTimeout(() => {
        window.location.reload()
      }, 3000)
    } else {
      ElMessage.error(response.data.error || '更新失败')
    }
  } catch (error) {
    console.error('更新密钥失败:', error)
    ElMessage.error('更新失败: ' + (error.response?.data?.error || error.message))
  } finally {
    keyLoading.value = false
  }
}

// 认证成功处理
const onAuthSuccess = (apiKey) => {
  console.log('认证成功，重新加载配置')
  loadConfig()
}

// 监听全局认证事件
const handleAuthRequired = () => {
  showAuthDialog.value = true
}

onMounted(() => {
  // 检查是否有API密钥
  if (!hasApiKey()) {
    showAuthDialog.value = true
  } else {
    loadConfig()
  }
  
  // 监听认证事件
  window.addEventListener('auth-required', handleAuthRequired)
})

onUnmounted(() => {
  window.removeEventListener('auth-required', handleAuthRequired)
})
</script>

<style scoped>
.config-panel {
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.page-title__icon {
  font-size: 30px;
  color: #409eff;
}

.header-card h1 {
  margin: 0 0 10px 0;
  color: #409eff;
}

.header-card p {
  margin: 0;
  color: #909399;
}

.dark .page-title__icon,
.dark .header-card h1 {
  color: #79bbff;
}

.dark .header-card p {
  color: #a8abb2;
}

.config-tabs {
  margin-bottom: 20px;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.action-card {
  text-align: center;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.dark .status-item {
  border-bottom-color: #414243;
}

.status-item:last-child {
  border-bottom: none;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

.divider-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>
