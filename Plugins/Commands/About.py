from nonebot.log import logger
from nonebot_plugin_alconna import Command

from Scripts.Managers.Version import version_manager
from Scripts.Utils import turn_message_text

logger.debug('加载命令 About 完毕！')

matcher = Command('about').build(use_cmd_start=True)


@matcher.handle()
async def handle():
    message = await turn_message_text(about_handler())
    await matcher.finish(message)


async def about_handler():
    yield f'当前版本为 {version_manager.version}，{'发现新版本，请及时更新！' if version_manager.check_update() else '已是最新版本！'}'
    yield '\n项目官网：https://qqbot.bugjump.xyz/'
    yield '项目地址 https://github.com/Minecraft-QQBot'
    yield '欢迎加入 QQ 交流群 962802248，对这个项目感兴趣不妨点个 Star 吧！'
