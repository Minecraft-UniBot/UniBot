from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import Command
from nonebot_plugin_alconna.uniseg import Image, UniMessage

from Scripts.Config import config
from Scripts.Globals import render_template
from Scripts.Managers import server_manager
from Scripts.Utils import turn_message_text
from Scripts.Rules import command_group_rule

__plugin_meta__ = PluginMetadata(
    name='服务器列表',
    description='展示当前与 UniBot 建立连接的 Minecraft 服务器。',
    usage='.server',
)

matcher = (
    Command('server', '查看已连接的服务器列表。')
    .build(rule=command_group_rule, use_cmd_start=True)
)


@matcher.handle()
async def handle():
    if config.image.mode:
        servers = [
            {'name': name, 'index': index}
            for index, name in enumerate(server_manager.servers.keys())
        ]
        image = await render_template('Server', (500, 0), servers=servers)
        await matcher.finish(UniMessage(Image(raw=image)))
    message = await turn_message_text(server_handler())
    await matcher.finish(message)


async def server_handler():
    if not server_manager.servers:
        yield '当前没有已连接的服务器！'
        return
    for index, name in enumerate(server_manager.servers.keys()):
        yield f'[{index}] {name}'
