from fastapi import APIRouter, Depends, Query

from Scripts.Config import config
from Scripts.Managers import data_manager
from .Auth import get_current_user, require_role
from .Schemas import BindPlayerRequest

router = APIRouter(prefix='/api/players', tags=['Players'])


@router.get('', summary='获取玩家绑定列表')
async def get_players(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = Query(''),
    current_user: dict = Depends(get_current_user),
):
    '''获取所有玩家绑定关系，支持搜索和分页'''
    all_items = []
    for user_id, players in data_manager.players.items():
        all_items.append({'user': user_id, 'players': players, 'bound_at': ''})

    if keyword:
        keyword_lower = keyword.lower()
        all_items = [
            item for item in all_items
            if keyword_lower in item['user'].lower()
            or any(keyword_lower in p.lower() for p in item['players'])
        ]

    total = len(all_items)
    start = (page - 1) * page_size
    items = all_items[start:start + page_size]
    return {
        'code': 0,
        'data': {'items': items, 'total': total, 'page': page, 'page_size': page_size},
        'message': 'ok',
    }


@router.get('/{user}', summary='查询用户绑定')
async def get_user_bindings(user: str, current_user: dict = Depends(get_current_user)):
    '''查询指定用户的所有绑定'''
    if user not in data_manager.players:
        return {'code': 404, 'data': None, 'message': '用户不存在'}
    return {'code': 0, 'data': {'user': user, 'players': data_manager.players[user]}, 'message': 'ok'}


@router.post('', summary='绑定玩家')
async def bind_player(body: BindPlayerRequest, current_user: dict = Depends(require_role('admin', 'operator'))):
    '''绑定用户与游戏 ID'''
    if not body.user or not body.player:
        return {'code': 1, 'data': None, 'message': 'user 和 player 不能为空'}

    # 检查该游戏 ID 是否已被其他用户绑定
    if await data_manager.check_player_occupied(body.player):
        existing_user = None
        for bound_user, bound_players in data_manager.players.items():
            if body.player.lower() in [p.lower() for p in bound_players]:
                existing_user = bound_user
                break
        if existing_user and existing_user != body.user:
            return {'code': 1, 'data': None, 'message': '该游戏 ID 已被其他用户绑定'}

    # 检查绑定数量上限
    if body.user in data_manager.players:
        if config.qq_bound_max_number > 0 and len(data_manager.players[body.user]) >= config.qq_bound_max_number:
            return {'code': 1, 'data': None, 'message': '绑定数量已达上限'}

    success = await data_manager.append_player(body.user, body.player)
    if not success:
        return {'code': 1, 'data': None, 'message': '绑定数量已达上限'}
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.delete('/{user}/{player}', summary='解除绑定')
async def unbind_player(user: str, player: str, current_user: dict = Depends(require_role('admin', 'operator'))):
    '''解除用户与游戏 ID 的绑定'''
    if user not in data_manager.players:
        return {'code': 404, 'data': None, 'message': '绑定关系不存在'}
    if player not in data_manager.players.get(user, []):
        return {'code': 404, 'data': None, 'message': '绑定关系不存在'}
    await data_manager.remove_player(user, player)
    return {'code': 0, 'data': None, 'message': 'ok'}
