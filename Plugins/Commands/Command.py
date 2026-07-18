from nonebot.log import logger
from nonebot_plugin_alconna import on_alconna, Match
from nonebot_plugin_uninfo import Uninfo
from arclet.alconna import Alconna, Args

from Scripts.Config import config
from Scripts.Managers import server_manager
from Scripts.Utils import turn_message_text

logger.debug('加载命令 Command 完毕！')

# 使用 Args 接收不定长参数，command 部分作为一个整体
matcher = on_alconna(
    Alconna("command", Args["server", str]["command?", str]),
    use_cmd_start=True,
)


@matcher.handle()
async def handle(session: Uninfo, server: Match[str], command: Match[str]):
    if not command.available:
        await matcher.finish('参数不正确！请查看语法后再试。')
    message = await turn_message_text(command_handler(server.result, command.result))
    await matcher.finish(message)


def parse_command(command: str):
    if config.command_minecraft_whitelist:
        for enabled_command in config.command_minecraft_whitelist:
            if command.startswith(enabled_command):
                return command
        return None
    for disabled_command in config.command_minecraft_blacklist:
        if command.startswith(disabled_command):
            return None
    return command


async def command_handler(server_flag, command):
    if not (cmd := parse_command(command)):
        yield f'命令 {command} 已被禁止！'
        return
    if server_flag == '*':
        if not server_manager.servers:
            yield '当前没有已连接的服务器，无法执行命令！'
            return
        for name, bot in server_manager.servers.items():
            yield '已发送指令到所有服务器：'
            try:
                result = await bot.send_rcon_command(cmd)
                yield f'  [{name}] -> {result if result else "无返回值"}'
            except Exception as error:
                logger.warning(f'向服务器 [{name}] 发送指令失败：{error}')
                yield f'  [{name}] -> 发送指令失败'
        return
    bot = server_manager.get_server(server_flag)
    if bot is None:
        yield f'服务器 [{server_flag}] 不存在！请检查插件配置。'
        return
    try:
        result = await bot.send_rcon_command(cmd)
        yield f'命令已发送到服务器 [{bot.id}]！服务器回应：{result if result else "无返回值"}'
    except Exception as error:
        yield f'向服务器 [{server_flag}] 发送指令失败：{error}'
