from arclet.alconna import Alconna, Subcommand, command_manager
from arclet.alconna.args import Args
from nonebot.log import logger
from nonebot_plugin_alconna import Command, Match
from nonebot_plugin_alconna.uniseg import Image, UniMessage

from Scripts.Config import config
from Scripts.Globals import render_template
from Scripts.Utils import turn_message_text
from Scripts.Rules import command_group_rule

logger.debug('加载命令 Help 完毕！')

matcher = (
    Command('help <command?#命令名称:str>', '查看所有可用命令的帮助信息。')
    .build(rule=command_group_rule, use_cmd_start=True)
)


@matcher.handle()
async def handle(command: Match[str]):
    if config.image_mode:
        if command.available:
            detail = get_command_detail(command.result)
            image = await render_template('Help', (600, 800), detail=detail, commands=None)
        else:
            commands = get_commands_list()
            image = await render_template('Help', (600, 800), detail=None, commands=commands)
        await matcher.finish(UniMessage(Image(raw=image)))
    if command.available:
        message = await turn_message_text(detailed_handler(command.result))
        await matcher.finish(message)
    message = await turn_message_text(help_handler())
    await matcher.finish(message)


def get_commands_list() -> list[dict]:
    """构建命令列表数据用于图片渲染"""
    commands = []
    for name in config.command_enabled:
        alconna = get_alconna(name)
        if alconna is None:
            continue
        usage = alconna.meta.usage or gen_usage(alconna)
        description = alconna.meta.description or ''
        subcommands = [option for option in alconna.options if isinstance(option, Subcommand)]
        sub_list = []
        for index, subcommand in enumerate(subcommands):
            branch = '└─' if index == len(subcommands) - 1 else '├─'
            sub_desc = f' — {subcommand.help_text}' if subcommand.help_text else ''
            sub_list.append(f'{branch} {subcommand.name}{sub_desc}')
        commands.append({'usage': usage, 'description': description, 'subcommands': sub_list})
    return commands


def get_command_detail(name: str) -> dict | None:
    """构建命令详情数据用于图片渲染"""
    if name not in config.command_enabled:
        return None
    alconna = get_alconna(name)
    if alconna is None:
        return None
    args_list = []
    if isinstance(alconna.args, Args):
        args_list = [{'name': arg.name, 'notice': arg.notice} for arg in alconna.args if arg.notice]
    subcommands = [option for option in alconna.options if isinstance(option, Subcommand)]
    sub_list = [{'name': sub.name, 'usage': sub_usage(sub), 'description': sub.help_text or ''} for sub in subcommands]
    return {
        'name': name,
        'usage': alconna.meta.usage or gen_usage(alconna),
        'description': alconna.meta.description or '',
        'args': args_list,
        'subcommands': sub_list,
    }


def get_alconna(name: str):
    """从 command_manager 中获取已注册的 Alconna 对象。"""
    for command in command_manager.get_commands():
        if command.command == name:
            return command
    return None


def gen_usage(alconna: Alconna):
    """根据 Alconna 对象自动生成用法字符串。"""
    parts = [alconna.command]
    if isinstance(alconna.args, Args):
        for arg in alconna.args:
            parts.append(f'<*{arg.name}>' if arg.optional else f'<{arg.name}>')
    return ' '.join(parts)


def sub_usage(subcommand: Subcommand):
    """根据子命令的参数构造用法字符串。"""
    parts = [subcommand.name]
    if isinstance(subcommand.args, Args):
        for arg in subcommand.args:
            parts.append(f'<*{arg.name}>' if arg.optional else f'<{arg.name}>')
    return ' '.join(parts)


def help_handler():
    yield '命令列表：'
    for name in config.command_enabled:
        alconna = get_alconna(name)
        if alconna is None:
            continue
        usage = alconna.meta.usage or gen_usage(alconna)
        description = alconna.meta.description or ''
        yield f'    {usage} — {description}'
        subcommands = [option for option in alconna.options if isinstance(option, Subcommand)]
        for index, subcommand in enumerate(subcommands):
            branch = '└─' if index == len(subcommands) - 1 else '├─'
            subcommand_description = f' — {subcommand.help_text}' if subcommand.help_text else ''
            yield f'    {branch} {subcommand.name}{subcommand_description}'
    yield '\n注：<name> 代表必填的参数，<*name> 代表此参数可选。'


def detailed_handler(name: str):
    if name not in config.command_enabled:
        yield f'命令 {name} 不存在或已被禁用！'
        return
    alconna = get_alconna(name)
    if alconna is None:
        yield f'命令 {name} 不存在或已被禁用！'
        return
    yield f'命令 {name} 的详细信息：'
    yield f'    用法：{alconna.meta.usage or gen_usage(alconna)}'
    if alconna.meta.description:
        yield f'    描述：{alconna.meta.description}'
    if isinstance(alconna.args, Args):
        notices = [arg for arg in alconna.args if arg.notice]
        if notices:
            yield '    参数：'
            for arg in notices:
                yield f'        {arg.name} — {arg.notice}'
    subcommands = [option for option in alconna.options if isinstance(option, Subcommand)]
    if not subcommands:
        return
    yield '    子命令：'
    for index, subcommand in enumerate(subcommands):
        branch = '└─' if index == len(subcommands) - 1 else '├─'
        continuation = '    ' if index == len(subcommands) - 1 else '│   '
        subcommand_description = f' — {subcommand.help_text}' if subcommand.help_text else ''
        yield f'        {branch} {sub_usage(subcommand)}{subcommand_description}'
        if not isinstance(subcommand.args, Args):
            continue
        for arg in subcommand.args:
            if arg.notice:
                yield f'        {continuation}    {arg.name} — {arg.notice}'
