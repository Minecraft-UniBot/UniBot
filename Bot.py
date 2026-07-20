import asyncio
import tomllib
import importlib
from pathlib import Path

import nonebot
from nonebot.log import logger

nonebot.init()

driver = nonebot.get_driver()

with open('pyproject.toml', 'rb') as file:
    config = tomllib.load(file)['tool']['nonebot']

for adapter in config.get('adapters', []):
    module = importlib.import_module(adapter['module_name'])
    driver.register_adapter(getattr(module, 'Adapter'))

for plugin in config.get('plugins', []):
    nonebot.load_plugin(plugin)

for plugin_dir in config.get('plugin_dirs', []):
    nonebot.load_plugins(plugin_dir)


def main():
    log_path = Path('./Logs/')
    if not log_path.exists():
        log_path.mkdir()
    logger.add((log_path / '{time}.log'), rotation='1 day')

    nonebot.run()


@driver.on_startup
async def startup():
    from Scripts.Managers import version_manager, server_manager, data_manager

    await version_manager.init()
    server_manager.init()
    data_manager.load()


@driver.on_shutdown
def shutdown():
    from Scripts.Managers import data_manager

    asyncio.run(data_manager.save())


if __name__ == '__main__':
    main()
