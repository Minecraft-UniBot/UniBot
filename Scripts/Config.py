from json import loads

from nonebot import get_plugin_config
from pydantic import BaseModel, model_validator


class Config(BaseModel):
    port: int = 8000

    token: str = ''
    bot_prefix: str = ''
    admin_superusers: bool = True

    superusers: list[str] = []
    command_start: list[str] = ['.']
    command_enabled: list[str] = []

    command_groups: list[str] = []
    message_groups: list[str] = []

    command_minecraft_whitelist: list[str] = []
    command_minecraft_blacklist: list[str] = []

    broadcast_server: bool = True
    broadcast_player: bool = True

    sync_all_qq_message: bool = True
    sync_all_game_message: bool = False
    sync_message_between_servers: bool = True

    sync_sensitive_words: list[str] = []

    list_compatible_mode: bool = False

    whitelist_command: str = 'whitelist'

    sync_color_source: str = 'gray'
    sync_color_player: str = 'gray'
    sync_color_message: str = 'gray'

    qq_bound_max_number: int = 1

    image_mode: bool = False
    image_background: str = None

    ai_enabled: bool = False
    ai_api_key: str = None
    ai_base_url: str = None
    ai_system_prompt: str = None
    ai_model_name: str = None

    auto_reply_enabled: bool = False
    auto_reply_keywords: dict[str, list[str]] = None

    api_enabled: bool = False
    api_token: str = None

    # Minecraft adapter config
    minecraft_ws_urls: dict[str, list[str]] = {}
    minecraft_access_token: str | None = None

    @model_validator(mode='before')
    @classmethod
    def _parse_json_strings(cls, data):
        if not isinstance(data, dict):
            return data
        for field in ('minecraft_ws_urls', 'auto_reply_keywords'):
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = loads(data[field])
                except (TypeError, ValueError):
                    pass
        return data

    @model_validator(mode='after')
    def _normalize(self):
        self.bot_prefix = self.bot_prefix.upper() if self.bot_prefix else None
        if 'about' not in self.command_enabled:
            self.command_enabled.append('about')
        if self.sync_all_qq_message and 'send' in self.command_enabled:
            self.command_enabled.remove('send')
        return self


config = get_plugin_config(Config)

