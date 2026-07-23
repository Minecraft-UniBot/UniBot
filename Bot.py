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
        try:
            module = importlib.import_module(adapter['module_name'])
        except ImportError:
            logger.warning(f'导入适配器模块 {adapter["module_name"]} 失败，已跳过！')
            continue
        adapter_class = getattr(module, 'Adapter', None)
        if adapter_class is None:
            logger.warning(f'适配器模块 {adapter["module_name"]} 未包含 Adapter 类，已跳过！')
            continue
        driver.register_adapter(adapter_class)
    for plugin in environment_manager.nonebot_config.get('plugins', []):
        module_name = plugin if isinstance(plugin, str) else plugin.get('module_name', '')
        enabled = plugin if isinstance(plugin, str) else plugin.get('enabled', True)
        if module_name and enabled:
            nonebot.load_plugin(module_name)

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
    from Scripts.Config import config
    from Scripts.Api.Limiter import rate_limiter
    from Scripts.Managers import version_manager, server_manager, data_manager, plugin_manager, webui_manager

    await version_manager.init()
    server_manager.init()
    data_manager.load()
    plugin_manager.load()

    if config.webui.enabled:
        await webui_manager.init()
        rate_limiter.start()


@driver.on_shutdown
async def shutdown():
    from Scripts.Api.Limiter import rate_limiter
    from Scripts.Managers import data_manager

    rate_limiter.stop()
    await data_manager.save()


if __name__ == '__main__':
    main()
