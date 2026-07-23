from openai import AsyncClient
from openai import RateLimitError, BadRequestError

from nonebot import on_message
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from nonebot_plugin_alconna import UniMsg
from nonebot_plugin_uninfo import Uninfo

from Scripts.Config import config
from Scripts.Utils import get_permission

__plugin_meta__ = PluginMetadata(
    name='AI 对话',
    description='通过 OpenAI 兼容接口提供上下文对话功能。',
    usage='向机器人发送消息开始对话。',
)

logger.debug('加载 Ai 功能完毕！')
client = AsyncClient(base_url=config.ai.base_url, api_key=config.ai.api_key)
# 保持系统提示 + 最近 10 轮对话
messages: list[dict] = [{'role': 'system', 'content': config.ai.system_prompt}]
MAX_HISTORY = 21

matcher = on_message(rule=to_me(), priority=15, block=False)


@matcher.handle()
async def handle_message(session: Uninfo, msg: UniMsg):
    plain_text = msg.extract_plain_text().strip()
    if plain_text in ('清空缓存', '清除缓存'):
        if not get_permission(session):
            await matcher.finish('你没有权限执行此操作！')
        await clear()
        await matcher.finish('缓存已清空！')
    if plain_text:
        messages.append({'role': 'user', 'content': plain_text})
    try:
        completion = await client.chat.completions.create(
            messages=messages, model=config.ai.model_name, temperature=0.3
        )
    except RateLimitError:
        await matcher.finish('啊哦！你问的太快啦，我的脑袋转不过来了 TwT')
    except BadRequestError as error:
        await matcher.finish(f'啊哦！遇到错误：{error.message}')
    response = completion.choices[0]
    if text := response.message.content:
        messages.append(dict(response.message))
        # 保留系统提示 + 最近 10 轮对话
        if len(messages) > 21:
            messages[:] = [messages[0]] + messages[-20:]
        await matcher.finish(text)
    await matcher.finish('呃？你在说什么，能不能重新说一下 T_T')


async def clear():
    messages.clear()
    messages.append({'role': 'system', 'content': config.ai.system_prompt})
    file_list = await client.files.list()
    for file in file_list.data:
        await client.files.delete(file.id)
