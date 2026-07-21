import sys
import tomlkit
from pathlib import Path
from json import JSONDecodeError, loads, dumps

from nonebot.log import logger


class EnvironmentManager:
    mapping: list = []
    environment: dict = {}

    env_path: Path = Path('.env')
    pyproject_path: Path = Path('pyproject.toml')

    # pyproject.toml 数据
    version: str = ''
    webui_version: str = ''
    nonebot_config: dict = {}

    def init(self):
        '''加载 .env 和 pyproject.toml 配置'''
        self.load_env()
        self.load_pyproject()

    def load_env(self):
        '''加载 .env 配置文件'''
        if not self.env_path.exists():
            logger.error('没有找到配置文件！请重新下载后重试。')
            sys.exit(1)
        file_content = self.env_path.read_text('Utf-8')
        for line in file_content.split('\n'):
            line = line.strip()
            if line.startswith('#') or (not line):
                self.mapping.append(line)
                continue
            key, value = line.split('=', 1)
            key, value = key.strip(), value.strip()
            try:
                value = loads(value)
            except JSONDecodeError:
                pass
            self.environment[key] = value
            self.mapping.append(key)
        logger.success('预加载配置文件完毕！文件已载入到内存中。')

    def load_pyproject(self):
        '''加载 pyproject.toml 配置（版本号、NoneBot 适配器/插件等）'''
        if not self.pyproject_path.exists():
            logger.error('没有找到 pyproject.toml！请重新下载后重试。')
            sys.exit(1)
        with self.pyproject_path.open('r', encoding='utf-8') as file:
            data = tomlkit.parse(file.read())
        self.version = data.get('project', {}).get('version', '')
        self.webui_version = data.get('unibot', {}).get('webui_version', '')
        self.nonebot_config = data.get('tool', {}).get('nonebot', {})
        logger.success('加载 pyproject.toml 完毕！')

    # ===== .env 操作 =====

    def read_env(self) -> dict:
        '''获取 .env 配置字典'''
        return self.environment

    def update_env(self, new: dict):
        '''更新 .env 配置并写回文件'''
        logger.info(f'正在更新配置 {new}')
        for key, value in new.items():
            self.environment[key] = value
            if key not in self.mapping:
                self.mapping.append(key)
        self.write_env()

    def write_env(self):
        '''将 .env 配置写回文件'''
        logger.info('正在写入配置……')
        lines = []
        for line in self.mapping:
            if line.startswith('#') or (not line):
                lines.append(line)
                continue
            lines.append(f'{line}={dumps(self.environment[line], ensure_ascii=False)}')
        self.env_path.write_text('\n'.join(lines), encoding='Utf-8')
        logger.success('写入配置成功！手动重启机器人后修改才会生效。')

    # ===== pyproject.toml 操作 =====

    def read_pyproject(self) -> dict:
        '''读取 pyproject.toml 完整内容（保留注释和格式）'''
        with self.pyproject_path.open('r', encoding='utf-8') as file:
            return tomlkit.parse(file.read())

    def write_pyproject(self, data: dict):
        '''写回 pyproject.toml（保留注释和格式）'''
        with self.pyproject_path.open('w', encoding='utf-8') as file:
            file.write(tomlkit.dumps(data))

    def add_adapter(self, name: str, module_name: str) -> bool:
        '''添加适配器，返回是否成功（False 表示已存在）'''
        data = self.read_pyproject()
        adapters = data.setdefault('tool', {}).setdefault('nonebot', {}).setdefault('adapters', [])
        if any(adapter['module_name'] == module_name for adapter in adapters):
            return False
        adapters.append({'name': name, 'module_name': module_name})
        self.write_pyproject(data)
        return True

    def remove_adapter(self, module_name: str):
        '''移除适配器'''
        data = self.read_pyproject()
        adapters = data.get('tool', {}).get('nonebot', {}).get('adapters', [])
        data['tool']['nonebot']['adapters'] = [
            adapter for adapter in adapters if adapter['module_name'] != module_name
        ]
        self.write_pyproject(data)

    def add_plugin(self, module_name: str) -> bool:
        '''添加插件，返回是否成功（False 表示已存在）'''
        data = self.read_pyproject()
        plugins = data.setdefault('tool', {}).setdefault('nonebot', {}).setdefault('plugins', [])
        if module_name in plugins:
            return False
        plugins.append(module_name)
        self.write_pyproject(data)
        return True

    def remove_plugin(self, module_name: str):
        '''移除插件'''
        data = self.read_pyproject()
        plugins = data.get('tool', {}).get('nonebot', {}).get('plugins', [])
        data['tool']['nonebot']['plugins'] = [
            plugin for plugin in plugins if plugin != module_name
        ]
        self.write_pyproject(data)


environment_manager = EnvironmentManager()
