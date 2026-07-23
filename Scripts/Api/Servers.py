import asyncio

from fastapi import APIRouter, Depends

from nonebot.log import logger

from Scripts.Config import config
from Scripts.Managers import server_manager
from .Auth import get_current_user, require_role
from .Schemas import BroadcastRequest, ExecuteCommandRequest

router = APIRouter(prefix='/api/servers', tags=['Servers'])


def check_command_allowed(command: str) -> bool:
    '''检查指令是否在白名单/黑名单约束内'''
    command_name = command.strip().split()[0].lower() if command.strip() else ''
    if config.command_minecraft_whitelist:
        return command_name in [item.lower() for item in config.command_minecraft_whitelist]
    if config.command_minecraft_blacklist:
        return command_name not in [item.lower() for item in config.command_minecraft_blacklist]
    return True


@router.get('', summary='获取服务器列表')
async def get_servers(current_user: dict = Depends(get_current_user)):
    '''获取所有服务器状态'''
    servers = server_manager.servers or {}
    statuses = await asyncio.gather(*(server_manager.get_status(server) for server in servers.values()))
    server_list = [{'name': name, **status} for name, status in zip(servers, statuses)]
    return {'code': 0, 'data': server_list, 'message': 'ok'}


@router.get('/{name}', summary='获取服务器详情')
async def get_server_detail(name: str, current_user: dict = Depends(get_current_user)):
    '''获取单个服务器详情'''
    servers = server_manager.servers or {}
    if name not in servers:
        return {'code': 404, 'data': None, 'message': f'服务器 [{name}] 不存在'}
    status, player_data = await asyncio.gather(
        server_manager.get_status(servers[name]),
        server_manager.get_player_list(servers[name]),
    )
    players, max_players = player_data
    if not status['max_players']:
        status['max_players'] = max_players
    status['players'] = len(players)
    return {
        'code': 0,
        'data': {
            'name': name,
            **status,
            'player_list': players,
        },
        'message': 'ok',
    }


@router.get('/{name}/players', summary='获取服务器在线玩家')
async def get_server_players(name: str, current_user: dict = Depends(get_current_user)):
    '''获取指定服务器的在线玩家列表'''
    servers = server_manager.servers or {}
    if name not in servers:
        return {'code': 404, 'data': None, 'message': f'服务器 [{name}] 不存在'}
    players, max_players = await server_manager.get_player_list(servers[name])
    return {
        'code': 0,
        'data': {'server': name, 'players': players, 'count': len(players), 'max_players': max_players},
        'message': 'ok',
    }


@router.post('/{name}/execute', summary='执行 RCON 指令')
async def execute_command(name: str, body: ExecuteCommandRequest, current_user: dict = Depends(require_role('admin', 'operator'))):
    '''在指定服务器执行 RCON 指令，name 为 all 时广播'''
    if not body.command:
        return {'code': 1, 'data': None, 'message': '指令不能为空'}
    if not check_command_allowed(body.command):
        return {'code': 1, 'data': None, 'message': '该指令不在允许范围内'}

    servers = server_manager.servers or {}

    if name == 'all':
        results = await server_manager.execute(body.command)
        return {'code': 0, 'data': results or {}, 'message': 'ok'}

    if name not in servers:
        return {'code': 404, 'data': None, 'message': f'服务器 [{name}] 不存在'}

    result = await server_manager.execute(body.command, name)
    response_text = result.get(name, '') if result else ''
    return {'code': 0, 'data': {'response': response_text}, 'message': 'ok'}


@router.post('/broadcast', summary='广播消息')
async def broadcast_message(body: BroadcastRequest, current_user: dict = Depends(require_role('admin', 'operator'))):
    '''广播消息到所有服务器'''
    if not body.message:
        return {'code': 1, 'data': None, 'message': '消息不能为空'}
    await server_manager.broadcast(body.message)
    logger.info(f'WebUI 广播消息：{body.message}')
    return {'code': 0, 'data': None, 'message': 'ok'}
