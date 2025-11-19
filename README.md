# Popup AI

弹出式 AI 助手 - 基于 Python + GTK4 + Libadwaita 的 Wayland 原生应用

## 特性

- 🚀 自管理后台进程，零延迟弹窗
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

# 使用
popup-ai                    # 弹出窗口（自动启动后台）
popup-ai "你的文本"          # 带初始文本弹出
popup-ai start              # 手动启动后台进程
popup-ai stop               # 停止后台进程
popup-ai restart            # 重启后台进程
popup-ai status             # 查看后台状态
```

## 后台进程管理

Popup AI 使用自管理的后台进程（daemon），无需 systemd：

- 首次运行时自动启动后台进程
- 后台进程通过 D-Bus 监听窗口调用请求
- 支持窗口最小化后快速恢复
- 命令响应时间 < 100ms

详细文档请参考 [DAEMON.md](DAEMON.md)

## 项目结构

```
popup_ai/
├── main.py          # 程序入口
├── daemon.py        # 后台进程管理
├── application.py   # GTK Application
├── window.py        # 主窗口
├── preferences.py   # 设置窗口
├── ai_service.py    # AI 服务层
└── config.py        # 配置管理

data/               # 桌面文件、D-Bus 服务等
```

## 系统要求

- Python >= 3.11
- GTK4
- Libadwaita
- Wayland
