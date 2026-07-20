from nonebot.log import logger
from nonebot_plugin_alconna import Command, Match
from nonebot_plugin_uninfo import Uninfo

from Scripts.Managers import data_manager, server_manager
from Scripts.Utils import get_player_name
from Scripts.Rules import command_group_rule

logger.debug('加载命令 Send 完毕！')

matcher = (
    Command('send <message#要发送的消息内容:str+>', '向已连接的服务器发送消息。')
    .build(rule=command_group_rule, use_cmd_start=True)
)


@matcher.handle()
async def handle(session: Uninfo, message: Match[list[str]]):
    if not message.available:
        await matcher.finish('参数错误，请检查命令格式！')
    msg = ' '.join(message.result).strip()
    if not msg:
        await matcher.finish('参数错误，请检查命令格式！')
    user_id = str(session.user.id)
    user_name = session.user.name or get_player_name(str(session.user.name))
    if name := data_manager.players.get(user_id, (user_name,))[0]:
        await server_manager.send_message(f'[QQ]<{name}> {msg}')
        await matcher.finish(f'已向服务器发送消息：{msg}。')
    await server_manager.send_message(f'[QQ]<未知用户> {msg}')
    await matcher.finish('未找到你的玩家名称，请绑定后再试！')
