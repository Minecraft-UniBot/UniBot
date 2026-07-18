# Minecraft_QQBot

### [**文档**](https://mcbot.ytb.icu/)

**一款基于 Nonebot2 与 Minecraft 交互的跨平台 QQ 机器人**。使用 `nonebot-adapter-minecraft` 代替自定义 WebSocket 实现与 Minecraft 服务器的通信，通过 `nonebot_plugin_alconna` + `uninfo` 实现跨平台指令支持。

目前已实现的功能有：

- 多服互联，群服互通。
  - 在不同服务器之间转发消息。
  - 可在游戏内看到 QQ 群的消息。
  - 可使用指令在游戏内向 QQ 群发送消息。
  - 可播报服务器开启、关闭，玩家进入离开服务器以及死亡消息。
- 可自行配置指令的开启或关闭。
- 可自行配置接入 AI 功能。
- 跨平台指令支持。目前已实现的指令有：
  - `luck` 查看今日幸运指数。
  - `list` 查询每个服务器的玩家在线情况。
  - `help` 查看帮助信息。
  - `server` 查看当前在线的服务器并显示对应编号。
  - `bound` 有关绑定白名单的指令。
  - `command` 发送指令到服务器。
  - `send` 发送消息到服务器。

更多功能还在探索中……

> [!WARNING]
> 本项目采用 GPL3 许可证，请勿商用！如若修改请务必开源并且注明出处。

## 架构

```
BotServer
├── nonebot2 核心
├── nonebot-adapter-onebot      ← QQ 平台接入
├── nonebot-adapter-minecraft   ← Minecraft 服务器通信
├── nonebot_plugin_alconna      ← 跨平台命令处理
├── nonebot_plugin_uninfo       ← 统一会话信息
├── Plugins/Commands/           ← 指令（Alconna 跨平台）
├── Plugins/Events.py           ← MC 事件处理（加入/离开/死亡/聊天）
└── Scripts/                    ← 核心逻辑
```

Minecraft 服务端需安装 [鹊桥（QueQiao）](https://github.com/17TheWord/MC_QQ_Spigot) 插件/模组来连接机器人。

## 快速开始

1. 配置 `.env` 文件，填写 `SUPERUSERS`、`MESSAGE_GROUPS`、`COMMAND_GROUPS` 等必要配置
2. 配置 `MINECRAFT_WS_URLS`：

  ```ini
  MINECRAFT_WS_URLS={"server1": ["ws://你的服务器IP:端口/路径"]}
  ```

3. 在 Minecraft 服务端安装鹊桥插件，配置连接地址指向机器人
4. 启动机器人

## Docker 部署

本项目支持使用 Docker 进行部署，方便快捷。

### 使用 Docker Compose

```bash
git clone https://github.com/Minecraft-QQBot/BotServer
cd BotServer
docker-compose up -d
```

### 自行构建镜像

```bash
docker build -t minecraft-qqbot .
docker run -d \
  --name minecraft-qqbot \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/Logs:/app/Logs \
  --restart unless-stopped \
  minecraft-qqbot
```

## 鸣谢

- [nonebot-adapter-minecraft](https://github.com/17TheWord/nonebot-adapter-minecraft) 提供了 Minecraft 协议适配。
- [NoneBot2](https://nonebot.dev/) 机器人框架。
- 感谢以下人员为此机器人开发提供帮助，在此特别鸣谢：
  - [Msg_Lbo](https://github.com/Msg-Lbo) 提供网站服务器以及域名。
  - [meng877](https://github.com/meng877) 提出意见，贡献部分代码。
  - [Decent_Kook](https://github.com/AISophon) 提供测试环境，提出意见，帮忙宣传。
  - [creepebucket](https://github.com/creepebucket) 提供测试环境。

> [!TIP]
> 若遇到问题，或有更好的想法，可以加入 QQ 群 [`962802248`](https://qm.qq.com/q/B3kmvJl2xO) 或者提交 Issues
> 向作者反馈。若你有能力，欢迎为本项目提供代码贡献！

## 友链

- TQM 服务器
- [LemonFate 服务器](https://www.lemonfate.cn/)
- [RedstoneDaily 红石日报](https://www.redstonedaily.com/)
