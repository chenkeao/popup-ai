# Popup AI Daemon Management

Popup AI 使用自管理的后台进程（daemon）来保持应用常驻，无需 systemd。

## 架构

- **客户端模式**: `popup-ai [text]` - 通过 D-Bus 与后台进程通信，显示窗口
- **后台进程**: 自动启动并管理，监听 D-Bus 消息，创建和管理 GTK 窗口

## 使用方法

### 基本使用

```bash
# 打开窗口（自动启动后台进程）
popup-ai

# 打开窗口并设置初始文本
popup-ai "你好，这是一个测试"
```

### 后台进程控制

```bash
# 手动启动后台进程
popup-ai start

# 停止后台进程
popup-ai stop

# 重启后台进程
popup-ai restart

# 查看后台进程状态
popup-ai status
```

## 自动启动

后台进程会在第一次使用 `popup-ai` 时自动启动，无需手动管理。

如果需要在系统启动时自动启动，可以添加到自动启动应用：

1. 打开系统设置 -> 自动启动应用
2. 添加命令：`/home/你的用户名/.local/bin/popup-ai start`

或者创建 autostart 文件：

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/popup-ai.desktop << EOF
[Desktop Entry]
Type=Application
Name=Popup AI
Exec=$HOME/.local/bin/popup-ai start
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
```

## 技术细节

- **PID 文件**: `$XDG_RUNTIME_DIR/popup-ai.pid`
- **锁文件**: `$XDG_RUNTIME_DIR/popup-ai.lock`
- **日志文件**: `$XDG_RUNTIME_DIR/popup-ai.log`
- **D-Bus 服务**: `io.github.chenkeao.PopupAI`

## 故障排除

### 后台进程无法启动

```bash
# 检查状态
popup-ai status

# 查看日志
cat $XDG_RUNTIME_DIR/popup-ai.log
```

### 进程僵死

```bash
# 强制停止并清理
popup-ai stop
rm -f $XDG_RUNTIME_DIR/popup-ai.pid

# 重新启动
popup-ai start
```

### D-Bus 连接问题

确保 D-Bus 会话总线正在运行：

```bash
echo $DBUS_SESSION_BUS_ADDRESS
```

### 查看实时日志

```bash
tail -f $XDG_RUNTIME_DIR/popup-ai.log
```
