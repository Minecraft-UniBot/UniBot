from asyncio import Lock
from json import loads, dump
from pathlib import Path

import nonebot
from nonebot.log import logger


class PluginManager:
    '''插件管理器，管理已安装插件的启停状态与市场交互'''

    plugin_states: dict[str, bool] = {}

    data_dir = Path('Data')
    plugins_file = data_dir / 'Plugins.json'

    lock = Lock()

    def load(self):
        '''加载插件启停状态'''
        if self.plugins_file.exists():
            try:
                self.plugin_states = loads(self.plugins_file.read_text('Utf-8'))
            except Exception:
                logger.warning('插件状态文件损坏，使用空数据！')
                self.plugin_states = {}
        logger.success('加载插件状态完毕！')

    async def save(self):
        '''持久化插件启停状态'''
        async with self.lock:
            with self.plugins_file.open('w', encoding='Utf-8') as file:
                dump(self.plugin_states, file, ensure_ascii=False, indent=2)

    def get_installed_plugins(self) -> list[dict]:
        '''获取所有已安装插件信息'''
        plugins = []
        for plugin in nonebot.get_loaded_plugins():
            metadata = plugin.metadata
            name = plugin.name
            enabled = self.plugin_states.get(name, True)
            plugins.append({
                'name': name,
                'display_name': metadata.name if metadata else name,
                'version': metadata.extra.get('version', '') if metadata else '',
                'description': metadata.description if metadata else '',
                'author': metadata.extra.get('author', '') if metadata else '',
                'enabled': enabled,
                'type': 'plugin',
            })
        return plugins

    def get_plugin_detail(self, name: str) -> dict | None:
        '''获取指定插件详情'''
        plugin = nonebot.get_plugin(name)
        if not plugin:
            return None
        metadata = plugin.metadata
        enabled = self.plugin_states.get(name, True)
        return {
            'name': name,
            'display_name': metadata.name if metadata else name,
            'version': metadata.extra.get('version', '') if metadata else '',
            'description': metadata.description if metadata else '',
            'author': metadata.extra.get('author', '') if metadata else '',
            'homepage': metadata.homepage if metadata else '',
            'enabled': enabled,
            'type': 'plugin',
            'dependencies': [],
            'config_schema': {},
        }

    async def set_enabled(self, name: str, enabled: bool) -> bool:
        '''设置插件启停状态'''
        plugin = nonebot.get_plugin(name)
        if not plugin:
            return False
        self.plugin_states[name] = enabled
        await self.save()
        return True


plugin_manager = PluginManager()
