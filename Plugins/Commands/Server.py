from nonebot.log import logger
from nonebot_plugin_alconna import Command

from Scripts.Managers import server_manager
from Scripts.Utils import turn_message_text
from Scripts.Rules import command_group_rule

logger.debug('加载命令 Server 完毕！')

# 使用 Args 接收不定长参数，command 部分作为一个整体
matcher = Command('server').build(rule=command_group_rule, use_cmd_start=True)


@matcher.handle()
async def handle():
    message = await turn_message_text(server_handler())
    await matcher.finish(message)


async def server_handler():
    if not server_manager.servers:
        yield '当前没有已连接的服务器！'
        return
    for index, name in enumerate(server_manager.servers.keys()):
        yield f'[{index}] {name}'
