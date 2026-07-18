import re
from collections.abc import AsyncIterable, Iterable

from .Config import config

regex = re.compile(r'[A-Z0-9_]+|\.[A-Z0-9_]+', re.IGNORECASE)


async def turn_message_text(iterator: AsyncIterable[str] | Iterable[str]) -> str:
    if isinstance(iterator, Iterable):
        return '\n'.join([text for text in iterator])
    return '\n'.join([text async for text in iterator])


def check_player(player: str) -> bool:
    return len(player) <= 16 and get_player_name(player) == player


def check_message(message: str) -> bool:
    return any(word in message for word in config.sync_sensitive_words)


def get_player_name(name: str) -> str | None:
    if result := regex.search(name):
        return result.group()


def get_permission(session) -> bool:
    """检查用户是否为超级用户或管理员"""
    uid = str(session.user.id)
    if uid in config.superusers:
        return True
    if config.admin_superusers and session.member:
        return session.member.role in ('owner', 'admin', 'superuser', 'operator')
    return False
