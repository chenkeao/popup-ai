# Popup AI

弹出式 AI 助手 - 基于 Python + GTK4 + Libadwaita 的 Wayland 原生应用

## 特性

- 🚀 通过 systemd 用户服务实现零延迟弹窗
- 🤖 支持本地模型 (Ollama) 和 API 调用
- 💬 流式 AI 响应，可随时停止
- 📝 自定义 prompt 模板管理
- 💾 对话历史记录
- 🎨 现代化 Libadwaita UI
- ⌨️ 快捷键支持 (Ctrl+Enter 发送)

## 快速开始

### 开发环境

```bash
# 安装系统依赖 (Fedora)
sudo dnf install python3 python3-gobject gtk4 libadwaita python3-cairo meson

# 设置开发环境
./setup-dev.sh

# 运行程序
./run-dev.sh
```

### 生产安装

```bash
# 编译安装
./install.sh

# 启用后台服务
systemctl --user enable --now popup-ai.service

# 使用
popup-ai                    # 弹出窗口
popup-ai "你的文本"          # 带初始文本弹出
```

## 项目结构

```
popup_ai/
├── main.py          # 程序入口
├── application.py   # GTK Application
├── window.py        # 主窗口
├── preferences.py   # 设置窗口
├── ai_service.py    # AI 服务层
└── config.py        # 配置管理

data/               # 桌面文件、systemd 服务等
```

## 系统要求

- Python >= 3.11
- GTK4
- Libadwaita
- Wayland
- systemd (用户服务)
