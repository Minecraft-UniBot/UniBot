import asyncio
from pathlib import Path

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotAdapter
from nonebot.adapters.minecraft import Adapter as MinecraftAdapter
from nonebot.log import logger

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(OneBotAdapter)
driver.register_adapter(MinecraftAdapter)

nonebot.load_plugins('Plugins')


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
