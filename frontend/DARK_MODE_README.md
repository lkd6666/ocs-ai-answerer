# 暗黑模式使用说明

## 🌙 功能概述

前端现已完整支持暗黑模式，提供了以下功能：

- ✅ **自动跟随系统**：默认跟随系统主题设置
- ✅ **手动切换**：可以手动切换浅色/深色模式
- ✅ **记忆功能**：保存用户的主题选择
- ✅ **平滑过渡**：主题切换时有流畅的动画效果
- ✅ **全局适配**：所有组件都完美适配暗黑模式

## 🎨 使用方法

### 切换主题

1. 点击顶部导航栏右侧的**主题图标按钮**
2. 在下拉菜单中选择：
   - **跟随系统**：根据操作系统的主题设置自动切换
   - **浅色模式**：始终使用浅色主题
   - **深色模式**：始终使用深色主题

### 主题图标说明

- 🖥️ **显示器图标**：当前为"跟随系统"模式
- ☀️ **太阳图标**：当前为"浅色模式"
- 🌙 **月亮图标**：当前为"深色模式"

## 🎯 特性

### 1. 智能跟随系统

默认情况下，应用会自动检测并跟随系统的主题设置：

- **Windows 10/11**：设置 → 个性化 → 颜色 → 选择模式
- **macOS**：系统偏好设置 → 通用 → 外观
- **Linux**：取决于桌面环境设置

当系统主题改变时，应用会实时响应并切换。

### 2. 用户偏好记忆

用户的主题选择会自动保存到浏览器本地存储，下次访问时会自动应用。

### 3. 平滑过渡动画

所有主题切换都有0.3秒的平滑过渡动画，确保视觉体验流畅。

### 4. 全局样式适配

- ✅ Element Plus 组件自动适配
- ✅ 自定义组件样式完美适配
- ✅ 卡片、表格、对话框等都有对应的暗黑样式
- ✅ 颜色对比度符合WCAG标准

## 🎨 主题颜色

### 浅色模式
- 背景渐变：紫色渐变 (#667eea → #764ba2)
- 导航栏：白色 (#ffffff)
- 卡片背景：白色
- 文字颜色：深色

### 深色模式  
- 背景渐变：深蓝渐变 (#1a1a2e → #16213e)
- 导航栏：深灰色 (#1a1a1a)
- 卡片背景：深色 (Element Plus 暗黑主题)
- 文字颜色：浅色

## 💻 技术实现

### 文件结构

```
frontend/src/
├── utils/
│   └── theme.js           # 主题管理工具
├── styles/
│   └── dark.css          # 暗黑模式全局样式
├── App.vue               # 主题切换器和应用逻辑
└── main.js               # 导入暗黑模式CSS
```

### 核心API

```javascript
// theme.js 提供的API
import { 
  getThemeMode,      // 获取主题模式 (auto/light/dark)
  saveThemeMode,     // 保存主题模式
  getActualTheme,    // 获取实际主题 (light/dark)
  applyTheme,        // 应用主题到HTML
  watchSystemTheme   // 监听系统主题变化
} from './utils/theme'
```

### HTML类名

主题通过在 `<html>` 标签上添加 `dark` 类来实现：

```html
<!-- 浅色模式 -->
<html></html>

<!-- 深色模式 -->
<html class="dark"></html>
```

所有暗黑模式样式都使用 `.dark` 前缀：

```css
/* 浅色模式 */
.app-container {
  background: white;
}

/* 深色模式 */
.dark .app-container {
  background: #1a1a1a;
}
```

## 🔧 自定义样式

如果需要为新组件添加暗黑模式支持，请遵循以下模式：

```vue
<style scoped>
/* 浅色模式样式 */
.my-component {
  background: white;
  color: #000;
}

/* 深色模式样式 */
.dark .my-component {
  background: #1a1a1a;
  color: #fff;
}

/* 添加过渡动画 */
.my-component {
  transition: background-color 0.3s ease, color 0.3s ease;
}
</style>
```

## 📱 浏览器兼容性

- ✅ Chrome 76+
- ✅ Firefox 67+
- ✅ Safari 12.1+
- ✅ Edge 79+

## 🐛 已知问题

1. **IE浏览器**：不支持 `prefers-color-scheme` 媒体查询，无法自动跟随系统主题
2. **部分旧浏览器**：可能不支持CSS自定义属性，暗黑模式可能显示异常

## 🚀 最佳实践

### 开发建议

1. **测试两种模式**：开发新功能时应同时测试浅色和深色模式
2. **使用CSS变量**：优先使用Element Plus提供的CSS变量
3. **避免硬编码颜色**：使用语义化的颜色变量而不是直接写颜色值
4. **确保对比度**：深色模式下确保文字和背景有足够的对比度

### 用户体验建议

1. 大多数用户会选择"跟随系统"模式
2. 长时间使用建议切换到深色模式减轻眼睛疲劳
3. 白天使用浅色模式，夜间使用深色模式

## 📚 相关资源

- [Element Plus 暗黑模式文档](https://element-plus.org/zh-CN/guide/dark-mode.html)
- [CSS变量文档](https://developer.mozilla.org/zh-CN/docs/Web/CSS/Using_CSS_custom_properties)
- [prefers-color-scheme](https://developer.mozilla.org/zh-CN/docs/Web/CSS/@media/prefers-color-scheme)

## 💡 常见问题

### Q: 如何重置主题设置？
A: 打开浏览器开发者工具 → Application → Local Storage → 删除 `ocs_theme_mode` 键

### Q: 为什么我的主题没有跟随系统变化？
A: 请确保：
1. 选择了"跟随系统"模式
2. 浏览器支持 `prefers-color-scheme`
3. 操作系统已正确设置主题

### Q: 如何禁用暗黑模式？
A: 目前无法完全禁用，但可以强制选择"浅色模式"

---

**更新日期**: 2024-11-12  
**版本**: v2.3.0
