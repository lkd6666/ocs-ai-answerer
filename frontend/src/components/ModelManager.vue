<template>
  <div class="model-manager">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Grid /></el-icon>
            自定义模型管理
          </span>
          <el-button type="primary" @click="showAddDialog" :icon="Plus">
            添加模型
          </el-button>
        </div>
      </template>
      <el-alert 
        title="提示" 
        type="info" 
        :closable="false"
        show-icon
      >
        在这里管理自定义AI模型，为不同题型指定特定模型，并精确控制每个模型的参数。
      </el-alert>
    </el-card>

    <!-- 模型列表 -->
    <el-card class="models-card">
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="模型列表" name="models">
          <div class="toolbar">
            <el-input
              v-model="searchQuery"
              placeholder="搜索模型名称或ID"
              :prefix-icon="Search"
              style="width: 300px; margin-right: 10px;"
              clearable
            />
            <el-switch
              v-model="showEnabledOnly"
              active-text="仅显示启用的"
              @change="loadModels"
            />
          </div>

          <el-table
            :data="filteredModels"
            style="width: 100%; margin-top: 20px;"
            v-loading="loading"
          >
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                  {{ row.enabled ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="模型名称" min-width="180">
              <template #default="{ row }">
                <div>
                  <strong>{{ row.name }}</strong>
                  <el-tag v-if="row.is_builtin" type="info" size="small" style="margin-left: 8px;">
                    内置预设
                  </el-tag>
                  <div style="color: #909399; font-size: 12px;">
                    ID: {{ row.id }}
                  </div>
                  <div v-if="row.is_builtin" style="color: #E6A23C; font-size: 11px; margin-top: 2px;">
                    <el-icon><InfoFilled /></el-icon> 可直接编辑或删除
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="提供商" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ row.provider }}</el-tag>
              </template>
            </el-table-column>

            <el-table-column label="模型" min-width="180">
              <template #default="{ row }">
                <el-text truncated>{{ row.model_name }}</el-text>
              </template>
            </el-table-column>

            <el-table-column label="特性" width="180">
              <template #default="{ row }">
                <el-tag v-if="row.is_multimodal" type="success" size="small" style="margin-right: 5px;">
                  <el-icon><Picture /></el-icon> 多模态
                </el-tag>
                <el-tag v-if="row.supports_reasoning" type="warning" size="small">
                  <el-icon><ChatDotRound /></el-icon> 思考
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="Token限制" width="100" align="center">
              <template #default="{ row }">
                {{ row.max_tokens }}
              </template>
            </el-table-column>

            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="viewModel(row)">
                  <el-icon><View /></el-icon> 查看
                </el-button>
                <el-button link type="primary" size="small" @click="testModel(row)">
                  <el-icon><VideoPlay /></el-icon> 测试
                </el-button>
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click="editModel(row)"
                >
                  <el-icon><Edit /></el-icon> 编辑
                </el-button>
                
                <el-button
                  link
                  type="danger"
                  size="small"
                  @click="deleteModel(row)"
                >
                  <el-icon><Delete /></el-icon> 删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="题型映射" name="mapping">
          <el-alert 
            title="题型映射说明" 
            type="info" 
            :closable="false"
            style="margin-bottom: 20px;"
          >
            为不同题型指定使用的模型。系统会按列表顺序优先使用靠前的模型，支持自动故障转移。
          </el-alert>

          <div v-for="(config, type) in questionTypeMappings" :key="type" class="type-mapping">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
              <h3 style="margin: 0;">{{ getTypeName(type) }}</h3>
              <div style="display: flex; align-items: center; gap: 8px;">
                <el-switch
                  v-model="config.enable_reasoning"
                  @change="saveTypeMapping(type)"
                  :disabled="hasNativeReasoner(config.models) || !canEnableReasoning(config.models)"
                >
                  <template #active-action>
                    <el-icon style="font-size: 12px;"><ChatDotRound /></el-icon>
                  </template>
                </el-switch>
                <span style="font-size: 13px; color: #909399;">
                  {{ config.enable_reasoning ? '启用思考' : '普通模式' }}
                </span>
                <el-tooltip v-if="hasNativeReasoner(config.models)" content="所有模型都是原生思考模型，自动启用思考" placement="top">
                  <el-icon style="color: #67c23a;"><CircleCheckFilled /></el-icon>
                </el-tooltip>
                <el-tooltip v-else-if="!canEnableReasoning(config.models) && config.models.length > 0" content="所选模型均不支持思考模式" placement="top">
                  <el-icon style="color: #f56c6c;"><WarningFilled /></el-icon>
                </el-tooltip>
              </div>
            </div>
            <el-select
              v-model="config.models"
              multiple
              placeholder="选择模型（可多选，按优先级排序）"
              style="width: 100%;"
              @change="saveTypeMapping(type)"
            >
              <el-option
                v-for="model in enabledModelsList"
                :key="model.id"
                :label="`${model.name} (${model.id})`"
                :value="model.id"
                :disabled="type === 'image' && !model.is_multimodal"
              >
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span :style="{ opacity: (type === 'image' && !model.is_multimodal) ? 0.5 : 1 }">
                    {{ model.name }}
                  </span>
                  <div style="display: flex; gap: 4px;">
                    <el-tag v-if="model.is_multimodal" type="success" size="small">
                      <el-icon style="vertical-align: middle;"><Picture /></el-icon>
                      多模态
                    </el-tag>
                    <el-tag v-else type="info" size="small">
                      <el-icon style="vertical-align: middle;"><Document /></el-icon>
                      文本
                    </el-tag>
                    <el-tag v-if="model.supports_reasoning" type="warning" size="small">
                      <el-icon style="vertical-align: middle;"><ChatDotRound /></el-icon>
                      思考
                    </el-tag>
                  </div>
                </div>
              </el-option>
            </el-select>
            <div class="mapping-tip">
              <el-icon><InfoFilled /></el-icon>
              {{ getTypeTip(type) }}
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 添加/编辑模型对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑模型' : '添加模型'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="modelFormRef"
        :model="modelForm"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="模型ID" prop="model_id" v-if="!isEdit">
          <el-input v-model="modelForm.model_id" placeholder="唯一标识符，如: gpt4_vision" />
          <div class="form-tip">模型的唯一标识符，添加后不可修改</div>
        </el-form-item>

        <el-form-item label="显示名称" prop="name">
          <el-input v-model="modelForm.name" placeholder="如: GPT-4 Vision" />
        </el-form-item>

        <el-form-item label="提供商" prop="provider">
          <el-select v-model="modelForm.provider" style="width: 100%;">
            <el-option label="OpenAI 兼容" value="openai" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item label="API协议" prop="api_protocol">
          <el-select v-model="modelForm.api_protocol" style="width: 100%;">
            <el-option label="自动识别（推荐）" value="openai_compat" />
            <el-option label="OpenAI Responses API" value="responses" />
            <el-option label="Chat Completions 兼容" value="chat_completions" />
          </el-select>
          <div class="form-tip">
            OpenAI 官方模型建议优先使用 Responses API；DeepSeek、豆包及大多数兼容网关继续使用 Chat Completions。
          </div>
        </el-form-item>

        <el-form-item label="API密钥" prop="api_key">
          <el-input
            v-model="modelForm.api_key"
            type="password"
            placeholder="sk-..."
            show-password
          />
        </el-form-item>

        <el-form-item label="API基础URL" prop="base_url">
          <el-input v-model="modelForm.base_url" placeholder="https://api.example.com/v1" />
          <div class="form-tip">API的基础URL，通常以/v1结尾</div>
        </el-form-item>

        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="modelForm.model_name" placeholder="gpt-4-vision-preview" />
          <div class="form-tip">实际调用时使用的模型名称</div>
        </el-form-item>

        <el-divider content-position="left">模型特性</el-divider>

        <el-form-item label="多模态支持">
          <el-switch v-model="modelForm.is_multimodal" />
          <div class="form-tip">是否支持图片输入（多模态模型）</div>
        </el-form-item>

        <el-form-item label="思考模式">
          <el-switch v-model="modelForm.supports_reasoning" />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            是否支持深度推理/思考模式（如DeepSeek Reasoner）
          </div>
        </el-form-item>

        <!-- 思考模式参数配置 -->
        <el-collapse v-if="modelForm.supports_reasoning" style="margin-bottom: 20px;">
          <el-collapse-item name="reasoning">
            <template #title>
              <span class="collapse-title">
                <el-icon><ChatDotRound /></el-icon>
                思考模式参数配置
              </span>
            </template>
            <el-alert
              type="info"
              :closable="false"
              style="margin-bottom: 15px;"
            >
              <div style="font-size: 12px;">
                不同的模型可能使用不同的参数名称和值。请根据模型的API文档配置。
              </div>
            </el-alert>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="参数名称" prop="reasoning_param_name">
                  <el-input
                    v-model="modelForm.reasoning_param_name"
                    placeholder="reasoning_effort"
                  />
                  <div class="form-tip">
                    <el-icon><InfoFilled /></el-icon>
                    API请求中的参数名称
                  </div>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="参数值" prop="reasoning_param_value">
                  <el-input
                    v-model="modelForm.reasoning_param_value"
                    placeholder="medium"
                  />
                  <div class="form-tip">
                    <el-icon><InfoFilled /></el-icon>
                    参数的具体值
                  </div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-alert
              type="warning"
              :closable="false"
            >
              <div style="font-size: 12px;">
                <strong>常见配置示例：</strong>
                <ul style="margin: 5px 0; padding-left: 20px;">
                  <li><strong>DeepSeek/豆包：</strong> 参数名=<code>reasoning_effort</code>，值=<code>low/medium/high</code></li>
                  <li><strong>OpenAI Responses：</strong> 参数名可保留 <code>reasoning_effort</code>，系统会自动转换为 <code>reasoning.effort</code>，值支持 <code>minimal/low/medium/high/xhigh</code></li>
                  <li><strong>Claude Thinking：</strong> 参数名=<code>thinking</code>，值=<code>enabled</code></li>
                  <li><strong>自定义模型：</strong> 请参考模型的API文档</li>
                </ul>
                <div style="margin-top: 10px;">
                  <strong>注意：</strong>OpenAI 官方最新推理模型建议选择 Responses API；旧兼容接口和第三方网关仍可继续使用现有参数。
                </div>
              </div>
            </el-alert>
          </el-collapse-item>
        </el-collapse>

        <el-divider content-position="left">Token参数</el-divider>

        <el-alert
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <template #title>
            <el-icon><InfoFilled /></el-icon>
            参数说明
          </template>
          <div style="font-size: 13px; line-height: 1.6;">
            <p><strong>最大Tokens</strong>: 控制生成内容的最大长度（100-100000）</p>
            <p><strong>Temperature</strong>: 控制输出的随机性（0-2）。值越低越确定，越高越有创造性。推荐0.1-0.3</p>
            <p><strong>Top-P</strong>: 核采样参数（0-1）。控制输出的多样性。推荐0.9-0.95</p>
          </div>
        </el-alert>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最大Tokens" prop="max_tokens">
              <el-input-number
                v-model="modelForm.max_tokens"
                :min="100"
                :max="100000"
                :step="100"
                style="width: 100%;"
              />
              <div class="form-tip">
                <el-icon><InfoFilled /></el-icon>
                单次生成的最大token数量，影响回答长度和成本
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Temperature" prop="temperature">
              <el-input-number
                v-model="modelForm.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                :precision="1"
                style="width: 100%;"
              />
              <div class="form-tip">
                <el-icon><InfoFilled /></el-icon>
                0=确定性输出，2=高度随机。答题推荐0.1
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Top-P" prop="top_p">
              <el-input-number
                v-model="modelForm.top_p"
                :min="0"
                :max="1"
                :step="0.05"
                :precision="2"
                style="width: 100%;"
              />
              <div class="form-tip">
                <el-icon><InfoFilled /></el-icon>
                核采样阈值，控制输出多样性。推荐0.95
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用状态">
              <el-switch v-model="modelForm.enabled" />
              <div class="form-tip">
                <el-icon><InfoFilled /></el-icon>
                禁用后该模型不会被使用
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveModel" :loading="saving">
          {{ isEdit ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看模型详情对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      :title="`模型详情 - ${viewingModel?.name || ''}`"
      width="700px"
    >
      <div v-if="viewingModel" class="model-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模型ID">
            {{ viewingModel.id }}
          </el-descriptions-item>
          <el-descriptions-item label="模型类型">
            <el-tag v-if="viewingModel.is_builtin" type="info" size="small">内置预设</el-tag>
            <el-tag v-else type="success" size="small">自定义模型</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="显示名称">
            {{ viewingModel.name }}
          </el-descriptions-item>
          <el-descriptions-item label="提供商">
            {{ viewingModel.provider }}
          </el-descriptions-item>
          <el-descriptions-item label="API协议" :span="2">
            {{ viewingModel.api_protocol || 'openai_compat' }}
          </el-descriptions-item>
          <el-descriptions-item label="API基础URL" :span="2">
            {{ viewingModel.base_url }}
          </el-descriptions-item>
          <el-descriptions-item label="模型名称" :span="2">
            {{ viewingModel.model_name }}
          </el-descriptions-item>
          <el-descriptions-item label="API密钥" :span="2">
            <el-text type="info">{{ viewingModel.api_key }}</el-text>
          </el-descriptions-item>
          <el-descriptions-item label="多模态支持">
            <el-tag v-if="viewingModel.is_multimodal" type="success" size="small">
              <el-icon><Picture /></el-icon> 支持
            </el-tag>
            <el-tag v-else type="info" size="small">不支持</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="思考模式">
            <el-tag v-if="viewingModel.supports_reasoning" type="warning" size="small">
              <el-icon><ChatDotRound /></el-icon> 支持
            </el-tag>
            <el-tag v-else type="info" size="small">不支持</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="最大Tokens">
            {{ viewingModel.max_tokens }}
          </el-descriptions-item>
          <el-descriptions-item label="Temperature">
            {{ viewingModel.temperature }}
          </el-descriptions-item>
          <el-descriptions-item label="Top-P">
            {{ viewingModel.top_p }}
          </el-descriptions-item>
          <el-descriptions-item label="启用状态">
            <el-switch :model-value="viewingModel.enabled" disabled />
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDate(viewingModel.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间" :span="2">
            {{ formatDate(viewingModel.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <el-alert
          v-if="viewingModel.is_builtin"
          type="warning"
          :closable="false"
          style="margin-top: 20px;"
        >
          <template #title>
            <el-icon><InfoFilled /></el-icon>
            内置预设说明
          </template>
          此模型是系统提供的初始预设模板。你可以直接编辑、测试、删除，也可以把它当作普通模型继续使用。
        </el-alert>
      </div>

      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="editFromView">
          编辑配置
        </el-button>
      </template>
    </el-dialog>

    <!-- 测试模型对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试模型连接"
      width="600px"
    >
      <el-form label-width="100px">
        <el-form-item label="测试提示词">
          <el-input
            v-model="testPrompt"
            type="textarea"
            :rows="3"
            placeholder="输入测试提示词，如：你好，请介绍一下你自己"
          />
        </el-form-item>
      </el-form>

      <div v-if="testResult" class="test-result">
        <el-alert
          :title="testResult.success ? '连接成功！' : '连接失败'"
          :type="testResult.success ? 'success' : 'error'"
          :closable="false"
          show-icon
        >
          <template v-if="testResult.success">
            <div><strong>延迟:</strong> {{ testResult.latency }}秒</div>
            <div><strong>Token使用:</strong> 输入{{ testResult.tokens.prompt }} + 输出{{ testResult.tokens.completion }} = {{ testResult.tokens.total }}</div>
            <div style="margin-top: 10px;"><strong>模型响应:</strong></div>
            <el-input
              type="textarea"
              :rows="4"
              :model-value="testResult.response"
              readonly
              style="margin-top: 5px;"
            />
          </template>
          <div v-else>
            {{ testResult.error }}
          </div>
        </el-alert>
      </div>

      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="runTest" :loading="testing">
          开始测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Edit, Delete, VideoPlay, Grid,
  Picture, ChatDotRound, InfoFilled, View, Document,
  CircleCheckFilled, WarningFilled
} from '@element-plus/icons-vue'
import axios from 'axios'
import { getApiKey, hasApiKey } from '../utils/auth'

// API基础配置
const API_BASE = window.location.origin

// 认证检查
const showAuthDialog = ref(false)

// 检查是否需要认证
if (!hasApiKey()) {
  ElMessage.warning('请先在配置管理页面进行身份认证')
  setTimeout(() => {
    window.location.href = '/#/config'
  }, 2000)
}

// 数据状态
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const models = ref({})
const questionTypeModels = ref({})
const activeTab = ref('models')
const searchQuery = ref('')
const showEnabledOnly = ref(false)

// 对话框状态
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const testDialogVisible = ref(false)
const isEdit = ref(false)
const modelFormRef = ref(null)
const viewingModel = ref(null)

// 表单数据
const modelForm = ref({
  model_id: '',
  name: '',
  provider: 'openai',
  api_protocol: 'openai_compat',
  api_key: '',
  base_url: '',
  model_name: '',
  is_multimodal: false,
  max_tokens: 2000,
  temperature: 0.1,
  top_p: 0.95,
  supports_reasoning: false,
  reasoning_param_name: 'reasoning_effort',
  reasoning_param_value: 'medium',
  enabled: true
})

// 测试相关
const testingModelId = ref('')
const testPrompt = ref('你好，请用一句话介绍你自己')
const testResult = ref(null)

// 表单验证规则
const formRules = {
  model_id: [{ required: true, message: '请输入模型ID', trigger: 'blur' }],
  name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  api_protocol: [{ required: true, message: '请选择API协议', trigger: 'change' }],
  api_key: [{ required: true, message: '请输入API密钥', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入API基础URL', trigger: 'blur' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }]
}

// 题型映射配置
const questionTypeMappings = ref({
  single: { models: [], enable_reasoning: false },
  multiple: { models: [], enable_reasoning: true },
  judgement: { models: [], enable_reasoning: false },
  completion: { models: [], enable_reasoning: false },
  image: { models: [], enable_reasoning: false }
})

// 计算属性
const filteredModels = computed(() => {
  const modelsList = Object.entries(models.value).map(([id, config]) => ({
    id,
    ...config
  }))

  let filtered = modelsList

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(m =>
      m.id.toLowerCase().includes(query) ||
      m.name.toLowerCase().includes(query)
    )
  }

  return filtered
})

const enabledModelsList = computed(() => {
  return Object.entries(models.value)
    .filter(([_, config]) => config.enabled)
    .map(([id, config]) => ({
      id,
      ...config
    }))
})

const sanitizeTypeModels = (type, modelIds) => {
  const ids = Array.isArray(modelIds) ? modelIds : []
  if (type !== 'image') {
    return ids
  }

  return ids.filter(id => {
    const model = models.value[id]
    return model && model.is_multimodal
  })
}

const applySanitizedTypeMappings = (showMessage = false) => {
  let removedCount = 0

  Object.keys(questionTypeMappings.value).forEach(type => {
    const currentModels = Array.isArray(questionTypeMappings.value[type]?.models)
      ? questionTypeMappings.value[type].models
      : []
    const sanitizedModels = sanitizeTypeModels(type, currentModels)
    removedCount += currentModels.length - sanitizedModels.length
    questionTypeMappings.value[type].models = sanitizedModels
  })

  if (showMessage && removedCount > 0) {
    ElMessage.warning('已自动移除图片题中的非多模态模型')
  }
}

// 方法
const loadModels = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/models`, {
      headers: { 'X-API-Key': getApiKey() },
      params: { enabled_only: showEnabledOnly.value }
    })

    if (response.data.success) {
      models.value = response.data.models
      questionTypeModels.value = response.data.question_type_models

      // 初始化映射配置（兼容新旧格式）
      Object.keys(questionTypeMappings.value).forEach(type => {
        const config = questionTypeModels.value[type]
        if (config && typeof config === 'object' && !Array.isArray(config)) {
          // 新格式：{ models: [...], enable_reasoning: true/false }
          questionTypeMappings.value[type].models = config.models || []
          questionTypeMappings.value[type].enable_reasoning = config.enable_reasoning || false
        } else if (Array.isArray(config)) {
          // 旧格式：直接是数组
          questionTypeMappings.value[type].models = config
          questionTypeMappings.value[type].enable_reasoning = false
        } else {
          // 空配置
          questionTypeMappings.value[type].models = []
          questionTypeMappings.value[type].enable_reasoning = false
        }
      })

      applySanitizedTypeMappings(true)
    }
  } catch (error) {
    ElMessage.error('加载模型列表失败: ' + (error.response?.data?.error || error.message))
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  modelForm.value = {
    model_id: '',
    name: '',
    provider: 'openai',
    api_protocol: 'openai_compat',
    api_key: '',
    base_url: '',
    model_name: '',
    is_multimodal: false,
    max_tokens: 2000,
    temperature: 0.1,
    top_p: 0.95,
    supports_reasoning: false,
    reasoning_param_name: 'reasoning_effort',
    reasoning_param_value: 'medium',
    enabled: true
  }
  dialogVisible.value = true
}

const viewModel = (model) => {
  viewingModel.value = model
  viewDialogVisible.value = true
}

const editFromView = () => {
  if (viewingModel.value) {
    viewDialogVisible.value = false
    editModel(viewingModel.value)
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (e) {
    return dateString
  }
}

const editModel = async (model) => {
  try {
    const response = await axios.get(`${API_BASE}/api/models/${model.id}`, {
      headers: { 'X-API-Key': getApiKey() }
    })

    const fullModel = response.data.model
    isEdit.value = true
    modelForm.value = {
      model_id: model.id,
      name: fullModel.name,
      provider: fullModel.provider,
      api_protocol: fullModel.api_protocol || 'openai_compat',
      api_key: fullModel.api_key || '',
      base_url: fullModel.base_url,
      model_name: fullModel.model_name,
      is_multimodal: fullModel.is_multimodal,
      max_tokens: fullModel.max_tokens,
      temperature: fullModel.temperature,
      top_p: fullModel.top_p,
      supports_reasoning: fullModel.supports_reasoning,
      reasoning_param_name: fullModel.reasoning_param_name || 'reasoning_effort',
      reasoning_param_value: fullModel.reasoning_param_value || 'medium',
      enabled: fullModel.enabled
    }
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载模型详情失败: ' + (error.response?.data?.error || error.message))
  }
}

const saveModel = async () => {
  try {
    await modelFormRef.value.validate()

    saving.value = true

    const data = { ...modelForm.value }
    const url = isEdit.value
      ? `${API_BASE}/api/models/${modelForm.value.model_id}`
      : `${API_BASE}/api/models`
    const method = isEdit.value ? 'put' : 'post'

    const response = await axios[method](url, data, {
      headers: {
        'X-API-Key': getApiKey(),
        'Content-Type': 'application/json'
      }
    })

    if (response.data.success) {
      ElMessage.success(response.data.message || '操作成功')
      dialogVisible.value = false
      loadModels()
    } else {
      ElMessage.error(response.data.error || '操作失败')
    }
  } catch (error) {
    if (error.response) {
      ElMessage.error(error.response.data?.error || '操作失败')
    }
  } finally {
    saving.value = false
  }
}

const deleteModel = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型"${model.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await axios.delete(`${API_BASE}/api/models/${model.id}`, {
      headers: { 'X-API-Key': getApiKey() }
    })

    if (response.data.success) {
      ElMessage.success('删除成功')
      loadModels()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.response?.data?.error || error.message))
    }
  }
}

const testModel = (model) => {
  testingModelId.value = model.id
  testResult.value = null
  testDialogVisible.value = true
}

const runTest = async () => {
  testing.value = true
  testResult.value = null

  try {
    const response = await axios.post(
      `${API_BASE}/api/models/test/${testingModelId.value}`,
      { test_prompt: testPrompt.value },
      {
        headers: {
          'X-API-Key': getApiKey(),
          'Content-Type': 'application/json'
        }
      }
    )

    testResult.value = response.data
  } catch (error) {
    testResult.value = {
      success: false,
      error: error.response?.data?.error || error.message
    }
  } finally {
    testing.value = false
  }
}

const saveTypeMapping = async (type) => {
  try {
    questionTypeMappings.value[type].models = sanitizeTypeModels(
      type,
      questionTypeMappings.value[type].models
    )

    const response = await axios.put(
      `${API_BASE}/api/models/question-types/${type}`,
      { 
        model_ids: questionTypeMappings.value[type].models,
        enable_reasoning: questionTypeMappings.value[type].enable_reasoning
      },
      {
        headers: {
          'X-API-Key': getApiKey(),
          'Content-Type': 'application/json'
        }
      }
    )

    if (response.data.success) {
      ElMessage.success(`${getTypeName(type)}配置已保存`)
    }
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.response?.data?.error || error.message))
  }
}

const hasNativeReasoner = (modelIds) => {
  if (!modelIds || modelIds.length === 0) return false
  
  const nativeReasonerCount = modelIds.filter(id => {
    const model = models.value[id]
    return model && model.model_name && model.model_name.toLowerCase().includes('reasoner')
  }).length
  
  const totalCount = modelIds.length
  
  // 只有当所有模型都是原生思考模型时才禁用开关
  return nativeReasonerCount > 0 && nativeReasonerCount === totalCount
}

const canEnableReasoning = (modelIds) => {
  if (!modelIds || modelIds.length === 0) return false
  
  // 检查是否有任何模型支持思考
  return modelIds.some(id => {
    const model = models.value[id]
    return model && (
      model.supports_reasoning || 
      (model.model_name && model.model_name.toLowerCase().includes('reasoner'))
    )
  })
}

const getTypeName = (type) => {
  const names = {
    single: '单选题',
    multiple: '多选题',
    judgement: '判断题',
    completion: '填空题',
    image: '图片题'
  }
  return names[type] || type
}

const getTypeTip = (type) => {
  const tips = {
    single: '优先使用成本较低的模型',
    multiple: '建议使用支持思考模式的模型',
    judgement: '简单题型，使用基础模型即可',
    completion: '根据填空复杂度选择合适的模型',
    image: '必须使用支持多模态的模型'
  }
  return tips[type] || ''
}

// 生命周期
onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.model-manager {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.models-card {
  margin-top: 20px;
}

.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.type-mapping {
  margin-bottom: 30px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.dark .type-mapping {
  background: #262727;
}

.type-mapping h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}

.dark .type-mapping h3 {
  color: #e5eaf3;
}

.mapping-tip {
  margin-top: 10px;
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 5px;
}

.dark .mapping-tip {
  color: #a8abb2;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.collapse-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dark .form-tip {
  color: #a8abb2;
}

.el-alert p {
  margin: 8px 0;
}

.el-alert p:first-child {
  margin-top: 0;
}

.el-alert p:last-child {
  margin-bottom: 0;
}

.el-alert ul {
  margin: 5px 0;
  padding-left: 20px;
}

.el-alert li {
  margin: 4px 0;
  line-height: 1.5;
}

.el-alert code {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.dark .el-alert code {
  background: rgba(255, 255, 255, 0.1);
}

.test-result {
  margin-top: 20px;
}

.model-detail {
  max-height: 600px;
  overflow-y: auto;
}

.model-detail :deep(.el-descriptions__label) {
  font-weight: 500;
  background: #f5f7fa;
}

.dark .model-detail :deep(.el-descriptions__label) {
  background: #262727;
}

.model-detail :deep(.el-descriptions__content) {
  word-break: break-all;
}
</style>
