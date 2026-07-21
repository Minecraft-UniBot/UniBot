from nonebot.log import logger

from .Environment import environment_manager


class VersionManager:
    version: str = ''
    latest_version: str | None = None

    def check_update(self):
        if self.latest_version is None:
            return False
        return self.latest_version != self.version

    async def init(self):
        self.version = environment_manager.version
        logger.info(f'监测到当前为 {self.version} 版本。')
        logger.warning('版本检查服务器G了，作者挖坑不填，捞B')

    # async def update_version(self):
    #     logger.info(F'更新版本到 {self.latest_version}……')
    #     if response := await download(
    #             F'https://github.com/Minecraft-QQBot/BotServer/releases/download/v{self.latest_version}/BotServer-v{self.latest_version}.zip'):
    #         with ZipFile(response) as zip_file:
    #             for file in zip_file.namelist():
    #                 if file.startswith('BotServer/') and ('.env' not in file):
    #                     file_path = file[10:]
    #                     if '.' in file_path:
    #                         with open(file_path, 'wb') as target_file:
    #                             target_file.write(zip_file.read(file))
    #                         continue
    #                     if not path.exists(file_path) and file_path:
    #                         mkdir(file_path)
    #         logger.success(F'更新版本到 {self.latest_version} 成功！请重启机器人。')
    #         return None
    #     logger.warning(F'更新版本到 {self.latest_version} 失败，请检查网络稍后再试。')


version_manager = VersionManager()
