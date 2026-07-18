from nonebot_plugin_alconna import on_alconna, Match
from nonebot_plugin_uninfo import Uninfo
from arclet.alconna import Alconna, Args, Subcommand

from Scripts.Config import config
from Scripts.Managers import data_manager, server_manager
from Scripts.Utils import check_player, get_permission

matcher = on_alconna(
    Alconna(
        "bound",
        Subcommand("append", Args["user_id", str]["player", str]),
        Subcommand("list"),
        Subcommand("query", Args["user_id?", str]),
        Subcommand("remove", Args["user_id?", str]["player?", str]),
        Args["player?", str]
    ),
    use_cmd_start=True,
    priority=10,
)


@matcher.handle()
async def handle_base(session: Uninfo, player: Match[str]):
    """处理 .bound <player>"""
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
    if data_manager.check_player_occupied(player):
        return '此玩家名称已经绑定过了，请换一个名称！'
    if not server_manager.check_online():
        return '当前没有已连接的服务器，绑定失败！请联系管理员连接后再试。'
    if data_manager.append_player(user, player):
        await server_manager.execute(f'{config.whitelist_command} add {player}')
        return f'用户 {session.user.name or user}({user}) 已成功绑定白名单到 {player} 玩家。'
    return '你绑定的玩家个数过多，绑定失败！'


@matcher.assign("append")
async def handle_append(session: Uninfo, user_id: str, player: str):
    """处理 .bound append <user_id> <player>"""
    if not get_permission(session):
        await matcher.finish('你没有权限执行此命令！')
    message = await bound_append_handler(user_id, player)
    await matcher.finish(message)


async def bound_append_handler(user: str, player: str):
    if not check_player(player):
        return '玩家名称非法！玩家名称只能包含字母、数字、下划线且长度不超过 16 个字符。'
    if data_manager.check_player_occupied(player):
        return '此玩家名称已经绑定过了，请换一个名称！'
    if not server_manager.check_online():
        return '当前没有已连接的服务器，绑定失败！请连接后再试。'
    if data_manager.append_player(user, player):
        await server_manager.execute(f'{config.whitelist_command} add {player}')
        return f'用户 ({user}) 已绑定白名单到 {player} 玩家。'
    return '你绑定的玩家个数过多，绑定失败！'


@matcher.assign("list")
async def handle_list(session: Uninfo):
    """处理 .bound list"""
    if not get_permission(session):
        await matcher.finish('你没有权限执行此命令！')
    if data_manager.players:
        message = f'白名单列表：\n' + '\n'.join(f'  {user} -> {"、".join(players)}' for user, players in data_manager.players.items())
        await matcher.finish(message)
    await matcher.finish('当前没有绑定任何玩家！')


@matcher.assign("query")
async def handle_query(session: Uninfo, user_id: Match[str]):
    """处理 .bound query [user_id]"""
    target_user = user_id.result if user_id.available else str(session.user.id)
    if target_user not in data_manager.players:
        await matcher.finish(f'用户 ({target_user}) 还没有绑定白名单！')
    await matcher.finish(f'用户 ({target_user}) 绑定的白名单有 {"、".join(data_manager.players[target_user])} 。')


@matcher.assign("remove")
async def handle_remove(session: Uninfo, user_id: Match[str], player: Match[str]):
    """处理 .bound remove [user_id] [player]"""
    current_user = str(session.user.id)
    # 如果第一个参数是数字且不是当前用户，需要管理员权限
    if user_id.available and user_id.result != current_user and not get_permission(session):
        await matcher.finish('你没有权限执行此命令！')
    # 如果只有一个非数字参数，可能是玩家名（自己解绑自己）
    if user_id.available and not user_id.result.isdigit():
        # 此时 user_id 其实是 player
        message = await bound_remove_handler(session, [], user_id.result)
        await matcher.finish(message)
    # 两个参数
    if user_id.available and player.available:
        message = await bound_remove_admin(session, user_id.result, player.result)
        await matcher.finish(message)
    # 一个数字参数
    if user_id.available and not player.available:
        message = await bound_remove_user(session, user_id.result)
        await matcher.finish(message)
    # 无参数 - 自己解绑全部
    message = await bound_remove_self_all(session)
    await matcher.finish(message)


async def bound_remove_handler(session: Uninfo, args: list, player_name: str = ''):
    if not server_manager.check_online():
        return '当前没有已连接的服务器，请稍后再次尝试！'
    user = str(session.user.id)
    if player_name:
        if await data_manager.remove_player(user, player_name):
            await server_manager.execute(f'{config.whitelist_command} remove {player_name}')
            return f'已移除白名单 {player_name}！'
        return f'你没有绑定名为 {player_name} 的白名单！'
    bounded = await data_manager.remove_player(user)
    if bounded:
        for player in bounded:
            await server_manager.execute(f'{config.whitelist_command} remove {player}')
        return f'已移除所有绑定的白名单！'
    return '你还没有绑定白名单！'


async def bound_remove_user(session: Uninfo, target_user: str):
    if not server_manager.check_online():
        return '当前没有已连接的服务器，请稍后再次尝试！'
    bounded = await data_manager.remove_player(target_user)
    if not bounded:
        return f'用户 ({target_user}) 还没有绑定白名单！'
    for player in bounded:
        await server_manager.execute(f'{config.whitelist_command} remove {player}')
    return f'已移除用户 ({target_user}) 绑定的所有白名单！'


async def bound_remove_admin(session: Uninfo, target_user: str, player_name: str):
    if not server_manager.check_online():
        return '当前没有已连接的服务器，请稍后再次尝试！'
    if target_user not in data_manager.players:
        return f'用户 ({target_user}) 还没有绑定白名单！'
    if await data_manager.remove_player(target_user, player_name):
        await server_manager.execute(f'{config.whitelist_command} remove {player_name}')
        return f'用户 {target_user} 已经从白名单中移除！'
    return f'用户 ({target_user}) 没有绑定名为 {player_name} 的白名单！'


async def bound_remove_self_all(session: Uninfo):
    if not server_manager.check_online():
        return '当前没有已连接的服务器，请稍后再次尝试！'
    user = str(session.user.id)
    bounded = await data_manager.remove_player(user)
    if not bounded:
        return '你还没有绑定白名单！'
    for player in bounded:
        await server_manager.execute(f'{config.whitelist_command} remove {player}')
    return f'已移除所有绑定的白名单！'
