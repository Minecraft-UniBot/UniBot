import importlib
from pathlib import Path

import nonebot
from nonebot.log import logger

nonebot.init()
driver = nonebot.get_driver()

def main():
    from Scripts.Config import config as bot_config
    from Scripts.Managers import environment_manager, webui_manager
    
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
        webui_manager.mount(nonebot.get_app())
    
    log_path = Path('./Logs/')
    if not log_path.exists():
        log_path.mkdir()
    logger.add((log_path / '{time}.log'), rotation='1 day')

    nonebot.run()


@driver.on_startup
async def startup():
    from Scripts.Config import config as bot_config
    from Scripts.Managers import version_manager, server_manager, data_manager, plugin_manager, webui_manager

    await version_manager.init()
    server_manager.init()
    data_manager.load()
    plugin_manager.load()

    if bot_config.webui.enabled:
        await webui_manager.init()


@driver.on_shutdown
async def shutdown():
    from Scripts.Managers import data_manager

    await data_manager.save()


if __name__ == '__main__':
    main()
