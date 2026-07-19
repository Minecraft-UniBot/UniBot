import asyncio
from datetime import datetime

from nonebot import on_notice, on_message, on_command
from nonebot.params import ArgPlainText
from nonebot.log import logger
from nonebot.adapters.minecraft import PlayerChatEvent, PlayerJoinEvent, PlayerQuitEvent, PlayerDeathEvent
from nonebot.adapters.minecraft.message import MessageSegment
from nonebot.adapters.minecraft.models import HoverAction, HoverEvent, Component

from nonebot_plugin_uninfo import Uninfo, SupportScope as UninfoSupportScope
from nonebot_plugin_alconna import Target, SupportScope as AlconnaSupportScope
from nonebot_plugin_alconna.uniseg import UniMsg

from Scripts.Config import config
from Scripts.Managers import server_manager
from Scripts.Utils import check_message


notice_watcher = on_notice()
message_watcher = on_message()


scope_mapping = {
    str(UninfoSupportScope.qq_client): 'QQ',
    str(UninfoSupportScope.qq_guild): 'QQ 频道',
    str(UninfoSupportScope.telegram): 'Telegram',
    str(UninfoSupportScope.discord): 'Discord',
    str(UninfoSupportScope.dodo): 'DoDo',
    str(UninfoSupportScope.kook): 'Kook',
    str(UninfoSupportScope.wechat): '微信',
    str(UninfoSupportScope.wecom): '企业微信',
}
segment_mapping = {
    'text': lambda seg: seg.data.get('text', ''),
    'image': lambda seg: '[图片]',
    'video': lambda seg: '[视频]',
    'audio': lambda seg: '[语音]',
    'file': lambda seg: '[文件]'
}


def message_to_text(message: UniMsg):
    '''将 UniMsg 转换为文本'''

    texts = [func(seg) for seg in message if (func := segment_mapping.get(seg.type)) is not None if func(seg)]
    return ' '.join(texts)


def build_server_message(source: str, player: str, content: str):
    '''构建服务器消息'''
    now_time = datetime.now().strftime('%H:%M:%S')
    hover_event = HoverEvent(action=HoverAction.show_text, contents=Component(text=now_time))
    message = MessageSegment.text(f'[{source}] ', color=config.sync_color_source, hover_event=hover_event)
    message += MessageSegment.text(f'[{player}] ', color=config.sync_color_player, hover_event=hover_event)
    message += MessageSegment.text(content, color=config.sync_color_message, hover_event=hover_event)
    return message


async def send_message_to_group(message: str):
    try:
        for group_info in config.message_groups:
            platform, group_id = group_info.split(':')
            if scope := getattr(AlconnaSupportScope, platform.lower(), None):
                asyncio.create_task(Target.group(group_id, scope).send(message))
                continue
            logger.warning(f'不支持的平台类型：{platform}，请检查配置文件！')
        return True
    except Exception:
        logger.warning('发送群消息到失败！请检查机器人状态或填写群组信息是否正确。')
        return False


@notice_watcher.handle()
async def handle_player_join(event: PlayerJoinEvent):
    '''处理玩家加入服务器事件'''
    name = event.server_name
    player = event.player.nickname
    logger.info(f'收到玩家 {player} 加入服务器 [{name}] 通知！')

    if config.list_compatible_mode:
        # 在兼容模式下记录玩家
        pass

    server_message = f'玩家 {player} 加入了游戏。'
    group_message = f'玩家 {player} 加入了 [{name}] 服务器，喵～'

    if config.bot_prefix and player.upper().startswith(config.bot_prefix):
        group_message = f'机器人 {player} 加入了 [{name}] 服务器。'
        server_message = f'[{name}] 机器人 {player} 加入了游戏。'

    if config.sync_message_between_servers:
        await server_manager.broadcast(build_server_message(name, player, server_message), name)

    if config.broadcast_player:
        await send_message_to_group(group_message)


@notice_watcher.handle()
async def handle_player_quit(event: PlayerQuitEvent):
    '''处理玩家离开服务器事件'''
    name = event.server_name
    player = event.player.nickname
    logger.info(f'收到玩家 {player} 离开服务器 [{name}] 通知！')

    server_message = f'玩家 {player} 离开了游戏。'
    group_message = f'玩家 {player} 离开了 [{name}] 服务器，呜……'

    if config.bot_prefix and player.upper().startswith(config.bot_prefix):
        server_message = f'机器人 {player} 离开了游戏。'
        group_message = f'机器人 {player} 离开了 [{name}] 服务器。'

    if config.sync_message_between_servers:
        await server_manager.broadcast(build_server_message(name, player, server_message), name)

    if config.broadcast_player:
        await send_message_to_group(group_message)


@notice_watcher.handle()
async def handle_player_death(event: PlayerDeathEvent):
    '''处理玩家死亡事件'''
    name = event.server_name
    player = event.player.nickname
    death_message = event.death.text or f'{player} 死亡了'
    logger.debug(f'收到玩家死亡消息：{death_message}')

    if (not config.bot_prefix) or (not player.upper().startswith(config.bot_prefix)):
        broadcast_message = f'玩家 {player} 死亡了，呜……'
        if config.sync_message_between_servers:
            await server_manager.broadcast(build_server_message(name, player, broadcast_message), name)
        if config.broadcast_player:
            await send_message_to_group(broadcast_message)


@message_watcher.handle()
async def handle_player_chat(event: PlayerChatEvent):
    '''处理玩家聊天事件'''
    name = event.server_name
    player = event.player.nickname
    chat_message = str(event.message)
    logger.debug(f'收到玩家 {player} 在服务器 [{name}] 发送消息！')

    if config.sync_all_game_message:
        if check_message(chat_message):
            logger.warning(f'检测到消息 {chat_message} 包含敏感词，已丢弃！')
            await send_message_to_group(f'检测到玩家 {player} 发送的消息包含敏感词，已丢弃！详情请看控制台。')
            return

        await send_message_to_group(f'[{name}] <{player}> {chat_message}')

    if config.sync_message_between_servers:
        await server_manager.broadcast(build_server_message(name, player, chat_message), name)


@message_watcher.handle()
async def handle_group_message(message: UniMsg, session: Uninfo):
    if session.scope == 'Minecraft':
        text_message = message_to_text(message)
        old_text_message = text_message.strip()
        for prefix in config.command_start:
            text_message = text_message.lstrip(prefix).strip()
        if old_text_message == text_message:
            await message_watcher.finish()
        logger.debug(f'收到服务器指令：{text_message}')
        commands = ('send', 'gp', 'qq')
        old_text_message = text_message
        for command in commands:
            if text_message.startswith(command):
                text_message = text_message.lstrip(command).strip()
        if old_text_message == text_message:
            await message_watcher.finish()
        if not text_message:
            await message_watcher.finish('请在指令后输入要发送的消息！')
        if check_message(text_message):
            await message_watcher.finish('检测到消息包含敏感词，已丢弃！')
        await send_message_to_group(f'[{session.self_id}] <{session.user.name}> {text_message}')
        await message_watcher.finish('消息已发送！')
    platform_name = scope_mapping.get(session.scope, '未知平台')
    await server_manager.broadcast(build_server_message(platform_name, session.user.name or str(session.user.id), message_to_text(message)))
