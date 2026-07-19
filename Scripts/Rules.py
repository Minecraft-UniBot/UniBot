from .Config import config
from nonebot import require
from nonebot.rule import Rule

require('nonebot_plugin_uninfo')
from nonebot_plugin_uninfo import Uninfo, SupportScope


def is_message_group(session: Uninfo):
    scope = SupportScope(session.scope)
    group_info = f'{scope.name}:{session.id}'
    return group_info in config.message_groups


def is_command_group(session: Uninfo):
    scope = SupportScope(session.scope)
    group_info = f'{scope.name}:{session.scene.id}'
    return group_info in config.command_groups


message_group_rule = Rule(is_message_group)
command_group_rule = Rule(is_command_group)
