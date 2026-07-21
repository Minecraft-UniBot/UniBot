from fastapi import APIRouter, Depends, Query

from Scripts.Managers import plugin_manager
from .Auth import get_current_user, require_role
from .Schemas import InstallPluginRequest, UpgradePluginRequest

router = APIRouter(prefix='/api/plugins', tags=['Plugins'])


@router.get('', summary='获取已安装插件列表')
async def get_plugins(current_user: dict = Depends(get_current_user)):
    '''获取所有已安装插件'''
    return {'code': 0, 'data': plugin_manager.get_installed_plugins(), 'message': 'ok'}


@router.get('/market', summary='插件市场')
async def get_market(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = Query(''),
    category: str = Query(''),
    current_user: dict = Depends(get_current_user),
):
    '''从远程注册表获取可用插件列表'''
    # 插件市场为预留接口，当前返回空列表
    return {
        'code': 0,
        'data': {'items': [], 'total': 0, 'page': page, 'page_size': page_size},
        'message': 'ok',
    }


@router.post('/market/install', summary='安装插件')
async def install_plugin(body: InstallPluginRequest, current_user: dict = Depends(require_role('admin'))):
    '''从市场安装插件'''
    # 预留接口
    return {'code': 1, 'data': None, 'message': '插件市场暂未开放'}


@router.post('/market/upgrade', summary='升级插件')
async def upgrade_plugin(body: UpgradePluginRequest, current_user: dict = Depends(require_role('admin'))):
    '''升级已安装插件'''
    # 预留接口
    return {'code': 1, 'data': None, 'message': '插件市场暂未开放'}


@router.get('/{name}', summary='获取插件详情')
async def get_plugin_detail(name: str, current_user: dict = Depends(get_current_user)):
    '''获取指定插件详情'''
    detail = plugin_manager.get_plugin_detail(name)
    if not detail:
        return {'code': 404, 'data': None, 'message': '插件不存在'}
    return {'code': 0, 'data': detail, 'message': 'ok'}


@router.post('/{name}/enable', summary='启用插件')
async def enable_plugin(name: str, current_user: dict = Depends(require_role('admin'))):
    '''启用插件'''
    success = await plugin_manager.set_enabled(name, True)
    if not success:
        return {'code': 404, 'data': None, 'message': '插件不存在'}
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.post('/{name}/disable', summary='禁用插件')
async def disable_plugin(name: str, current_user: dict = Depends(require_role('admin'))):
    '''禁用插件'''
    success = await plugin_manager.set_enabled(name, False)
    if not success:
        return {'code': 404, 'data': None, 'message': '插件不存在'}
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.delete('/{name}', summary='卸载插件')
async def uninstall_plugin(name: str, current_user: dict = Depends(require_role('admin'))):
    '''卸载插件'''
    # 预留接口
    return {'code': 1, 'data': None, 'message': '暂不支持在线卸载，请手动操作'}
