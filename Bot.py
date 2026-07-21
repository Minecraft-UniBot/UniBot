import importlib
from pathlib import Path

import nonebot
from nonebot.log import logger

nonebot.init()
driver = nonebot.get_driver()

def main():
    from Scripts.Config import config as bot_config
    from Scripts.Managers.Environment import environment_manager
    
    # 提前加载 .env 和 pyproject.toml 配置（适配器注册、插件加载需要）
    environment_manager.init()

    for adapter in environment_manager.nonebot_config.get('adapters', []):
        module = importlib.import_module(adapter['module_name'])
        driver.register_adapter(getattr(module, 'Adapter'))
    for plugin in environment_manager.nonebot_config.get('plugins', []):
        nonebot.load_plugin(plugin)
    for plugin_dir in environment_manager.nonebot_config.get('plugin_dirs', []):
        nonebot.load_plugins(plugin_dir)

    # 挂载 WebUI API 路由（需在 nonebot.init() 之后、nonebot.run() 之前）

    if bot_config.webui.enabled:
        from fastapi import FastAPI
        from Scripts.Api import api_router, setup_cors
        from Scripts.Api.Ws import log_sink

        app: FastAPI = nonebot.get_app()
        setup_cors(app)
        app.include_router(api_router)
        logger.add(log_sink, level='DEBUG', format='{time:HH:mm:ss} | {level} | {message}')
        logger.success('WebUI API 路由挂载完毕！')
    
    log_path = Path('./Logs/')
    if not log_path.exists():
        log_path.mkdir()
    logger.add((log_path / '{time}.log'), rotation='1 day')

    nonebot.run()


@driver.on_startup
async def startup():
    from Scripts.Managers import version_manager, server_manager, data_manager, plugin_manager, environment_manager

    await version_manager.init()
    server_manager.init()
    data_manager.load()
    plugin_manager.load()


@driver.on_shutdown
async def shutdown():
    from Scripts.Managers import data_manager

    await data_manager.save()


if __name__ == '__main__':
    main()
