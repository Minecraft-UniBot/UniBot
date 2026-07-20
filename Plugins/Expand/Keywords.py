from nonebot import on_message
from nonebot.log import logger
from nonebot_plugin_alconna import UniMsg

from Scripts.Config import config

logger.debug('加载 关键词回复 功能完毕！')
matcher = on_message(priority=15, block=False)


@matcher.handle()
async def watch_keywords(msg: UniMsg):
    plain_text = msg.extract_plain_text()
    for reply_text, keywords in config.auto_reply.keywords.items():
        for keyword in keywords:
            if all(word in plain_text for word in keyword.split()):
                await matcher.finish(reply_text)
