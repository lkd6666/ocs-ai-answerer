<template>
  <div class="data-viewer">
    <el-card class="header-card">
      <div class="page-title">
        <el-icon class="page-title__icon"><DataAnalysis /></el-icon>
        <h1>答题记录可视化</h1>
      </div>
    </el-card>

    <!-- 控制按钮 -->
    <el-card class="controls-card">
      <el-space wrap>
        <el-button type="primary" @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button type="success" @click="exportData">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
        <el-button type="danger" @click="clearData">
          <el-icon><Delete /></el-icon>
          清空数据
        </el-button>
      </el-space>
    </el-card>

    <!-- 筛选栏 -->
    <el-card class="filter-card" v-if="allData.length > 0">
      <el-space wrap>
        <el-input
          v-model="searchText"
          :prefix-icon="Search"
          placeholder="搜索题目、答案..."
          style="width: 300px"
          clearable
          @input="filterData"
        />
        <el-select v-model="typeFilter" placeholder="所有题型" style="width: 150px" @change="filterData" clearable>
          <el-option label="所有题型" value="" />
          <el-option label="单选题" value="单选题" />
          <el-option label="多选题" value="多选题" />
          <el-option label="判断题" value="判断题" />
          <el-option label="填空题" value="填空题" />
        </el-select>
        <el-select v-model="reasoningFilter" placeholder="所有模式" style="width: 150px" @change="filterData" clearable>
          <el-option label="所有模式" value="" />
          <el-option label="思考模式" value="是" />
          <el-option label="普通模式" value="否" />
        </el-select>
        <el-select v-model="dateFilter" placeholder="全部日期" style="width: 150px" @change="onDateFilterChange">
          <el-option label="全部日期" value="all" />
          <el-option label="今天" value="today" />
          <el-option label="近7天" value="7" />
          <el-option label="近30天" value="30" />
          <el-option label="指定日期" value="custom" />
        </el-select>
        <el-date-picker
          v-if="dateFilter === 'custom'"
          v-model="customDate"
          type="date"
          placeholder="选择日期"
          style="width: 180px"
          @change="filterData"
        />
      </el-space>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row" v-if="stats.total > 0">
      <el-col :xs="12" :sm="8" :md="6">
        <el-card shadow="hover" class="stat-card stat-card-total">
          <el-statistic title="总答题数" :value="stats.total" suffix="题" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card shadow="hover" class="stat-card stat-card-time">
          <el-statistic title="平均AI耗时" :value="stats.avgTime" :precision="2" suffix="秒" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card shadow="hover" class="stat-card stat-card-reasoning">
          <el-statistic title="思考模式答题" :value="stats.reasoningCount" suffix="题" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card shadow="hover" class="stat-card stat-card-totaltime">
          <el-statistic title="总耗时" :value="stats.totalTime" :precision="1" suffix="分钟" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card shadow="hover" class="stat-card stat-card-cost">
          <el-statistic title="总费用" :value="stats.totalCost" :precision="4" prefix="¥" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card shadow="hover" class="stat-card stat-card-tokens">
          <el-statistic title="总Token数" :value="stats.totalTokens" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card shadow="hover" class="stat-card stat-card-input">
          <el-statistic title="输入Token" :value="stats.inputTokens" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6">
        <el-card shadow="hover" class="stat-card stat-card-output">
          <el-statistic title="输出Token" :value="stats.outputTokens" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16" class="charts-row" v-if="stats.total > 0">
      <el-col :xs="24" :sm="12">
        <el-card shadow="hover" class="chart-card">
          <template #header><h3>题型分布</h3></template>
          <div class="chart-container">
            <canvas ref="typeChartCanvas"></canvas>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card shadow="hover" class="chart-card">
          <template #header><h3>答题耗时分布</h3></template>
          <div class="chart-container">
            <canvas ref="timeChartCanvas"></canvas>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card shadow="hover" class="chart-card">
          <template #header><h3>思考模式使用情况</h3></template>
          <div class="chart-container">
            <canvas ref="reasoningChartCanvas"></canvas>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card shadow="hover" class="chart-card">
          <template #header><h3>每日答题量</h3></template>
          <div class="chart-container">
            <canvas ref="dailyChartCanvas"></canvas>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-card class="table-card" v-if="stats.total > 0">
      <el-table :data="paginatedData" stripe style="width: 100%" @row-click="showDetailDialog">
        <el-table-column prop="时间戳" label="时间戳" width="160" />
        <el-table-column prop="题型" label="题型" width="100">
          <template #default="scope">
            <el-tag :type="getTypeTagColor(scope.row.题型)" size="small">
              {{ scope.row.题型 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="题目" label="题目" min-width="200" show-overflow-tooltip class-name="question-cell" />
        <el-table-column prop="选项" label="选项" width="150" show-overflow-tooltip />
        <el-table-column prop="原始回答" label="原始回答" width="150" show-overflow-tooltip />
        <el-table-column prop="思考过程" label="思考过程" width="150" show-overflow-tooltip />
        <el-table-column prop="处理后答案" label="处理后答案" width="150" />
        <el-table-column prop="AI耗时(秒)" label="AI耗时" width="100">
          <template #default="scope">{{ scope.row['AI耗时(秒)'] }}秒</template>
        </el-table-column>
        <el-table-column prop="总耗时(秒)" label="总耗时" width="100">
          <template #default="scope">{{ scope.row['总耗时(秒)'] }}秒</template>
        </el-table-column>
        <el-table-column prop="模型" label="模型" width="150" />
        <el-table-column prop="思考模式" label="思考模式" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.思考模式 === '是'" type="danger" size="small">是</el-tag>
            <el-tag v-else type="info" size="small">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="输入Token" label="输入Token" width="110" />
        <el-table-column prop="输出Token" label="输出Token" width="110" />
        <el-table-column prop="总Token" label="总Token" width="100" />
        <el-table-column prop="费用(元)" label="费用(元)" width="120">
          <template #default="scope">
            <span style="color: #f56c6c; font-weight: bold;" v-if="parseFloat(scope.row['费用(元)'] || 0) > 0">
              ¥{{ parseFloat(scope.row['费用(元)']).toFixed(6) }}
            </span>
            <span v-else style="color: #999;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="提供商" label="提供商" width="120" />
      </el-table>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalRecords"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; justify-content: center;"
      />
    </el-card>

    <!-- 空状态 -->
    <el-empty v-if="allData.length === 0" description="请加载CSV文件开始查看数据" :image-size="200" />

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" width="800px" top="5vh">
      <template #header>
        <div class="dialog-title">
          <el-icon><Tickets /></el-icon>
          <span>题目详情</span>
        </div>
      </template>
      <div v-if="currentDetail" class="detail-content">
        <div class="detail-item">
          <div class="detail-label">时间戳</div>
          <div class="detail-value">{{ currentDetail.时间戳 }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">题型</div>
          <div class="detail-value">
            <el-tag :type="getTypeTagColor(currentDetail.题型)" size="small">
              {{ currentDetail.题型 }}
            </el-tag>
          </div>
        </div>
        <div class="detail-item">
          <div class="detail-label">题目</div>
          <div class="detail-value">{{ currentDetail.题目 || '无' }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">选项</div>
          <div class="detail-value">{{ currentDetail.选项 || '无选项' }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">原始回答</div>
          <div class="detail-value">{{ currentDetail.原始回答 || '无' }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">思考过程</div>
          <div class="detail-value">{{ currentDetail.思考过程 || '无思考过程' }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">处理后答案</div>
          <div class="detail-value">{{ currentDetail.处理后答案 || '无' }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">AI耗时</div>
          <div class="detail-value">{{ currentDetail['AI耗时(秒)'] }}秒</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">总耗时</div>
          <div class="detail-value">{{ currentDetail['总耗时(秒)'] }}秒</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">模型</div>
          <div class="detail-value">{{ currentDetail.模型 || '未知' }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">思考模式</div>
          <div class="detail-value">
            <el-tag v-if="currentDetail.思考模式 === '是'" type="danger" size="small">是</el-tag>
            <el-tag v-else type="info" size="small">否</el-tag>
          </div>
        </div>
        <div class="detail-item">
          <div class="detail-label">Token信息</div>
          <div class="detail-value">
            输入: {{ currentDetail.输入Token }} / 输出: {{ currentDetail.输出Token }} / 总计: {{ currentDetail.总Token }}
          </div>
        </div>
        <div class="detail-item">
          <div class="detail-label">费用</div>
          <div class="detail-value" style="color: #f56c6c; font-weight: bold;">
            {{ parseFloat(currentDetail['费用(元)'] || 0) > 0 ? '¥' + parseFloat(currentDetail['费用(元)']).toFixed(6) : '-' }}
          </div>
        </div>
        <div class="detail-item">
          <div class="detail-label">提供商</div>
          <div class="detail-value">{{ currentDetail.提供商 || '-' }}</div>
        </div>
      </div>
    </el-dialog>
    
    <!-- 认证对话框（可选认证，可以关闭） -->
    <AuthDialog v-model="showAuthDialog" :closable="true" @success="onAuthSuccess" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, Delete, Download, Refresh, Search, Tickets } from '@element-plus/icons-vue'
import axiosInstance from '../utils/axios'
import { hasApiKey } from '../utils/auth'
import AuthDialog from './AuthDialog.vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

// 使用认证的axios实例
const axios = axiosInstance

const loading = ref(false)
const showAuthDialog = ref(false)
const typeChartCanvas = ref(null)
const timeChartCanvas = ref(null)
const reasoningChartCanvas = ref(null)
const dailyChartCanvas = ref(null)

let typeChart = null
let timeChart = null
let reasoningChart = null
let dailyChart = null

const allData = ref([])  // 不再使用，保留用于兼容性
const filteredData = ref([])  // 不再使用，保留用于兼容性
const tableData = ref([])  // 当前页表格数据
const currentPage = ref(1)
const pageSize = ref(20)
const totalRecords = ref(0)  // 总记录数

// 图表数据
const chartData = ref({
  typeCounts: {},
  timeRanges: {},
  reasoningCounts: {},
  dailyCounts: {}
})

// 筛选条件
const searchText = ref('')
const typeFilter = ref('')
const reasoningFilter = ref('')
const dateFilter = ref('all')
const customDate = ref(null)

// 详情对话框
const detailDialogVisible = ref(false)
const currentDetail = ref(null)

const stats = reactive({
  total: 0,
  avgTime: 0,
  reasoningCount: 0,
  totalTime: 0,
  totalCost: 0,
  totalTokens: 0,
  inputTokens: 0,
  outputTokens: 0
})

// 解析CSV（支持多行字段和引号内的逗号）
const parseCSV = (text) => {
  // 先读取表头
  const firstLineEnd = text.indexOf('\n')
  if (firstLineEnd === -1) {
    return []
  }
  
  const headerLine = text.substring(0, firstLineEnd)
  const headers = parseCSVLine(headerLine).map(h => h.trim())
  
  if (headers.length === 0) {
    return []
  }
  
  const csvData = []
  
  // 解析数据行（需要考虑引号内的换行符）
  let rest = text.substring(firstLineEnd + 1)
  let currentLine = ''
  let inQuotes = false
  
  for (let i = 0; i < rest.length; i++) {
    const char = rest[i]
    const nextChar = rest[i + 1]
    
    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        // 转义的引号
        currentLine += '"'
        i++
      } else {
        // 切换引号状态
        inQuotes = !inQuotes
        currentLine += char
      }
    } else if (char === '\n' && !inQuotes) {
      // 真正的行结束（不在引号内）
      if (currentLine.trim()) {
        const values = parseCSVLine(currentLine)
        if (values.length > 0) {
          const row = {}
          headers.forEach((header, index) => {
            row[header] = (values[index] || '').trim()
          })
          csvData.push(row)
        }
      }
      currentLine = ''
    } else {
      currentLine += char
    }
  }
  
  // 处理最后一行（如果文件末尾没有换行符）
  if (currentLine.trim()) {
    const values = parseCSVLine(currentLine)
    if (values.length > 0) {
      const row = {}
      headers.forEach((header, index) => {
        row[header] = (values[index] || '').trim()
      })
      csvData.push(row)
    }
  }

  if (csvData.length === 0) {
    return []
  }

  // 按时间戳降序排列（最新的在前面）
  csvData.sort((a, b) => {
    const dateA = new Date(a['时间戳'] || '')
    const dateB = new Date(b['时间戳'] || '')
    return dateB - dateA  // 降序
  })

  return csvData
}

// 解析CSV行（处理引号内的逗号和换行符）
const parseCSVLine = (line) => {
  const result = []
  let current = ''
  let inQuotes = false
  
  // 处理转义的引号（双引号转义）
  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    const nextChar = line[i + 1]
    
    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        // 转义的引号（双引号）
        current += '"'
        i++ // 跳过下一个引号
      } else {
        // 开始或结束引号
        inQuotes = !inQuotes
      }
    } else if (char === ',' && !inQuotes) {
      // 字段分隔符（不在引号内）
      result.push(current)
      current = ''
    } else {
      current += char
    }
  }
  // 添加最后一个字段
  result.push(current)
  return result
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // 并行加载统计数据和第一页数据
    await Promise.all([
      loadStatsData(),
      loadPageData()
    ])
    
    ElMessage.success(`数据加载成功`)
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStatsData = async () => {
  try {
    // 构建筛选参数
    const params = {}
    
    if (searchText.value) {
      params.search = searchText.value
    }
    if (typeFilter.value) {
      params.type = typeFilter.value
    }
    if (reasoningFilter.value) {
      params.reasoning = reasoningFilter.value
    }
    if (dateFilter.value && dateFilter.value !== 'all') {
      params.date = dateFilter.value
      if (dateFilter.value === 'custom' && customDate.value) {
        params.custom_date = customDate.value
      }
    }
    
    // 调用统计API
    const response = await axios.get('/api/csv/stats', { params })
    
    if (response.data) {
      // 更新统计数据
      stats.total = response.data.total || 0
      stats.avgTime = response.data.avgTime || 0
      stats.reasoningCount = response.data.reasoningCount || 0
      stats.totalTime = response.data.totalTime || 0
      stats.totalCost = response.data.totalCost || 0
      stats.totalTokens = response.data.totalTokens || 0
      stats.inputTokens = response.data.inputTokens || 0
      stats.outputTokens = response.data.outputTokens || 0
      
      // 更新图表数据
      chartData.value = {
        typeCounts: response.data.typeCounts || {},
        timeRanges: response.data.timeRanges || {},
        reasoningCounts: response.data.reasoningCounts || {},
        dailyCounts: response.data.dailyCounts || {}
      }
      
      // 更新图表
      nextTick(() => {
        updateCharts()
      })
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败: ' + error.message)
  }
}

// 加载分页数据（真正的后端分页）
const loadPageData = async () => {
  try {
    // 构建筛选参数
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    // 添加筛选条件
    if (searchText.value) {
      params.search = searchText.value
    }
    if (typeFilter.value) {
      params.type = typeFilter.value
    }
    if (reasoningFilter.value) {
      params.reasoning = reasoningFilter.value
    }
    if (dateFilter.value && dateFilter.value !== 'all') {
      params.date = dateFilter.value
      if (dateFilter.value === 'custom' && customDate.value) {
        params.custom_date = customDate.value
      }
    }
    
    // 调用后端分页API
    const response = await axios.get('/api/csv', { params })
    
    if (response.data.data) {
      // 后端返回的已经是JSON数组，直接使用
      tableData.value = response.data.data
      totalRecords.value = response.data.total
    }
  } catch (error) {
    console.error('加载分页数据失败:', error)
    ElMessage.error('加载分页数据失败: ' + error.message)
  }
}

// 筛选数据（触发重新加载统计和分页数据）
const filterData = () => {
  currentPage.value = 1
  // 重新加载统计数据和第一页数据
  loadStatsData()
  loadPageData()
}

// 日期筛选变化
const onDateFilterChange = () => {
  filterData()
}

// 更新统计信息（已废弃，使用后端统计API）
const updateStats = () => {
  // 不再需要，统计数据从后端获取
}

// 更新所有图表
const updateCharts = () => {
  updateTypeChart()
  updateTimeChart()
  updateReasoningChart()
  updateDailyChart()
}

// 题型分布图
const updateTypeChart = () => {
  if (!typeChartCanvas.value) return
  
  if (typeChart) {
    typeChart.destroy()
  }
  
  const typeCounts = chartData.value.typeCounts || {}
  
  const ctx = typeChartCanvas.value.getContext('2d')
  typeChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: Object.keys(typeCounts),
      datasets: [{
        data: Object.values(typeCounts),
        backgroundColor: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  })
}

// 答题耗时分布图
const updateTimeChart = () => {
  if (!timeChartCanvas.value) return
  
  if (timeChart) {
    timeChart.destroy()
  }
  
  const timeRanges = chartData.value.timeRanges || {}
  
  const ctx = timeChartCanvas.value.getContext('2d')
  timeChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Object.keys(timeRanges),
      datasets: [{
        label: '题目数量',
        data: Object.values(timeRanges),
        backgroundColor: '#409EFF'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  })
}

// 思考模式使用情况图
const updateReasoningChart = () => {
  if (!reasoningChartCanvas.value) return
  
  if (reasoningChart) {
    reasoningChart.destroy()
  }
  
  const reasoningCounts = chartData.value.reasoningCounts || {}
  
  const ctx = reasoningChartCanvas.value.getContext('2d')
  reasoningChart = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: Object.keys(reasoningCounts),
      datasets: [{
        data: Object.values(reasoningCounts),
        backgroundColor: ['#E6A23C', '#409EFF']
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  })
}

// 每日答题量图
const updateDailyChart = () => {
  if (!dailyChartCanvas.value) return
  
  if (dailyChart) {
    dailyChart.destroy()
  }
  
  const dailyCounts = chartData.value.dailyCounts || {}
  const sortedDates = Object.keys(dailyCounts).sort()
  
  const ctx = dailyChartCanvas.value.getContext('2d')
  dailyChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: sortedDates,
      datasets: [{
        label: '答题数量',
        data: sortedDates.map(date => dailyCounts[date]),
        borderColor: '#409EFF',
        backgroundColor: 'rgba(64, 158, 255, 0.1)',
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  })
}

// 分页数据
const paginatedData = computed(() => {
  // 直接返回 tableData，因为已经是分页后的数据
  return tableData.value
})

const handleSizeChange = (val) => {
  pageSize.value = val
  loadPageData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadPageData()
}

// 获取题型标签颜色
const getTypeTagColor = (type) => {
  const colors = {
    '单选题': 'primary',
    '多选题': 'success',
    '判断题': 'danger',
    '填空题': 'warning'
  }
  return colors[type] || 'info'
}

// 显示详情对话框
const showDetailDialog = (row) => {
  currentDetail.value = row
  detailDialogVisible.value = true
}

// 导出数据 - 导出JSON格式数据并转换为CSV
const exportData = async () => {
  if (stats.total === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }
  
  try {
    // 构建过滤参数
    const params = {
      export: 'true'  // 导出全部数据
    }
    if (searchText.value) params.search = searchText.value
    if (typeFilter.value) params.type = typeFilter.value
    if (reasoningFilter.value) params.reasoning = reasoningFilter.value
    if (dateFilter.value && dateFilter.value !== 'all') {
      params.date = dateFilter.value
      if (dateFilter.value === 'custom' && customDate.value) {
        params.custom_date = customDate.value
      }
    }
    
    // 获取数据
    const response = await axios.get('/api/csv', { params })
    const data = response.data.data
    
    if (!data || data.length === 0) {
      ElMessage.warning('没有数据可导出')
      return
    }
    
    // 转换为CSV格式
    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join(','),
      ...data.map(row => 
        headers.map(header => {
          const value = (row[header] || '').toString()
          // CSV转义：双引号包裹，内部双引号加倍
          return `"${value.replace(/"/g, '""')}"`
        }).join(',')
      )
    ].join('\n')
    
    // 下载文件
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `ocs_answers_export_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败: ' + error.message)
  }
}

// 清空数据
const clearData = () => {
  if (stats.total === 0) {
    ElMessage.warning('当前没有数据可清空')
    return
  }
  
  // 检查是否有密钥
  if (!hasApiKey()) {
    ElMessage.warning('此操作需要访问密钥，请先登录')
    showAuthDialog.value = true
    return
  }
  
  const totalCount = stats.total
  ElMessageBox.confirm(
    `确定要清空CSV文件吗？\n\n当前共有 ${totalCount} 条记录\n\n此操作将清空CSV文件中的所有数据（保留表头），此操作不可恢复！`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const response = await axios.post('/api/csv/clear')
      if (response.data.success) {
        // 重新加载数据
        await loadData()
        ElMessage.success('CSV文件已清空')
      } else {
        ElMessage.error('清空失败: ' + (response.data.error || '未知错误'))
      }
    } catch (error) {
      console.error('清空CSV失败:', error)
      ElMessage.error('清空失败: ' + error.message)
    }
  }).catch(() => {})
}

// 认证成功处理
const onAuthSuccess = (apiKey) => {
  console.log('认证成功')
  // 认证成功后不需要特殊操作，因为axios拦截器会自动添加密钥
}

// 监听全局认证事件（仅在需要认证的操作失败时触发）
const handleAuthRequired = () => {
  showAuthDialog.value = true
}

onMounted(() => {
  // 直接加载数据，不检查密钥
  // 查看数据不需要认证，只有清空数据等操作才需要
  loadData()
  
  // 监听认证事件（当执行需要认证的操作时会触发）
  window.addEventListener('auth-required', handleAuthRequired)
})

onUnmounted(() => {
  if (typeChart) typeChart.destroy()
  if (timeChart) timeChart.destroy()
  if (reasoningChart) reasoningChart.destroy()
  if (dailyChart) dailyChart.destroy()
  
  // 移除事件监听
  window.removeEventListener('auth-required', handleAuthRequired)
})
</script>

<style scoped>
.data-viewer {
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.header-card h1 {
  margin: 0;
  color: #409eff;
}

.page-title {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.page-title__icon {
  color: #409eff;
  font-size: 28px;
}

.dark .header-card h1 {
  color: #79bbff;
}

.dark .page-title__icon {
  color: #79bbff;
}

.controls-card,
.filter-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-card-total {
  background: linear-gradient(135deg, #409EFF 0%, #66B1FF 100%);
  color: white;
}

.stat-card-time {
  background: linear-gradient(135deg, #409EFF 0%, #66B1FF 100%);
  color: white;
}

.stat-card-reasoning {
  background: linear-gradient(135deg, #67C23A 0%, #85CE61 100%);
  color: white;
}

.stat-card-totaltime {
  background: linear-gradient(135deg, #67C23A 0%, #85CE61 100%);
  color: white;
}

.stat-card-cost {
  background: linear-gradient(135deg, #F56C6C 0%, #F78989 100%);
  color: white;
}

.stat-card-tokens {
  background: linear-gradient(135deg, #909399 0%, #A6A9AD 100%);
  color: white;
}

.stat-card-input {
  background: linear-gradient(135deg, #E6A23C 0%, #EBB563 100%);
  color: white;
}

.stat-card-output {
  background: linear-gradient(135deg, #E6A23C 0%, #EBB563 100%);
  color: white;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card h3 {
  margin: 0;
  text-align: center;
  color: #303133;
}

.chart-container {
  height: 300px;
  padding: 10px;
}

.table-card {
  margin-bottom: 20px;
}

:deep(.question-cell) {
  cursor: pointer;
  color: #409eff;
}

:deep(.question-cell:hover) {
  text-decoration: underline;
}

.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-item {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-value {
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.dialog-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
</style>
