import nonebot
from nonebot.log import logger


class PluginManager:
    '''插件管理器，管理 pyproject.toml 中登记的插件与依赖插件'''

    def load(self):
        '''记录插件管理器已完成初始化。'''
        logger.success('加载插件管理器完毕！')

    def _configured_plugins(self) -> list[dict]:
        '''获取 pyproject.toml 中登记的插件配置。'''
        from Scripts.Managers import environment_manager

        configured_plugins = []
        for plugin in environment_manager.nonebot_config.get('plugins', []):
            if isinstance(plugin, str):
                configured_plugins.append({'module_name': plugin, 'enabled': True})
            elif plugin.get('module_name'):
                configured_plugins.append(plugin)
        return configured_plugins

    @staticmethod
    def _can_disable(module_name: str) -> bool:
        return (
            module_name.startswith('Plugins.Commands.')
            or module_name.startswith('Plugins.Expand.')
            or not module_name.startswith('Plugins.')
        )

    @staticmethod
    def _plugin_info(plugin, configured: dict | None = None) -> dict:
        metadata = plugin.metadata if plugin else None
        if plugin:
            module_name = plugin.module_name
        else:
            assert configured is not None
            module_name = configured['module_name']
        extra = metadata.extra if metadata else {}
        return {
            'name': plugin.name if plugin else module_name.rsplit('.', 1)[-1],
            'module_name': module_name,
            'display_name': metadata.name if metadata else module_name.rsplit('.', 1)[-1],
            'version': extra.get('version', '') if metadata else '',
            'description': metadata.description if metadata else '',
            'author': extra.get('author', '') if metadata else '',
            'homepage': metadata.homepage if metadata else '',
            'enabled': configured.get('enabled', True) if configured else True,
            'type': 'builtin' if module_name.startswith('Plugins.') else 'external',
            'can_disable': PluginManager._can_disable(module_name),
            'dependencies': [],
            'config_schema': {},
        }

    def get_installed_plugins(self) -> list[dict]:
        '''获取登记插件和未登记依赖插件的详细信息。'''
        loaded_plugins = {plugin.module_name: plugin for plugin in nonebot.get_loaded_plugins()}
        plugins = []
        configured_modules = set()
        for configured in self._configured_plugins():
            module_name = configured['module_name']
            configured_modules.add(module_name)
            plugins.append(self._plugin_info(loaded_plugins.get(module_name), configured))
        for module_name, plugin in loaded_plugins.items():
            if module_name not in configured_modules:
                info = self._plugin_info(plugin)
                info['type'] = 'dependency'
                info['can_disable'] = False
                plugins.append(info)
        return plugins

    def get_plugin_detail(self, name: str) -> dict | None:
        '''获取指定插件详情'''
        for plugin in self.get_installed_plugins():
            if plugin['name'] == name or plugin['module_name'] == name:
                return plugin
        return None

    async def set_enabled(self, name: str, enabled: bool) -> bool:
        '''设置可管理插件的启停状态，重启后生效。'''
        plugin = self.get_plugin_detail(name)
        if not plugin or not plugin['can_disable']:
            return False
        from Scripts.Managers import environment_manager

        environment_manager.set_plugin_enabled(plugin['module_name'], enabled)
        return True


plugin_manager = PluginManager()
