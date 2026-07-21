from copy import deepcopy

import tomlkit
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from Scripts.Config import TOML_PATH, Config, config
from Scripts.Managers import environment_manager
from .Auth import get_current_user, require_role

router = APIRouter(prefix='/api/config', tags=['Config'])


def deep_merge(base: dict, override: dict) -> dict:
    '''递归深合并两个字典，override 中的值覆盖 base'''
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def mask_api_key(data: dict) -> dict:
    '''对 ai.api_key 进行脱敏处理'''
    result = deepcopy(data)
    ai_config = result.get('ai', {})
    api_key = ai_config.get('api_key', '')
    if api_key:
        ai_config['api_key'] = api_key[:4] + '****'
    return result


@router.get('', summary='获取配置')
async def get_config(current_user: dict = Depends(get_current_user)):
    '''获取完整配置（api_key 脱敏）'''
    config_data = config.model_dump()
    return {
        'code': 0,
        'data': mask_api_key(config_data),
        'message': 'ok',
    }


@router.get('/schema', summary='获取配置 Schema')
async def get_config_schema(current_user: dict = Depends(get_current_user)):
    '''获取配置的 JSON Schema，供前端动态渲染表单'''
    return {
        'code': 0,
        'data': {
            'fields': [
                {'key': 'token', 'label': '连接密钥', 'type': 'secret', 'default': '', 'description': '防止未授权连接的密钥'},
                {'key': 'admin_superusers', 'label': '管理员视为超管', 'type': 'boolean', 'default': True, 'description': '是否将所有的管理员视为超级用户'},
                {'key': 'bot_prefix', 'label': '假人前缀', 'type': 'string', 'default': '', 'description': '假人前缀，用于 list 指令分类'},
                {'key': 'command_enabled', 'label': '启用的指令', 'type': 'list', 'default': [], 'description': '启用的指令列表'},
                {'key': 'command_groups', 'label': '指令群', 'type': 'list', 'default': [], 'description': '机器人只响应这些群的指令'},
                {'key': 'message_groups', 'label': '消息群', 'type': 'list', 'default': [], 'description': '消息同步的 QQ 群'},
                {'key': 'command_minecraft_whitelist', 'label': 'Minecraft 指令白名单', 'type': 'list', 'default': [], 'description': '允许执行的指令白名单'},
                {'key': 'command_minecraft_blacklist', 'label': 'Minecraft 指令黑名单', 'type': 'list', 'default': [], 'description': '禁止执行的指令黑名单'},
                {'key': 'broadcast_server', 'label': '播报服务器开关', 'type': 'boolean', 'default': True, 'description': '是否播报服务器开启/关闭'},
                {'key': 'broadcast_player', 'label': '播报玩家进出', 'type': 'boolean', 'default': True, 'description': '是否播报玩家进入/离开服务器'},
                {'key': 'sync_all_qq_message', 'label': '同步所有 QQ 消息', 'type': 'boolean', 'default': True, 'description': '是否把消息群内的所有消息转发到服务器内'},
                {'key': 'sync_all_game_message', 'label': '同步所有游戏消息', 'type': 'boolean', 'default': False, 'description': '是否转发所有服务器内消息到 QQ 群'},
                {'key': 'sync_message_between_servers', 'label': '服务器间消息同步', 'type': 'boolean', 'default': False, 'description': '是否把服务器内的消息转发到其他服务器'},
                {'key': 'sync_sensitive_words', 'label': '敏感词列表', 'type': 'list', 'default': [], 'description': '含有敏感词的消息不会被同步'},
                {'key': 'sync_color_source', 'label': '来源颜色', 'type': 'string', 'default': 'gray', 'description': '转发消息的来源颜色'},
                {'key': 'sync_color_player', 'label': '玩家颜色', 'type': 'string', 'default': 'gray', 'description': '转发消息的玩家名颜色'},
                {'key': 'sync_color_message', 'label': '消息颜色', 'type': 'string', 'default': 'gray', 'description': '转发消息的内容颜色'},
                {'key': 'qq_bound_max_number', 'label': '绑定上限', 'type': 'number', 'default': 1, 'description': '绑定 QQ 号的最大数量，0 表示不限制'},
                {'key': 'list_compatible_mode', 'label': '兼容模式', 'type': 'boolean', 'default': False, 'description': '通过监听进出更新玩家列表'},
                {'key': 'whitelist_command', 'label': '白名单指令', 'type': 'string', 'default': 'whitelist', 'description': '白名单的指令名称'},
                {'key': 'image.mode', 'label': '图片模式', 'type': 'boolean', 'default': False, 'description': '是否启用图片渲染'},
                {'key': 'image.background', 'label': '背景图片', 'type': 'string', 'default': '', 'description': '图片渲染的背景 CSS'},
                {'key': 'ai.enabled', 'label': '启用 AI', 'type': 'boolean', 'default': False, 'description': '是否启用 AI 功能'},
                {'key': 'ai.base_url', 'label': 'AI Base URL', 'type': 'string', 'default': '', 'description': 'OpenAI 兼容格式的 BaseUrl'},
                {'key': 'ai.model_name', 'label': 'AI 模型名称', 'type': 'string', 'default': '', 'description': '模型的名称'},
                {'key': 'ai.api_key', 'label': 'AI API Key', 'type': 'secret', 'default': '', 'description': 'OpenAI 兼容格式的 ApiKey'},
                {'key': 'ai.system_prompt', 'label': 'AI 提示词', 'type': 'string', 'default': '', 'description': 'AI 的系统提示词'},
                {'key': 'webui.enabled', 'label': '启用 WebUI', 'type': 'boolean', 'default': False, 'description': '是否开启 WebUI 管理面板'},
            ],
            'groups': [
                {'name': '基础', 'keys': ['token', 'admin_superusers', 'bot_prefix']},
                {'name': '指令', 'keys': ['command_enabled', 'command_groups', 'command_minecraft_whitelist', 'command_minecraft_blacklist']},
                {'name': '消息同步', 'keys': ['broadcast_server', 'broadcast_player', 'sync_all_qq_message', 'sync_all_game_message', 'sync_message_between_servers', 'sync_sensitive_words', 'sync_color_source', 'sync_color_player', 'sync_color_message']},
                {'name': '玩家', 'keys': ['qq_bound_max_number', 'list_compatible_mode', 'whitelist_command']},
                {'name': '图片渲染', 'keys': ['image.mode', 'image.background']},
                {'name': 'AI', 'keys': ['ai.enabled', 'ai.base_url', 'ai.model_name', 'ai.api_key', 'ai.system_prompt']},
                {'name': 'WebUI', 'keys': ['webui.enabled']},
            ],
        },
        'message': 'ok',
    }


@router.patch('', summary='更新配置')
async def patch_config(request: Request, current_user: dict = Depends(require_role('admin'))):
    '''部分更新配置，深合并后写回 Config.toml 并热更新'''
    try:
        patch_data = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}

    current_data = config.model_dump()
    merged_data = deep_merge(current_data, patch_data)

    # 写回 TOML 文件
    toml_output = deepcopy(merged_data)
    # 移除 NoneBot 内置配置字段（这些在 .env 中管理）
    for key in ('port', 'superusers', 'command_start'):
        toml_output.pop(key, None)

    # tomlkit 不支持 None 值，替换为空字符串
    def sanitize_none(data: dict) -> dict:
        result = {}
        for key, value in data.items():
            if value is None:
                result[key] = ''
            elif isinstance(value, dict):
                result[key] = sanitize_none(value)
            else:
                result[key] = value
        return result

    try:
        # 读取现有文件以保留注释和格式
        try:
            with open(TOML_PATH, 'r', encoding='utf-8') as file:
                toml_document = tomlkit.parse(file.read())
        except FileNotFoundError:
            toml_document = tomlkit.document()

        # 逐键更新，保留原有注释
        sanitized = sanitize_none(toml_output)
        for key, value in sanitized.items():
            if isinstance(value, dict) and key in toml_document and isinstance(toml_document[key], dict):
                for sub_key, sub_value in value.items():
                    toml_document[key][sub_key] = sub_value
            else:
                toml_document[key] = value

        with open(TOML_PATH, 'w', encoding='utf-8') as file:
            file.write(tomlkit.dumps(toml_document))
    except Exception as error:
        return {'code': 500, 'data': None, 'message': f'写入配置文件失败：{error}'}

    # 热更新内存中的配置对象（先经模型校验，保证嵌套配置仍为 Pydantic 子模型而非 dict）
    updated_config = Config.model_validate(merged_data)
    for field_name in Config.model_fields:
        setattr(config, field_name, getattr(updated_config, field_name))

    return {'code': 0, 'data': None, 'message': 'ok'}


# ===== .env 环境变量配置 =====

ENV_SCHEMA = [
    {'key': 'PORT', 'label': '监听端口', 'type': 'number', 'default': 8000, 'description': 'NoneBot 监听的端口'},
    {'key': 'HOST', 'label': '监听地址', 'type': 'string', 'default': '127.0.0.1', 'description': 'NoneBot 监听的 IP / 主机名，公网连接请改为 0.0.0.0'},
    {'key': 'SUPERUSERS', 'label': '超级用户', 'type': 'list', 'default': [], 'description': '拥有管理权限的用户的 QQ 号'},
    {'key': 'COMMAND_SEP', 'label': '命令分隔符', 'type': 'list', 'default': [' '], 'description': 'NoneBot 命令分隔字符'},
    {'key': 'COMMAND_START', 'label': '命令起始符', 'type': 'list', 'default': ['.'], 'description': 'NoneBot 命令起始字符'},
    {'key': 'LOG_LEVEL', 'label': '日志等级', 'type': 'string', 'default': 'INFO', 'description': '日志输出等级'},
    {'key': 'ONEBOT_ACCESS_TOKEN', 'label': 'OneBot AccessToken', 'type': 'secret', 'default': '', 'description': 'OneBot 平台的 AccessToken'},
    {'key': 'MINECRAFT_WS_URLS', 'label': 'Minecraft WS 地址', 'type': 'string', 'default': '', 'description': 'Minecraft 服务器 WebSocket 连接地址（JSON 格式）'},
    {'key': 'MINECRAFT_ACCESS_TOKEN', 'label': 'Minecraft 令牌', 'type': 'secret', 'default': '', 'description': 'Minecraft WebSocket 连接令牌'},
]

ENV_GROUPS = [
    {'name': '框架', 'keys': ['PORT', 'HOST', 'SUPERUSERS', 'COMMAND_SEP', 'COMMAND_START', 'LOG_LEVEL']},
    {'name': '适配器', 'keys': ['ONEBOT_ACCESS_TOKEN', 'MINECRAFT_WS_URLS', 'MINECRAFT_ACCESS_TOKEN']},
]


@router.get('/env', summary='获取环境变量配置')
async def get_env_config(current_user: dict = Depends(get_current_user)):
    '''获取 .env 中的配置项'''
    return {
        'code': 0,
        'data': {
            'values': environment_manager.read_env(),
            'schema': ENV_SCHEMA,
            'groups': ENV_GROUPS,
        },
        'message': 'ok',
    }


@router.patch('/env', summary='更新环境变量配置')
async def patch_env_config(request: Request, current_user: dict = Depends(require_role('admin'))):
    '''部分更新 .env 配置，写回文件（需重启生效）'''
    try:
        patch_data = await request.json()
    except Exception:
        return {'code': 1, 'data': None, 'message': '请求体格式错误'}
    environment_manager.update_env(patch_data)
    return {'code': 0, 'data': None, 'message': 'ok（重启后生效）'}


# ===== pyproject.toml NoneBot 插件/适配器管理 =====


class NoneBotItemRequest(BaseModel):
    name: str
    module_name: str


@router.get('/nonebot', summary='获取 NoneBot 插件与适配器列表')
async def get_nonebot_config(current_user: dict = Depends(get_current_user)):
    '''获取 pyproject.toml 中的 NoneBot 适配器和插件配置'''
    project_data = environment_manager.read_pyproject()
    nonebot_section = project_data.get('tool', {}).get('nonebot', {})
    return {
        'code': 0,
        'data': {
            'adapters': nonebot_section.get('adapters', []),
            'plugins': nonebot_section.get('plugins', []),
            'plugin_dirs': nonebot_section.get('plugin_dirs', []),
        },
        'message': 'ok',
    }


@router.post('/nonebot/adapters', summary='添加适配器')
async def add_adapter(body: NoneBotItemRequest, current_user: dict = Depends(require_role('admin'))):
    '''向 pyproject.toml 添加适配器'''
    if environment_manager.add_adapter(body.name, body.module_name):
        return {'code': 0, 'data': None, 'message': 'ok（重启后生效）'}
    return {'code': 1, 'data': None, 'message': '该适配器已存在'}


@router.delete('/nonebot/adapters', summary='移除适配器')
async def remove_adapter(body: NoneBotItemRequest, current_user: dict = Depends(require_role('admin'))):
    '''从 pyproject.toml 移除适配器'''
    environment_manager.remove_adapter(body.module_name)
    return {'code': 0, 'data': None, 'message': 'ok（重启后生效）'}


@router.post('/nonebot/plugins', summary='添加插件')
async def add_plugin(body: NoneBotItemRequest, current_user: dict = Depends(require_role('admin'))):
    '''向 pyproject.toml 添加插件'''
    if environment_manager.add_plugin(body.module_name):
        return {'code': 0, 'data': None, 'message': 'ok（重启后生效）'}
    return {'code': 1, 'data': None, 'message': '该插件已存在'}


@router.delete('/nonebot/plugins', summary='移除插件')
async def remove_plugin(body: NoneBotItemRequest, current_user: dict = Depends(require_role('admin'))):
    '''从 pyproject.toml 移除插件'''
    environment_manager.remove_plugin(body.module_name)
    return {'code': 0, 'data': None, 'message': 'ok（重启后生效）'}
