from nonebot.log import logger
from nonebot.adapters.minecraft import Bot as Server

from nonebot_plugin_alconna import Command, Match

from Scripts.Config import config
from Scripts.Globals import render_template
from Scripts.Managers import server_manager
from Scripts.Network import get_player_uuid
from Scripts.Utils import turn_message_text
from Scripts.Rules import command_group_rule

logger.debug('加载命令 List 完毕！')

matcher = Command('list <server?:str>').build(rule=command_group_rule, use_cmd_start=True)


@matcher.handle()
async def handle(server: Match[str]):
    server_flag = server.result if server.available else None
    flag, response = await get_players(server_flag)
    if flag is False:
        await matcher.finish(response)
    if config.image_mode:
        player_uuids = {}
        for players in response.values():
            for player in players[0]:       
                player_uuids[player] = await get_player_uuid(player)
        image = await render_template('List.html', (700, 1000), player_list=response, uuids=player_uuids)
        await matcher.finish(image)
    message = await turn_message_text(list_handler(response))
    await matcher.finish(message)


async def get_player_list(bot: Server):
    '''通过 RCON 命令获取玩家列表'''
    try:
        result = await bot.send_rcon_command(command='list')
    except Exception as e:
        print(e)
        return None
    if not result:
        return None
    # 解析 'There are X of max Y players online: player1, player2, ...'
    if ':' in result:
        players_str = result.split(':')[1].strip()
        if players_str:
            return [p.strip() for p in players_str.split(',')]
    return []


def classify_players(players: list):
    if not config.bot_prefix:
        return (players,)
    fake_players, real_players = [], []
    for player in players:
        if player.upper().startswith(config.bot_prefix):
            fake_players.append(player)
            continue
        real_players.append(player)
    return real_players, fake_players


async def get_players(server_flag: str = ''):
    if not server_manager.servers:
        return False, '当前没有已连接的服务器！'
    if server_flag:
        server = server_manager.get_server(server_flag)
        if server is None:
            return False, f'没有找到已连接的 [{server_flag}] 服务器！请检查编号或名称是否输入正确。'
        players = await get_player_list(server)
        return True, {server.self_id: classify_players(players) if players else ([],)}
    players = {}
    for name, server in server_manager.servers.items():
        result = await get_player_list(server)
        print(f'[{name}] 玩家列表：{result}')
        players[name] = classify_players(result) if result is not None else ([],)
    if not players:
        return False, '当前没有已连接的服务器！'
    return True, players


def list_handler(players: dict):
    if len(players) == 1:
        server_name, players_data = players.popitem()
        online_count = sum(len(p) for p in players_data)
        yield f'===== {server_name} 玩家列表 ====='
        yield from format_players(players_data)
        yield f'当前在线人数共 {online_count} 人'
        return
    player_count = 0
    if players:
        yield '====== 玩家列表 ======'
        for name, value in players.items():
            if value is None:
                continue
            player_count += sum(len(p) for p in value)
            yield f' -------- {name} --------'
            yield from format_players(value)
        yield f'当前在线人数共 {player_count} 人'
        return
    yield '当前没有已连接的服务器！'


def format_players(players: list):
    if config.bot_prefix and len(players) > 1:
        real_players, fake_players = players
        real_players_str = '\n    '.join(real_players)
        fake_players_str = '\n    '.join(fake_players)
        yield '  ———— 玩家 ————'
        if not real_players_str:
            real_players_str = '没有玩家在线！'
        yield '    ' + real_players_str
        yield '  ———— 假人 ————'
        if not fake_players_str:
            fake_players_str = '没有假人在线！'
        yield '    ' + fake_players_str + '\n'
        return
    if grouped := players[0]:
        yield '    ' + '\n    '.join(grouped) + '\n'
        return
    yield '  没有玩家在线！\n'
