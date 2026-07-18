from nonebot.log import logger
from nonebot_plugin_alconna import on_alconna, Match
from nonebot_plugin_uninfo import Uninfo
from arclet.alconna import Alconna, Args

from Scripts.Config import config
from Scripts.Managers import data_manager
from Scripts.Utils import turn_message_text

logger.debug('加载命令 Help 完毕！')

matcher = on_alconna(
    Alconna("help", Args["command?", str]),
    use_cmd_start=True,
)


@matcher.handle()
async def handle(session: Uninfo, command: Match[str]):
    if command.available:
        message = await turn_message_text(detailed_handler(command.result))
    else:
        message = await turn_message_text(help_handler())
    await matcher.finish(message)


def help_handler():
    yield '命令列表：'
    for name in config.command_enabled:
        info = data_manager.commands[name]
        yield f'  {name} — {data_manager.commands[name]["description"]}'
        if children := info.get('children'):
            for child_name, child_info in children.items():
                yield f'  +-- {name} {child_name} — {child_info["description"]}'
    yield '\n注：<name> 代表必填的参数，<*name> 代表此参数可选。'


def detailed_handler(name: str):
    if name in config.command_enabled:
        info = data_manager.commands[name]
        yield f'命令 {name} 的详细信息：'
        yield from format_info(info)
        if children := info.get('children'):
            for child_name, child_info in children.items():
                yield f'  +-- 子命令 {child_name}'
                yield from format_info(child_info, prefix='  ')
        return
    yield f'命令 {name} 不存在或已被禁用！'


def format_info(info: dict, prefix: str = ''):
    if parameters := info.get('parameters'):
        yield f'{prefix}  参数说明：'
        for parameter, usage in parameters.items():
            yield f'{prefix}    +-- {parameter} — {usage}'
