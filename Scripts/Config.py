from pathlib import Path
from tomllib import load

from nonebot import get_plugin_config
from pydantic import BaseModel, model_validator

TOML_PATH = Path('Config.toml')


class ImageConfig(BaseModel):
    mode: bool = False
    background: str | None = None


class AiConfig(BaseModel):
    enabled: bool = False
    base_url: str | None = None
    model_name: str | None = None
    api_key: str | None = None
    system_prompt: str | None = None


class AutoReplyConfig(BaseModel):
    enabled: bool = False
    keywords: dict[str, list[str]] | None = None


class WebUiConfig(BaseModel):
    enabled: bool = False


class Config(BaseModel):
    # NoneBot 内置配置（从 .env / 环境变量读取）
    port: int = 8000
    superusers: list[str] = []
    command_start: list[str] = ['.']

    # 自定义配置（从 config.toml 读取）
    token: str = ''
    bot_prefix: str = ''
    admin_superusers: bool = True

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

    server_memory_update_interval: int = 5
    server_memory_max_cache: int = 200

    image: ImageConfig = ImageConfig()
    ai: AiConfig = AiConfig()
    auto_reply: AutoReplyConfig = AutoReplyConfig()
    webui: WebUiConfig = WebUiConfig()

    @model_validator(mode='after')
    def normalize(self):
        self.bot_prefix = self.bot_prefix.upper() if self.bot_prefix else ''
        if 'about' not in self.command_enabled:
            self.command_enabled.append('about')
        if self.sync_all_qq_message and 'send' in self.command_enabled:
            self.command_enabled.remove('send')
        return self


with open(TOML_PATH, 'rb') as f:
    toml_data = load(f)

merged = get_plugin_config(Config).model_dump()
merged.update(toml_data)

config = Config.model_validate(merged)

