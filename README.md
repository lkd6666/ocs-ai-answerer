# OCS AI Answerer

## OCS智能答题API - 多模型支持版本

<div align="center">

[![GitHub Stars](https://img.shields.io/github/stars/lkd6666/ocs-ai-answerer?style=social)](https://github.com/lkd6666/ocs-ai-answerer/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/lkd6666/ocs-ai-answerer)](https://github.com/lkd6666/ocs-ai-answerer/issues)
[![GitHub License](https://img.shields.io/github/license/lkd6666/ocs-ai-answerer)](https://github.com/lkd6666/ocs-ai-answerer/blob/main/LICENSE)

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![DeepSeek](https://img.shields.io/badge/DeepSeek-AI-orange.svg)
![Doubao](https://img.shields.io/badge/Doubao-AI-purple.svg)
![AI Maintained](https://img.shields.io/badge/Maintained%20by-AI-00D9FF.svg)

一个专为[OCS网课助手](https://docs.ocsjs.com/)设计的智能答题API，支持DeepSeek、豆包等多个大语言模型，提供强大的AI答题能力。

> 📌 **关于 OCS**
> 
> [OCS (Online Course Script)](https://docs.ocsjs.com/) 是一款功能强大的网课助手脚本，支持超星学习通、智慧树、职教云等多个平台。本项目为 OCS 提供 AI 智能答题能力。
> 
> - 🌐 官方网站：https://docs.ocsjs.com/
> - 📦 脚本安装：https://docs.ocsjs.com/docs/work
> - 💬 交流社区：https://docs.ocsjs.com/

---

> 🤖 **AI 驱动开发**
> 
> 本项目由 AI 辅助设计、开发和维护，代表了人工智能在软件工程领域的实践应用。
> 
> - 💡 **智能设计**：AI 参与架构设计和功能规划
> - 🔧 **代码生成**：核心代码由 AI 协助编写和优化
> - 📝 **文档维护**：技术文档由 AI 自动生成和更新
> - 🐛 **问题诊断**：AI 协助分析和修复问题
> 
> 这种开发模式确保了代码质量、快速迭代和持续优化。

---

</div>

## ✨ 特性

### 🎨 全新 Vue3 可视化界面（v3.1）
- **前端技术栈升级**：从纯 HTML 重构为 Vue 3 + Element Plus 现代化架构
- **响应式设计**：完美适配桌面和移动端，流畅的用户体验
- **三大功能模块**：
  - 🏠 **配置管理面板**：可视化配置所有参数，支持保存并重启
  - 📊 **数据可视化页面**：Chart.js 图表、后端分页、实时统计
  - 📋 **API 文档页面**：在线查看完整的 API 接口文档
- **智能导航**：统一的导航栏，页面间自由跳转
- **即时保存**：一键保存配置并自动重启服务器，配置立即生效

### 🔒 企业级安全机制（v3.1）
- **访问密钥认证**：首次启动自动生成 64 位安全密钥
- **SHA256 加密存储**：密钥哈希存储，防止明文泄露
- **IP 限流保护**：失败 5 次锁定 5 分钟，防止暴力破解
- **分级权限控制**：
  - 公开访问：答题接口、数据查看、健康检查
  - 需要认证：配置管理、数据清空、服务器重启
- **前端安全**：LocalStorage 密钥管理、axios 自动注入、统一拦截

### 🎨 Web 配置界面增强（v2.2）
- **可视化配置管理**：通过浏览器图形界面管理所有配置，无需手动编辑文件
- **实时状态监控**：查看服务状态、当前模型、思考模式等实时信息
- **快速导航中心**：一键跳转到答题记录、API文档等功能页面
- **配置预览导出**：实时预览配置、导出.env文件、重置默认值
- **保存并重启**：一键保存配置并自动重启服务器，自动轮询检测重启状态

### 🤖 AI驱动
- **多模型支持**：DeepSeek V4 Flash、DeepSeek V4 Pro、豆包 (Doubao) 以及 OpenAI 兼容模型
- **模型管理器唯一配置源**：答题运行时统一从模型管理页读取模型、题型映射与启用状态
- **内置预设**：首次启动默认提供 3 个内置预设，可编辑、可删除、可测试
- **题型思考开关**：在 Web 管理台为不同题型分别配置是否启用深度思考
- **原生思考模型**：自动识别 Reasoner 模型，强制启用深度推理并提示混合模式行为
- **多选题智能**：多选题自动启用深度思考，提高准确率
- **图片题智能**：带图片题目自动启用深度思考，提高识别准确率
- **智能理解**：强大的自然语言理解能力

### 🎯 题型支持
- ✅ 单选题（Single Choice）
- ✅ 多选题（Multiple Choice） - 自动深度思考
- ✅ 判断题（True/False）
- ✅ 填空题（Completion）

### 🖼️ 多模态支持
- **图片识别**：支持豆包及 OpenAI 兼容多模态模型的图片+文本混合输入
- **自动提取**：从题干和选项中自动提取图片URL
- **图文混排**：按题干/选项中的原始出现顺序把图片插回请求消息，避免顺序错乱
- **智能思考**：带图片题目可自动启用深度思考模式
- **智能降级**：图片访问失败时自动切换纯文本模式

### 📊 数据记录
- **CSV日志**：记录每道题的详细信息（题目、选项、答案、思考过程、耗时等）
- **可视化界面**：Vue3 + Element Plus 现代化界面，图表展示答题数据
- **后端分页**：支持大数据量，搜索、筛选、排序功能
- **实时统计**：题型分布、思考模式使用、平均耗时、费用统计
- **数据导出**：支持 CSV 格式导出，数据清空需要密钥认证

### 🔧 其他特性
- 📝 **精准Prompt**：针对不同题型优化的提示词工程
- 🔄 **智能清洗**：答案格式化和匹配优化
- 🚀 **即插即用**：完美对接OCS脚本题库配置
- 🔁 **重试机制**：网络错误自动重试，支持代理配置
- 🔁 **模型故障转移**：同一题型配置多模型时自动降级，确保答题不中断
- ⚙️ **灵活配置**：所有参数通过环境变量或 Web 界面配置
- 🧪 **题型测试脚本**：`test_question.py` 支持一键模拟不同题型，验证模型与思考策略
- 🏷️ **标签展示**：在OCS中显示AI、深度思考、模型等标签
- 🔄 **一键重启**：保存配置并自动重启，智能轮询检测服务状态
- 🔒 **安全保护**：访问密钥、IP限流、SHA256加密

## 📋 目录

- [快速开始](#快速开始)
- [安装步骤](#安装步骤)
- [配置说明](#配置说明)
- [配置OCS脚本](#配置ocs脚本)
- [API文档](#api文档)
- [功能介绍](#功能介绍)
- [常见问题](#常见问题)
- [功能规划](#功能规划)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

#### 🌟 方式一：使用Web配置面板（推荐）

**最简单的方式，无需手动编辑文件！**

1. **启动服务**
   ```bash
   # Windows
   start.bat
   
   # Linux/Mac
   ./start.sh
   ```

2. **打开配置面板**
   - 在浏览器中访问：`http://localhost:5000/`
   - 首次使用会看到配置管理界面

3. **在模型管理页配置模型**
   - 点击顶部“模型管理”
   - 编辑内置预设或新增自定义模型
   - 为不同题型设置题型映射；图片题只允许多模态模型
   - OpenAI 官方或兼容推理模型可按需选择 `Responses API` 或 `Chat Completions`
   
4. **调整其他参数**（可选）
   - AI参数：温度、Token限制等
   - 全局兼容思考策略：默认思考强度、自动思考开关
   - 网络设置：代理、超时时间
   
5. **保存配置**
   - 点击页面底部“保存配置”按钮
   - 重启服务以应用新配置

> 💡 **提示**：
> - 通用运行参数会保存到 `.env`
> - 模型、题型映射与内置预设状态会保存到 `custom_models.json`
> - `.env` 中旧的 `MODEL_PROVIDER / PREFER_MODEL / IMAGE_MODEL / DEEPSEEK_* / DOUBAO_*` 仅用于首次迁移，不再作为答题运行时来源

#### 方式二：手动编辑配置文件

如果你更喜欢传统方式，也可以手动编辑：

复制 `env.template` 为 `.env` 并编辑：

```bash
# Windows
copy env.template .env

# Linux/Mac
cp env.template .env
```

### 🔑 获取API密钥

#### DeepSeek（推荐，性价比高）

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入 [API密钥页面](https://platform.deepseek.com/api_keys)
4. 点击"创建API密钥"
5. 复制生成的密钥（格式：`sk-xxxxxx...`）
6. 在“模型管理”页面编辑 `DeepSeek V4 Flash` / `DeepSeek V4 Pro` 预设并填入 API Key

#### 豆包（可选，支持图片）

1. 访问 [火山引擎控制台](https://console.volcengine.com/ark)
2. 注册/登录账号
3. 开通"豆包大模型"服务
4. 创建推理接入点，获取：
   - API密钥
   - 接入点ID（模型名）
5. 在“模型管理”页面编辑 `Doubao` 预设并填入 API Key / 模型名

### 📝 编辑配置文件

编辑 `.env` 文件，填写通用运行参数：

```env
# 思考兼容策略
ENABLE_REASONING=false
AUTO_REASONING_FOR_MULTIPLE=true  # 多选题自动启用
AUTO_REASONING_FOR_IMAGES=true    # 图片题自动启用（推荐）

# AI通用参数
TEMPERATURE=0.1
MAX_TOKENS=500
REASONING_MAX_TOKENS=4096
TOP_P=0.95

# 网络与服务参数
TIMEOUT=1200
MAX_RETRIES=3
PORT=5000
```

> 模型 API Key、Base URL、模型名、多模态能力、协议类型等请在“模型管理”页面维护，而不是继续依赖 `.env`。


### 3. 启动服务

```bash
python ocs_ai_answerer_advanced.py
```

看到以下输出表示启动成功：

```
╔═══════════════════════════════════════════════════════════╗
║       OCS智能答题API服务 - 多模型支持版本 v3.1          ║
╠═══════════════════════════════════════════════════════════╣
║  🏠 配置面板: http://0.0.0.0:5000/                      
║  📊 答题记录: http://0.0.0.0:5000/viewer                
║  📋 API文档: http://0.0.0.0:5000/docs                   
╠═══════════════════════════════════════════════════════════╣
║  接口地址: http://localhost:5000/api/answer              
║  健康检查: http://localhost:5000/api/health              
║  配置查询: http://localhost:5000/api/config              
║  CSV数据: http://localhost:5000/api/csv                  
║  延迟测试: http://localhost:5000/?t=时间戳               
╠═══════════════════════════════════════════════════════════╣
║  当前模式: 已配置模型 3 个 / 已启用 3 个                  ║
║    可答题型: single、multiple、judgement、completion     ║
║  思考模式: ❌ 未启用                                      ║
║  多选题思考: ✅ 自动启用                                  ║
║  图片题思考: ✅ 自动启用                                  ║
║  支持题型: 单选、多选、判断、填空                        ║
╠═══════════════════════════════════════════════════════════╣
║  💡 旧版HTML: http://0.0.0.0:5000/config_legacy          ║
╚═══════════════════════════════════════════════════════════╝

✅ 服务启动成功！
```

> ⚠️ **重要提示**：首次启动会自动生成访问密钥，请立即复制保存。配置管理、数据清空、重启服务等敏感操作都需要此密钥。

### 🎨 访问Web界面

服务启动后，可以访问以下页面：

#### 首次使用（需要访问密钥）
1. **获取访问密钥**：从服务器启动日志中复制 64 位密钥
2. **访问首页**：`http://localhost:5000/`
3. **输入访问密钥**：粘贴密钥进行验证
4. **配置模型**：进入“模型管理”页，填写预设或自定义模型的 API Key / Base URL / 模型名 / 协议类型
5. **保存并重启**：点击"保存并重启"按钮，系统自动重启并应用配置

#### 功能页面
- **🏠 首页/配置面板**：`http://localhost:5000/` - 管理通用配置（需要密钥）
- **🧩 模型管理**：`http://localhost:5000/models` - 管理模型、题型映射、思考开关（需要密钥）
- **📊 答题记录查看**：`http://localhost:5000/viewer` - 查看答题统计和图表（无需密钥）
- **📋 API 文档页面**：`http://localhost:5000/docs` - 查看完整 API 文档（无需密钥）

#### 安全说明
- ✅ **公开访问**：答题接口、数据查看、API 文档、健康检查
- 🔒 **需要密钥**：配置管理、数据清空、服务器重启、密钥修改

> 💡 **提示**：访问密钥会自动保存在浏览器 LocalStorage 中，无需每次输入

### 4. 配置OCS脚本

#### 方式一：安装OCS脚本（推荐）

如果还未安装 OCS 脚本，请先安装：

1. **安装脚本管理器**（推荐脚本猫）
   - Chrome/Edge：安装 [脚本猫(ScriptCat)](https://scriptcat.org/) 或 [Tampermonkey](https://www.tampermonkey.net/)
   - Firefox：安装 [脚本猫](https://scriptcat.org/) 或 [Tampermonkey](https://addons.mozilla.org/firefox/addon/tampermonkey/)
   - Safari：安装 [Userscripts](https://apps.apple.com/app/userscripts/id1463298887)
   
   > 💡 **推荐使用脚本猫**：国内开发，速度快，功能强大，更适合国内网络环境

2. **安装 OCS 脚本**
   - 访问 [OCS 官网](https://docs.ocsjs.com/docs/work)
   - 或直接在脚本管理器中添加本项目的 `ocs.user.js` 文件（包含标签兼容性优化）

3. **配置题库**
   - 在OCS脚本的"通用-全局设置-题库配置"中
   - 导入 `ocs_config.json` 文件

> 💡 **推荐使用项目提供的 `ocs.user.js`**
> 
> 本项目的 `ocs.user.js` 已针对 AI 答题功能进行优化，包含：
> - ✅ 支持 `purple` 和 `orange` 标签颜色（深度思考、自动思考标识）
> - ✅ 更好的 AI 答题标签显示
> - ✅ 完整的题库超时配置（3分钟）
> 
> **安装方法：**
> 1. 打开脚本管理器（脚本猫或Tampermonkey）
> 2. 点击"添加新脚本"或"新建脚本"
> 3. 将 `ocs.user.js` 的内容粘贴进去
> 4. 保存并启用
> 
> 或者直接从文件安装：
> 1. 下载项目中的 `ocs.user.js` 文件
> 2. 在脚本管理器中选择"从本地安装"
> 3. 选择下载的 `ocs.user.js` 文件

#### 方式二：仅配置题库（已安装OCS用户）

如果已经安装了 OCS 脚本，只需导入题库配置即可。

## 📦 安装步骤

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器
- DeepSeek 或 豆包 API密钥

### 详细安装

1. **克隆或下载项目**

```bash
git clone https://github.com/lkd6666/ocs-ai-answerer.git
cd ocs-ai-answerer
```

2. **创建虚拟环境（推荐）**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖包**

```bash
pip install -r requirements.txt
```

依赖包列表（`requirements.txt`）：
```
flask>=3.0.0
flask-cors>=4.0.0
openai>=1.12.0
python-dotenv>=1.0.0
httpx>=0.26.0
requests>=2.31.0
```

4. **配置环境变量**

```bash
# 复制模板
cp env.template .env

# 编辑配置
# Windows: notepad .env
# Linux/Mac: nano .env
```

5. **构建前端（首次使用或更新后）**

```bash
# 进入前端目录
cd frontend

# 安装依赖（首次）
npm install

# 构建生产版本
npm run build

# 返回项目根目录
cd ..
```

> 💡 **提示**：前端构建后会生成 `frontend/dist` 目录，Flask 会自动托管这些静态文件

**前端开发模式**（可选，仅开发时使用）：
```bash
cd frontend
npm run dev  # 启动开发服务器，支持热重载
```

6. **启动后端服务**

```bash
python ocs_ai_answerer_advanced.py
```

### 🏗️ 前端架构说明

#### 技术栈
- **框架**：Vue 3.4.0 (Composition API)
- **UI 库**：Element Plus 2.5.0
- **图表**：Chart.js 4.4.0
- **HTTP 客户端**：Axios 1.6.0
- **构建工具**：Vite 4.5.0

#### 目录结构
```
frontend/
├── src/
│   ├── components/
│   │   ├── ConfigPanel.vue    # 配置管理面板
│   │   ├── DataViewer.vue     # 数据可视化页面
│   │   ├── ApiDocs.vue        # API 文档页面
│   │   └── AuthDialog.vue     # 认证对话框
│   ├── utils/
│   │   ├── auth.js            # 密钥管理工具
│   │   └── axios.js           # HTTP 客户端配置
│   ├── App.vue                # 主应用组件
│   └── main.js                # 入口文件
├── public/                     # 静态资源
├── dist/                       # 构建输出（自动生成）
├── package.json               # 依赖配置
└── vite.config.js            # Vite 配置

```

#### Flask 静态文件托管
后端自动托管前端构建文件：
```python
# ocs_ai_answerer_advanced.py
app = Flask(__name__, 
    static_folder='dist',
    static_url_path='')

@app.route('/')
@app.route('/viewer')
@app.route('/docs')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')
```

### 🎁 打包成EXE（可选）

如需制作便携版exe文件，方便在其他电脑使用：

```bash
# 方法1：使用自动打包脚本（推荐）
python build_exe.py

# 或双击运行（Windows）
build_exe.bat

# 方法2：手动打包
pip install pyinstaller
pyinstaller --onefile --name=OCS-AI-Answerer ocs_ai_answerer_advanced.py
```

打包完成后：
- 可执行文件位置：`dist/OCS-AI-Answerer.exe`
- 详细说明：查看 [BUILD_GUIDE.md](BUILD_GUIDE.md)

## ⚙️ 配置说明

### 🔑 模型与密钥配置

- 所有模型凭据、Base URL、模型名、多模态能力、协议类型统一在“模型管理”页面维护。
- 首次升级时，历史 `.env` 里的 `DEEPSEEK_* / DOUBAO_*` 只会被用来迁移一次到内置预设。
- 升级完成后，答题运行时不再读取 `.env` 中的旧模型字段。

#### 默认内置预设

- `DeepSeek V4 Flash`：默认用于 `single / judgement / completion`
- `DeepSeek V4 Pro`：默认用于 `multiple`，失败时回退到 `DeepSeek V4 Flash`
- `Doubao`：默认用于 `image`

#### OpenAI / 兼容协议支持

- 支持 `openai_compat`、`responses`、`chat_completions`
- OpenAI 官方模型默认可走最新 `Responses API`
- 向后兼容旧的 `Chat Completions` 风格服务

### 环境变量详解

#### 思考模式配置

```env
# 全局启用思考模式（false=普通模式，true=思考模式）
ENABLE_REASONING=false

# 多选题自动启用深度思考（推荐开启）
AUTO_REASONING_FOR_MULTIPLE=true

# 带图片题目自动启用深度思考（推荐开启）
AUTO_REASONING_FOR_IMAGES=true

# 豆包思考强度（low/medium/high）
REASONING_EFFORT=medium
```

**思考模式说明：**
- **普通模式**：快速响应，适合简单题目，使用 `MAX_TOKENS`
- **思考模式**：深度推理，答案更准确但耗时更长，使用 `REASONING_MAX_TOKENS`
- **多选题自动思考**：仅对多选题启用，平衡速度和准确率
- **图片题自动思考**：仅对带图片题目启用，提高图片识别准确率

> 💡 **为什么需要单独配置思考模式的 token？**
> 
> 思考模式（如 deepseek-reasoner）需要输出详细的推理过程，比普通模式需要更多的 token。如果设置太小，可能导致推理过程被截断，影响答案质量。推荐配置：
> - `MAX_TOKENS=500`（普通模式，节省成本）
> - `REASONING_MAX_TOKENS=4096`（思考模式，确保完整推理）

#### AI参数配置

```env
TEMPERATURE=0.1               # 温度参数 (0-2)，越低越稳定
MAX_TOKENS=500               # 普通模式最大输出token数
REASONING_MAX_TOKENS=4096    # 思考模式最大输出token数
TOP_P=0.95                   # 核采样参数
```

**参数详解：**

| 参数 | 范围 | 推荐值 | 作用说明 |
|------|------|--------|----------|
| **TEMPERATURE** | 0.0-2.0 | 0.1 | **控制答案的随机性和创造性**<br>• 0.0-0.3：确定性高，适合答题（推荐）<br>• 0.4-0.7：平衡，适合对话<br>• 0.8-2.0：创造性高，答案多样但可能不准确 |
| **MAX_TOKENS** | 1-8192 | 500 | **普通模式的最大输出长度**<br>• 填空题：200-300 足够<br>• 选择题：300-500 合适<br>• 复杂题目：可增加到 1000+<br>• deepseek-chat 最大：8192 |
| **REASONING_MAX_TOKENS** | 1-65536 | 4096 | **思考模式的最大输出长度**<br>• 简单思考：2000-4000<br>• 中等复杂：4096-8000（推荐）<br>• 复杂推理：8000-16000<br>• 图片题：建议4096+（推荐）<br>• deepseek-reasoner 最大：65536 |
| **TOP_P** | 0.0-1.0 | 0.95 | **核采样，控制词汇选择范围**<br>• 0.9-1.0：词汇丰富，表达多样（推荐）<br>• 0.5-0.8：更保守，重复性增加<br>• 0.1-0.4：非常保守，可能过于机械 |

**答题场景推荐配置：**

```env
# 🎯 追求准确率（推荐）
TEMPERATURE=0.1               # 低温度，减少随机性
MAX_TOKENS=500               # 普通模式输出长度
REASONING_MAX_TOKENS=4096    # 思考模式输出长度
TOP_P=0.95                   # 保持自然表达

# ⚡ 追求速度
TEMPERATURE=0.05             # 更低温度，更快决策
MAX_TOKENS=300              # 限制输出长度
REASONING_MAX_TOKENS=2000   # 思考模式也限制
TOP_P=0.9                   # 略微降低

# 🔬 复杂题目 / 深度思考
TEMPERATURE=0.15             # 略高温度，更多思考
MAX_TOKENS=1000             # 更长的输出空间
REASONING_MAX_TOKENS=8192   # 思考模式大幅增加
TOP_P=0.95                  # 保持多样性

# 🧠 极限推理（适合超难题目）
TEMPERATURE=0.1              # 保持稳定
MAX_TOKENS=1000             
REASONING_MAX_TOKENS=16384  # 给思考模式最大空间
TOP_P=0.95
```

**参数组合效果：**

- **TEMPERATURE ↓ + TOP_P ↑**：准确但自然（最佳）
- **TEMPERATURE ↓ + TOP_P ↓**：准确但机械
- **TEMPERATURE ↑ + TOP_P ↑**：多样但不稳定
- **TEMPERATURE ↑ + TOP_P ↓**：不推荐（容易出错）

#### 网络配置

```env
HTTP_PROXY=             # HTTP代理（可选）
HTTPS_PROXY=            # HTTPS代理（可选）
TIMEOUT=1200.0          # 请求超时时间（秒）
MAX_RETRIES=3           # 最大重试次数
```

#### 服务配置

```env
HOST=0.0.0.0            # 监听地址
PORT=5000               # 监听端口
DEBUG=False             # 调试模式
CSV_LOG_FILE=ocs_answers_log.csv  # CSV日志文件路径
```

## 🔧 配置OCS脚本

### 前置要求

确保已安装 OCS 脚本。如果还没有安装，请参考 [快速开始 - 第4步](#4-配置ocs脚本)。

> 💡 **提示**：推荐使用本项目提供的 `ocs.user.js`，已包含 AI 答题的标签兼容性优化。

### 导入配置文件

1. 打开OCS脚本悬浮窗
2. 进入"通用" → "全局设置"
3. 找到"题库配置"，点击"点击配置"
4. 选择"自定义配置"
5. 将 `ocs_config.json` 的内容粘贴到文本框
6. 点击"解析并保存"

### 配置文件内容（`ocs_config.json`）

```json
{
  "name": "AI智能答题",
  "url": "http://localhost:5000/api/answer",
  "method": "post",
  "type": "fetch",
  "contentType": "json",
  "homepage": "https://github.com/lkd6666/ocs-ai-answerer",
  "headers": {
    "Content-Type": "application/json"
  },
  "data": {
    "question": "${title}",
    "options": {
      "handler": "return (env)=>env.options?.split('\\n')"
    },
    "type": {
      "handler": "return (env)=> env.type === 'single' ? 0 : env.type === 'multiple' ? 1 : env.type === 'completion' ? 3 : env.type === 'judgement' ? 4 : 0"
    },
    "images": {
      "handler": "return (env)=> { const imgPattern = /https?:\\/\\/[^\\s]+\\.(?:jpg|jpeg|png|gif|bmp|webp)/gi; return env.title?.match(imgPattern) || []; }"
    }
  },
  "handler": "return (res)=>res.success && res.ocs_format ? [res.ocs_format] : []"
}
```

### 验证配置

配置成功后，进入任意作业/考试页面，OCS应该显示：

> ✅ 当前有1个可用题库：AI智能答题

### OCS 脚本标签兼容性

如果使用官方原版 OCS 脚本，可能不支持 `purple` 和 `orange` 标签颜色。建议：

1. **使用项目提供的 `ocs.user.js`**（推荐）
   - 已包含所有标签颜色支持
   - 题库超时设置为3分钟
   - 完美兼容 AI 答题功能

2. **或修改现有 OCS 脚本**
   - 在 OCS 脚本中添加以下 CSS（搜索 `.search-result-answer-tag` 部分）：
   ```css
   .search-result-answer-tag.purple {
     background-color: #9b59b6;
     color: white;
   }
   .search-result-answer-tag.orange {
     background-color: #e67e22;
     color: white;
   }
   ```

### 标签说明

使用本项目的 AI 答题时，会显示以下标签：

| 标签 | 颜色 | 说明 |
|------|------|------|
| AI | 🔵 蓝色 | OCS自动添加，表示AI答题 |
| 深度思考 | 🟣 紫色 | 使用思考模式（需兼容脚本）|
| 自动思考 | 🟠 橙色 | 多选题自动启用思考（需兼容脚本）|
| 智能选择 | 🔵 蓝色 | 智能模型选择模式 |
| DEEPSEEK/DOUBAO | 🟢 绿色 | 实际使用的模型 |

## 📚 API文档

### 1. 答题接口

#### 请求

```http
POST /api/answer
Content-Type: application/json

{
  "question": "中国的首都是哪里？",
  "options": ["北京", "上海", "广州", "深圳"],
  "type": 0,
  "images": []
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 题目内容 |
| options | array | 否 | 选项列表（填空题可为空）|
| type | integer | 是 | 题型：0=单选, 1=多选, 3=填空, 4=判断 |
| images | array | 否 | 图片URL列表（仅豆包支持）|

#### 响应

```json
{
  "success": true,
  "question": "中国的首都是哪里？",
  "answer": "北京",
  "type": "single",
  "raw_answer": "北京",
  "model": "deepseek-chat",
  "provider": "deepseek",
  "reasoning_used": false,
  "ai_time": 1.23,
  "total_time": 1.25,
  "ocs_format": [
    "中国的首都是哪里？",
    "北京",
    {
      "ai": true,
      "tags": [
        {"text": "DEEPSEEK", "title": "模型: deepseek-chat", "color": "green"}
      ],
      "model": "deepseek-chat",
      "provider": "deepseek",
      "reasoning_used": false,
      "ai_time": 1.23,
      "total_time": 1.25
    }
  ]
}
```

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| question | string | 题目（回显）|
| answer | string | 处理后的答案 |
| type | string | 题型名称 |
| raw_answer | string | AI原始返回 |
| model | string | 使用的模型 |
| provider | string | 模型提供商 |
| reasoning_used | boolean | 是否使用思考模式 |
| ai_time | float | AI答题耗时（秒）|
| total_time | float | 总处理耗时（秒）|
| ocs_format | array | OCS脚本格式数据 |

### 2. 健康检查接口

```http
GET /api/health

Response:
{
  "status": "ok",
  "service": "OCS AI Answerer (Multi-Model)",
  "version": "3.1.0",
  "reasoning_enabled": false,
  "api_configured": true,
  "model_count": 3,
  "enabled_model_count": 3,
  "ready_question_types": ["single", "multiple", "judgement", "completion", "image"],
  "has_multimodal_model": true,
  "init_error": null
}
```

### 3. 配置管理接口（需要认证）

#### 获取配置
```http
GET /api/config
Headers: X-API-Key: <your-access-key>

Response:
{
  "ENABLE_REASONING": "false",
  "REASONING_EFFORT": "medium",
  "AUTO_REASONING_FOR_MULTIPLE": "true",
  "AUTO_REASONING_FOR_IMAGES": "true",
  "TEMPERATURE": "0.1",
  "MAX_TOKENS": "500",
  "REASONING_MAX_TOKENS": "4096",
  "TOP_P": "0.95",
  "_runtime": {
    "model_count": 3,
    "enabled_model_count": 3,
    "ready_question_types": ["single", "multiple", "judgement", "completion", "image"],
    "mapped_question_types": {
      "single": ["preset_deepseek_v4_flash"],
      "multiple": ["preset_deepseek_v4_pro", "preset_deepseek_v4_flash"],
      "image": ["preset_doubao"]
    },
    "has_multimodal_model": true,
    "can_answer_any": true,
    "init_error": null
  }
}
```

#### 保存配置
```http
POST /api/config
Headers: X-API-Key: <your-access-key>
Content-Type: application/json

{
  "ENABLE_REASONING": "true",
  "TEMPERATURE": "0.15",
  "TIMEOUT": "600",
  "LOG_LEVEL": "INFO"
}

Response:
{
  "success": true,
  "message": "配置已成功保存到 .env 文件",
  "file": "/path/to/.env",
  "note": "请重启服务以应用新配置"
}
```

### 4. 服务器重启接口（需要认证）

```http
POST /api/restart
Headers: X-API-Key: <your-access-key>

Response:
{
  "success": true,
  "message": "服务器将在 1 秒后重启"
}
```

### 5. 认证相关接口

#### 验证密钥
```http
POST /api/auth/verify
Content-Type: application/json

{
  "api_key": "your-access-key"
}

Response:
{
  "valid": true
}
```

#### 更新访问密钥
```http
POST /api/auth/update-key
Headers: X-API-Key: <your-old-key>
Content-Type: application/json

{
  "old_key": "old-access-key",
  "new_key": "new-access-key"
}

Response:
{
  "success": true,
  "message": "访问密钥已更新"
}
```

#### 获取认证状态
```http
GET /api/auth/status
Headers: X-API-Key: <your-access-key>

Response:
{
  "authenticated": true
}
```

### 6. CSV数据接口

#### 获取数据（支持分页和筛选）
```http
GET /api/csv?page=1&page_size=20&search=题目&type=单选题

Response:
{
  "success": true,
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### 获取统计数据
```http
GET /api/csv/stats

Response:
{
  "total": 100,
  "avgTime": 1.23,
  "reasoningCount": 20,
  "totalTime": 123.45,
  "totalCost": 0.5678,
  "totalTokens": 50000,
  "inputTokens": 30000,
  "outputTokens": 20000
}
```

#### 清空数据（需要认证）
```http
POST /api/csv/clear
Headers: X-API-Key: <your-access-key>

Response:
{
  "success": true,
  "message": "CSV文件已清空"
}
```

### 7. 前端页面路由

```http
GET /              # 首页（配置管理面板，需要认证）
GET /models        # 模型管理页（需要认证）
GET /viewer        # 答题记录可视化（公开访问）
GET /docs          # API 文档页面（公开访问）
GET /?t=<timestamp>
# OCS脚本用于测试连接延迟
```

## 🎯 功能介绍

### 1. 多模型支持

支持 DeepSeek、Doubao 以及 OpenAI 官方 / 兼容模型，统一通过“模型管理”页面维护。

#### DeepSeek
- **内置预设**：`DeepSeek V4 Flash`、`DeepSeek V4 Pro`
- **特点**：响应快、成本低，适合作为纯文本题主力模型
- **题型映射**：默认承担单选、判断、填空，以及多选题首选 / 回退

#### 豆包（Doubao）
- **模型**：自定义推理接入点
- **思考强度**：可配置 low/medium/high
- **特点**：支持图片输入，多模态理解

#### OpenAI / 兼容模型
- **协议类型**：支持 `Responses API`、`Chat Completions`
- **高强度思考**：已适配最新 OpenAI reasoning 参数，并请求 reasoning summary
- **向后兼容**：旧兼容网关仍可继续使用 `chat_completions`

### 2. 思考模式

#### 自动启用策略
- **多选题**：自动启用深度思考（可配置 `AUTO_REASONING_FOR_MULTIPLE`）
- **图片题**：自动启用深度思考（可配置 `AUTO_REASONING_FOR_IMAGES`）
- **单选/判断/填空（无图片）**：使用普通模式（除非全局启用）

#### 标签展示
在OCS界面中会显示：
- 🔵 **AI** - OCS自动添加
- 🟣 **深度思考** - 使用思考模式时显示
- 🟡 **自动思考** - 多选题或图片题自动启用时显示
- 🟢 **DEEPSEEK/DOUBAO** - 模型标识

### 3. 图片支持（多模态模型）

#### 自动提取
从题干和选项中自动提取图片URL：
- 支持格式：jpg, jpeg, png, gif, bmp, webp
- 自动去重
- 同时检测题干和选项中的图片

#### 智能思考
- 检测到图片时可自动启用深度思考模式（可配置 `AUTO_REASONING_FOR_IMAGES`）
- 提高图片识别和理解准确率
- 支持多选题+图片题同时触发

#### 智能过滤
过滤无关图标URL：
- `/icon/`, `/icons/`
- `video.png`, `audio.png`
- `play.png`, `pause.png`

#### 自动降级
- 首次尝试使用图片
- 如果图片访问失败，自动切换纯文本模式
- 确保答题流程不中断

### 4. CSV日志记录

自动记录每道题的详细信息：

| 字段 | 说明 |
|------|------|
| 时间戳 | 答题时间 |
| 题型 | 单选/多选/判断/填空 |
| 题目 | 完整题目文本 |
| 选项 | 所有选项（用 \| 分隔）|
| 原始回答 | AI原始返回的答案 |
| 思考过程 | 推理过程（如果有）|
| 处理后答案 | 清洗后的最终答案 |
| AI耗时(秒) | AI调用耗时 |
| 总耗时(秒) | 总处理耗时 |
| 模型 | 使用的模型 |
| 思考模式 | 是/否 |

### 5. 数据可视化

访问 `http://localhost:5000/viewer` 查看：

- 📊 **题型分布**：饼图显示各题型数量
- 📈 **思考模式使用**：思考vs普通模式统计
- ⏱️ **平均耗时**：AI耗时和总耗时对比
- 📋 **详细列表**：可搜索、过滤的题目列表
- 🔍 **详情查看**：点击题目查看完整信息

功能：
- 搜索题目/答案
- 按题型过滤
- 按思考模式过滤
- 导出数据
- 清空数据

## 🧪 测试示例

### 使用curl测试

```bash
# 单选题
curl -X POST http://localhost:5000/api/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "世界上最高的山峰是？",
    "options": ["泰山", "珠穆朗玛峰", "华山", "黄山"],
    "type": 0
  }'

# 多选题（自动启用深度思考）
curl -X POST http://localhost:5000/api/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "以下哪些是Python的特点？",
    "options": ["简洁", "高效", "跨平台", "开源"],
    "type": 1
  }'

# 带图片的题目（豆包）
curl -X POST http://localhost:5000/api/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "图片中是什么动物？ http://example.com/image.jpg",
    "options": ["猫", "狗", "鸟", "鱼"],
    "type": 0,
    "images": ["http://example.com/image.jpg"]
  }'
```

### 使用Python测试

```python
import requests

url = "http://localhost:5000/api/answer"

# 测试单选题
response = requests.post(url, json={
    "question": "1+1等于几？",
    "options": ["1", "2", "3", "4"],
    "type": 0
})

print(response.json())
# Output: {"success": true, "answer": "2", ...}
```

## ❓ 常见问题

### Q1: 如何选择模型？

到“模型管理”页配置题型映射即可。

- `single / judgement / completion` 默认用 `DeepSeek V4 Flash`
- `multiple` 默认用 `DeepSeek V4 Pro`，失败回退 `DeepSeek V4 Flash`
- `image` 默认用 `Doubao`

### Q2: 思考模式应该启用吗？

推荐配置：
```env
ENABLE_REASONING=false              # 全局不启用（节省成本）
AUTO_REASONING_FOR_MULTIPLE=true    # 多选题自动启用（提高准确率）
AUTO_REASONING_FOR_IMAGES=true      # 图片题自动启用（提高识别准确率）
```

**全局启用思考模式**会：
- ✅ 显著提高答案准确率
- ❌ 增加API调用耗时
- ❌ 增加API调用成本

**自动思考模式**（推荐）：
- ✅ 只在需要时启用（多选题、图片题）
- ✅ 平衡准确率和成本
- ✅ 自动判断，无需手动配置

### Q3: API返回"Connection error"

可能原因：
1. **网络问题**：检查网络连接
2. **代理配置**：如需代理，配置 `HTTP_PROXY`/`HTTPS_PROXY`
3. **图片URL问题**（豆包）：
   - 图片URL需要认证
   - 图片URL无法从豆包服务器访问
   - 会自动降级为纯文本模式

解决方案：
```env
# 配置代理
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080

# 增加超时时间
TIMEOUT=120.0

# 增加重试次数
MAX_RETRIES=5
```

### Q4: 图片题目无法识别

**检查清单：**
1. 确认 `image` 题型映射到了多模态模型
2. 检查图片URL是否可访问
3. 查看控制台是否显示"📷 图片"
4. 检查是否被过滤为图标URL

**非多模态模型不会处理图片**，系统会自动清理错误映射。

### Q5: 答案格式不正确

查看控制台输出：
```
🤖 AI原始回答: 北京#上海
✅ 处理后答案: 北京#上海
```

如果原始回答正确但处理后答案错误，可能需要调整 `AnswerProcessor` 类。

### Q6: CSV日志文件太大

清空日志文件：
```bash
# 方法1：通过API
curl -X POST http://localhost:5000/api/csv/clear

# 方法2：通过可视化页面
访问 http://localhost:5000/viewer
点击"清空数据"按钮

# 方法3：手动删除
rm ocs_answers_log.csv  # Linux/Mac
del ocs_answers_log.csv  # Windows
```

### Q7: 如何提高答题准确率？

**策略：**
1. **启用自动思考**：
   - `AUTO_REASONING_FOR_MULTIPLE=true`（多选题，默认开启）
   - `AUTO_REASONING_FOR_IMAGES=true`（图片题，默认开启）
2. **全局思考模式**（可选）：`ENABLE_REASONING=true`（所有题目）
3. **降低温度**：`TEMPERATURE=0.05`（更保守）
4. **使用多模态模型**：图片题目务必映射到支持图片的模型
5. **优化Prompt**：根据学科调整Prompt

### Q8: 服务器部署

使用 gunicorn（生产环境）：

```bash
# 安装gunicorn
pip install gunicorn

# 启动服务（4个worker）
gunicorn -w 4 -b 0.0.0.0:5000 ocs_ai_answerer_advanced:app

# 后台运行
nohup gunicorn -w 4 -b 0.0.0.0:5000 ocs_ai_answerer_advanced:app &
```

使用 systemd（Linux开机自启）：

```bash
# 创建服务文件
sudo nano /etc/systemd/system/ocs-ai.service
```

```ini
[Unit]
Description=OCS AI Answerer Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ocs-ai-answerer
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 ocs_ai_answerer_advanced:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl start ocs-ai
sudo systemctl enable ocs-ai  # 开机自启
```

### Q9: 网络代理配置

```env
# 配置HTTP代理
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080

# 或使用socks5代理
HTTP_PROXY=socks5://127.0.0.1:1080
HTTPS_PROXY=socks5://127.0.0.1:1080
```

### Q10: API密钥安全

**不要：**
- ❌ 将真实密钥提交到Git仓库
- ❌ 在公开代码中硬编码密钥
- ❌ 分享包含密钥的`.env`文件

**应该：**
- ✅ 使用`.env`文件存储密钥
- ✅ 将`.env`添加到`.gitignore`
- ✅ 使用环境变量或密钥管理服务（生产环境）
- ✅ 定期轮换API密钥
- ✅ 使用访问密钥保护配置页面

### Q11: 前端开发和调试

#### 开发环境设置
```bash
cd frontend
npm install
npm run dev  # 启动开发服务器 http://localhost:5173
```

#### 修改后重新构建
```bash
cd frontend
npm run build  # 构建到 dist/ 目录
```

#### 常见问题
- **端口冲突**：修改 `frontend/vite.config.js` 中的 `server.port`
- **API 代理**：开发模式下自动代理 `/api` 到 `http://localhost:5000`
- **热重载失效**：检查是否有文件监听限制（Linux 需要增加 `fs.inotify.max_user_watches`）

#### 前端独立部署（高级）
如果需要将前端部署到 CDN 或独立服务器：

1. **修改 API 基础地址**
```javascript
// frontend/src/utils/axios.js
const axios = axiosLib.create({
  baseURL: 'https://your-api-server.com',  // 修改为实际后端地址
  timeout: 30000
})
```

2. **构建生产版本**
```bash
cd frontend
npm run build
```

3. **部署 dist 目录**
   - 上传到 Nginx/Apache
   - 或使用 CDN（腾讯云 COS、阿里云 OSS 等）
   - 或使用静态托管服务（Vercel、Netlify 等）

4. **配置 CORS**
   后端需要允许跨域访问：
   ```python
   # ocs_ai_answerer_advanced.py
   CORS(app, resources={
       r"/api/*": {
           "origins": ["https://your-frontend-domain.com"],
           "allow_headers": ["Content-Type", "X-API-Key"]
       }
   })
   ```

### Q12: 访问密钥相关问题

#### 忘记访问密钥
```bash
# 查看当前密钥
cat .secret_key

# 或重新生成（会失效旧密钥）
rm .secret_key
python ocs_ai_answerer_advanced.py  # 重启会自动生成新密钥
```

#### 修改访问密钥
- **方法1**：通过 Web 界面（配置页面 → 系统设置 → 安全设置）
- **方法2**：删除 `.secret_key` 文件后重启服务器

#### 多用户共享密钥
- 将 `.secret_key` 文件中的 `raw_key` 分享给其他用户
- 其他用户在浏览器中输入该密钥即可访问
- **注意**：不要在公开渠道分享密钥！

#### 禁用访问密钥（不推荐）
如果在完全可信的内网环境，可以临时禁用：
```python
# 注释掉需要认证的装饰器
# @require_auth  # 注释这一行
def get_config():
    ...
```
**警告**：禁用后配置页面将完全暴露，存在安全风险！

**应该：**
- ✅ 使用`.env`文件存储密钥
- ✅ 将`.env`添加到`.gitignore`
- ✅ 使用环境变量或密钥管理服务（生产环境）
- ✅ 定期轮换API密钥

## 🔒 安全建议

1. **密钥管理**
   - 不要泄露API密钥
   - 使用环境变量存储
   - 定期轮换密钥

2. **访问控制**
   - 限制API访问IP
   - 添加认证机制（如API Token）
   - 使用HTTPS加密通信

3. **日志安全**
   - 定期清理敏感日志
   - 不要记录API密钥
   - 控制日志文件权限

## 🚀 功能规划

### ✅ 已实现的功能

#### 模型路由与故障转移
当前版本的模型选择由“模型管理”中的题型映射决定，而不是 `.env` 中的旧自动选模字段。

**当前工作方式：**
- 图片题优先使用 `image` 题型映射中的多模态模型
- 其余题型按映射列表顺序依次尝试
- 当首选模型失败时，自动回退到同题型的下一个候选模型
- 图片题映射会自动过滤非多模态模型，避免误配置

**推荐默认映射：**
- `single / judgement / completion` → `DeepSeek V4 Flash`
- `multiple` → `DeepSeek V4 Pro`，失败回退 `DeepSeek V4 Flash`
- `image` → `Doubao` 或其他支持多模态的 OpenAI 兼容模型

### 📊 计划中的功能
- 🔍 **题目相似度检测**：避免重复答题
- 💾 **答案缓存机制**：相同题目直接返回缓存答案
- 📈 **答题统计报告**：生成详细的答题分析报告
- 🔔 **错误预警**：自动检测可能的错误答案
- 🌐 **Web管理界面**：图形化配置和管理界面

## 📝 更新日志

### 详细更新见 [CHANGELOG.md](CHANGELOG.md)

### v3.0.0 (2025-11-11) 🎉 重大更新

#### 🎨 前端架构重构
- **Vue 3 + Element Plus**：从纯 HTML 重构为现代化前端框架
- **三大功能模块**：配置管理、数据可视化、API 文档
- **响应式设计**：完美适配桌面和移动端
- **统一导航**：顶部导航栏，页面间自由跳转
- **组件化开发**：ConfigPanel.vue、DataViewer.vue、AuthDialog.vue

#### 🔒 企业级安全机制
- **访问密钥认证**：首次启动自动生成 64 位安全密钥
- **SHA256 加密存储**：密钥哈希存储在 `.secret_key` 文件
- **IP 限流保护**：5 次失败锁定 5 分钟，防暴力破解
- **分级权限控制**：
  - 公开访问：答题接口、数据查看、API 文档、健康检查
  - 需要认证：配置管理、数据清空、服务器重启、密钥修改
- **前端安全集成**：
  - LocalStorage 密钥管理
  - Axios 自动注入认证头
  - 统一响应拦截器
  - 认证对话框组件

#### 📊 数据可视化增强
- **后端分页**：支持大数据量，每页可配置条数
- **高级筛选**：搜索、题型、思考模式、日期范围
- **实时统计**：独立的 `/api/csv/stats` 接口
- **JSON 响应**：返回 JSON 数组，时间降序排序
- **数据导出**：支持 CSV 格式导出
- **认证保护**：清空数据需要访问密钥

#### 🔄 配置管理升级
- **保存并重启**：一键保存配置并自动重启服务器
- **智能轮询**：自动检测服务器重启状态（每秒检查，最多 30 次）
- **实时反馈**：显示保存、重启、轮询进度
- **完整密钥显示**：在受保护的配置页面显示完整 API 密钥
- **行级更新**：保存配置时保留 .env 文件注释和结构
- **密钥管理**：Web 界面修改访问密钥

#### 🛠️ 技术改进
- **跨平台重启**：支持 Windows 和 Linux/Mac 的进程重启
- **打包兼容**：支持 PyInstaller 打包后的 exe 重启
- **前端构建**：Vite 4 构建系统，快速热重载
- **API 增强**：新增 6 个认证相关接口
- **错误处理**：统一的错误处理和用户提示

#### 📚 文档完善
- **完整 API 文档**：包含所有接口的请求/响应示例
- **安全指南**：访问密钥使用说明
- **前端构建指南**：开发和生产环境配置
- **部署说明**：服务器部署和开机自启

### v2.2.0 (2025-11-02)
- 🖼️ **图片题自动思考**：带图片题目自动启用深度思考模式
- 📷 **选项图片检测**：从选项中提取图片URL，完善图片检测
- ⚙️ **配置增强**：新增 `AUTO_REASONING_FOR_IMAGES` 配置项
- 📝 **文档更新**：完整的图片题思考模式说明

### v2.1.0 (2025-11-02)
- 🤖 **智能模型选择**：根据题目自动选择最合适的模型
- 🔧 **思考模式token配置**：单独配置思考模式的max_tokens
- 📝 **详细参数说明**：完整的AI参数文档和推荐配置
- 🔒 **安全优化**：移除硬编码密钥，完善.gitignore
- 📖 **文档增强**：API密钥获取指南、脚本猫推荐
- 🏷️ **标签兼容**：完整支持purple/orange标签颜色

### v2.0.0 (2025-11-02)
- ✨ 支持多模型（DeepSeek + 豆包）
- 🧠 支持思考模式（深度推理）
- 🖼️ 支持图片输入（豆包多模态）
- 📊 CSV日志记录功能
- 📈 HTML可视化界面
- ⚙️ 环境变量配置
- 🔄 智能降级机制
- 🏷️ OCS标签展示

### v1.0.0 (2024-11-01)
- ✨ 初始版本发布
- 🎯 支持4种题型（单选/多选/判断/填空）
- 🤖 集成DeepSeek AI
- 📝 优化的Prompt工程
- 🔄 智能答案处理

## 📄 License

MIT License

Copyright (c) 2024-2025

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

> 🤖 **AI 参与声明**
> 
> 本项目的设计、开发和维护过程中大量使用了人工智能技术。AI 作为开发工具，协助完成了代码编写、文档生成、问题诊断等工作。所有 AI 生成的内容都经过审核和测试，确保质量和可用性。

## 🤝 贡献

欢迎提交Issue和Pull Request！

> 💡 **关于 AI 维护**
> 
> 本项目采用 AI 辅助开发模式：
> - ✅ Issue 响应：AI 会参与问题分析和解答
> - ✅ 代码审查：AI 协助进行代码质量检查
> - ✅ 功能开发：AI 参与新功能的设计和实现
> - ✅ 文档更新：AI 自动维护技术文档
> 
> 人类开发者依然负责最终决策和代码审核。

## 📧 联系方式

- 📦 项目主页：https://github.com/lkd6666/ocs-ai-answerer
- 🐛 问题反馈：https://github.com/lkd6666/ocs-ai-answerer/issues
- ⭐ 给个Star：https://github.com/lkd6666/ocs-ai-answerer/stargazers
- 🌐 OCS 官网：https://docs.ocsjs.com/
- 📖 OCS 文档：https://docs.ocsjs.com/docs/work

---

<div align="center">

⭐ 如果这个项目对你有帮助，请给个star支持一下！⭐

**主要特性**
🤖 多模型 | 🧠 深度思考 | 🖼️ 图片识别 | 📊 数据可视化

**规划功能**
🎯 智能模型选择 | 💾 答案缓存 | 📈 统计报告 | 🌐 Web管理

---

**开发模式**
🤖 AI 辅助开发 | 💡 智能设计 | 🔧 自动优化 | 📝 文档自动生成

*本项目展示了 AI 在软件开发领域的创新应用*

</div>
