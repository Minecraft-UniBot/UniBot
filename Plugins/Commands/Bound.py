from nonebot.log import logger

from nonebot_plugin_uninfo import Uninfo
from nonebot_plugin_alconna import Match, At, Command
from nonebot_plugin_alconna.uniseg import Image, UniMessage

from Scripts.Config import config
from Scripts.Globals import render_template
from Scripts.Managers import data_manager, server_manager
from Scripts.Utils import check_player, get_permission
from Scripts.Rules import command_group_rule

logger.debug('加载命令 Bound 完毕！')

matcher = (
    Command('bound <player?#要绑定的玩家名:str>', '管理玩家白名单绑定。')
    .subcommand('list #列出所有绑定')
    .subcommand('query <user_id?:At|str> #查询指定用户的绑定')
    .subcommand('remove <player:At|str> #移除指定绑定')
    .subcommand('append <user_id:At|str> <player:str> #为指定用户添加绑定')
    .build(rule=command_group_rule, use_cmd_start=True)
)

@matcher.assign('$main')
async def handle_base(session: Uninfo, player: Match[str]):
    '''处理 .bound <player>'''
    if not player.available:
        await matcher.finish('请输入要绑定的玩家名称！')
    message = await bound_handler(session, player.result)
    await matcher.finish(message)


async def bound_handler(session: Uninfo, player: str):
    if not check_player(player):
        return '此玩家名称非法！玩家名称应只包含字母、数字、下划线且长度不超过 16 个字符。'
    user = str(session.user.id)
    if user in data_manager.players and player in data_manager.players[user]:
        return '你已经绑定了此白名单！'
    if await data_manager.check_player_occupied(player):
        return '此玩家名称已经绑定过了，请换一个名称！'
    if not server_manager.check_online():
        return '当前没有已连接的服务器，绑定失败！请联系管理员连接后再试。'
    if await data_manager.append_player(user, player):
        await server_manager.execute(f'{config.whitelist_command} add {player}')
        return f'用户 {session.user.name or user}({user}) 已成功绑定白名单到 {player} 玩家。'
    return '你绑定的玩家个数过多，绑定失败！'


@matcher.assign('list')
async def handle_list(session: Uninfo):
    '''处理 .bound list'''
    if not get_permission(session):
        await matcher.finish('你没有权限执行此命令！')
    if not data_manager.players:
        await matcher.finish('当前没有绑定任何玩家！')
    if config.image_mode:
        bindings = [
            {'user': user, 'players': players}
            for user, players in data_manager.players.items()
        ]
        image = await render_template('Bound', (600, 800), bindings=bindings)
        await matcher.finish(UniMessage(Image(raw=image)))
    message = '白名单列表：\n' + '\n'.join(
        f'  {user} -> {'、'.join(players)}' for user, players in data_manager.players.items()
    )
    await matcher.finish(message)


@matcher.assign('query')
async def handle_query(session: Uninfo, user_id: Match[At | str]):
    '''处理 .bound query [user_id]'''
    target_user = user_id.result if user_id.available else str(session.user.id)
    if isinstance(target_user, At):
        target_user = target_user.target
    if target_user not in data_manager.players:
        await matcher.finish(f'用户 ({target_user}) 还没有绑定白名单！')
    await matcher.finish(f'用户 ({target_user}) 绑定的白名单有 {'、'.join(data_manager.players[target_user])} 。')


@matcher.assign('remove')
async def handle_remove(session: Uninfo, player: Match[str]):
    '''处理 .bound remove [player]'''
    current_user = str(session.user.id)
    if not player.available:
        # .bound remove - 自己解绑全部
        await matcher.finish(await bound_remove_self_all(session))
    # .bound remove <QQ> - 管理员解绑用户
    if player.result != current_user and not get_permission(session):
        await matcher.finish('你没有权限执行此命令！')
    await matcher.finish(await bound_remove_user(player.result))


@matcher.assign('append')
async def handle_append(session: Uninfo, user_id: At | str, player: str):
    '''处理 .bound append <user_id> <player>'''
    if not get_permission(session):
        await matcher.finish('你没有权限执行此命令！')
    message = await bound_append_handler(user_id.target if isinstance(user_id, At) else user_id, player)
    await matcher.finish(message)


async def bound_append_handler(user: str, player: str):
    if not check_player(player):
        return '玩家名称非法！玩家名称只能包含字母、数字、下划线且长度不超过 16 个字符。'
    if await data_manager.check_player_occupied(player):
        return '此玩家名称已经绑定过了，请换一个名称！'
    if not server_manager.check_online():
        return '当前没有已连接的服务器，绑定失败！请连接后再试。'
    if await data_manager.append_player(user, player):
        await server_manager.execute(f'{config.whitelist_command} add {player}')
        return f'用户 ({user}) 已绑定白名单到 {player} 玩家。'
    return '你绑定的玩家个数过多，绑定失败！'


async def bound_remove_player(session: Uninfo, player_name: str):
    if not server_manager.check_online():
        return '当前没有已连接的服务器，请稍后再次尝试！'
    user = str(session.user.id)
    if await data_manager.remove_player(user, player_name):
        await server_manager.execute(f'{config.whitelist_command} remove {player_name}')
        return f'已移除白名单 {player_name}！'
    return f'你没有绑定名为 {player_name} 的白名单！'


async def bound_remove_user(target_user: str):
    if not server_manager.check_online():
        return '当前没有已连接的服务器，请稍后再次尝试！'
    bounded = await data_manager.remove_player(target_user)
    if not bounded:
        return f'用户 ({target_user}) 还没有绑定白名单！'
    for player in bounded:
        await server_manager.execute(f'{config.whitelist_command} remove {player}')
    return f'已移除用户 ({target_user}) 绑定的所有白名单！'


async def bound_remove_self_all(session: Uninfo):
    if not server_manager.check_online():
        return '当前没有已连接的服务器，请稍后再次尝试！'
    user = str(session.user.id)
    bounded = await data_manager.remove_player(user)
    if not bounded:
        return '你还没有绑定白名单！'
    for player in bounded:
        await server_manager.execute(f'{config.whitelist_command} remove {player}')
    return '已移除所有绑定的白名单！'
