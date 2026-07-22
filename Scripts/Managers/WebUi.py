import shutil
from pathlib import Path
from zipfile import ZipFile

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from nonebot.log import logger

from Scripts.Network import download
from Scripts.Api import api_router, setup_cors
from Scripts.Api.WebSocket import log_sink
from .Environment import environment_manager


class WebUiManager:
    '''WebUI 管理面板：负责 API 路由挂载、前端静态资源的版本校验/下载与静态文件挂载'''

    app: FastAPI | None = None

    webui_dir: Path = Path('WebUi')
    version_file: Path = Path('WebUi/.version')

    @property
    def version(self) -> str:
        '''当前期望的 WebUI 版本（来自 pyproject.toml [unibot] webui_version）'''
        return environment_manager.webui_version

    def read_local_version(self) -> str:
        '''读取本地已下载的 WebUI 版本'''
        if self.version_file.exists():
            return self.version_file.read_text('Utf-8').strip()
        return ''

    def is_ready(self) -> bool:
        '''检查本地 WebUI 是否已下载且版本匹配'''
        return (
            (self.webui_dir / 'index.html').exists()
            and self.read_local_version() == self.version
        )

    async def ensure_downloaded(self) -> bool:
        '''确保 WebUI 静态资源已下载且版本匹配，否则重新下载'''
        if not self.version:
            logger.warning('未配置 WebUI 版本（pyproject.toml [unibot] webui_version），跳过下载！')
            return False
        if self.is_ready():
            logger.info(f'WebUI 静态资源已就绪（{self.version}）。')
            return True
        logger.info(f'正在下载 WebUI 静态资源（{self.version}）……')
        url = f'https://github.com/Minecraft-UniBot/WebUi/releases/download/{self.version}/WebUi.zip'
        if not (response := await download(url)):
            logger.warning(f'下载 WebUI（{self.version}）失败，请检查网络稍后再试。')
            return False
        try:
            if self.webui_dir.exists():
                shutil.rmtree(self.webui_dir)
            self.webui_dir.mkdir(parents=True, exist_ok=True)
            with ZipFile(response) as zip_file:
                zip_file.extractall(self.webui_dir)
            self.version_file.write_text(self.version, encoding='Utf-8')
        except Exception as error:
            logger.warning(f'解压 WebUI 静态资源失败：{error}')
            return False
        logger.success(f'下载 WebUI 静态资源（{self.version}）成功！')
        return True

    def mount(self, app: FastAPI):
        '''挂载 WebUI API 路由到 /webui 前缀下（需在 nonebot.init() 之后、nonebot.run() 之前调用）'''
        self.app = app
        setup_cors(app)
        app.include_router(api_router, prefix='/webui')
        logger.add(log_sink, level='DEBUG', format='{time:HH:mm:ss} | {level} | {message}')
        logger.success('WebUI API 路由挂载完毕！')

    def mount_static(self):
        '''挂载 WebUI 静态文件到 /webui/ 路径'''
        if self.app is None:
            logger.warning('WebUI 尚未挂载 API 路由，无法挂载静态文件！')
            return
        if not (self.webui_dir / 'index.html').exists():
            logger.warning('WebUI 静态资源缺失，仅挂载 API 路由。')
            return
        self.app.mount('/webui', StaticFiles(directory=self.webui_dir, html=True), name='webui')
        logger.success('WebUI 静态文件挂载完毕！访问路径：/webui/')

    async def init(self):
        '''初始化：校验并下载 WebUI 静态资源，随后挂载静态文件'''
        try:
            await self.ensure_downloaded()
            self.mount_static()
        except Exception as error:
            logger.error(f'下载 WebUi 遇到错误，已自动禁用！错误：{error}')


webui_manager = WebUiManager()
