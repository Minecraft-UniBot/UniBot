from nonebot import get_adapter
from nonebot.log import logger

from nonebot.adapters.minecraft.message import Message
from nonebot.adapters.minecraft import Bot as MCServer, Adapter as MCAdapter

from ..Config import config


class ServerManager:
    '''Minecraft 服务器管理器，封装与 Minecraft 的交互'''
    servers = None

    def init(self):
        self.servers = get_adapter(MCAdapter).bots

    def get_server(self, server_flag: str | int) -> MCServer | None:
        '''通过名称或编号获取 Minecraft 机器人'''
        if self.servers is None:
            return None
        if isinstance(server_flag, int) or (isinstance(server_flag, str) and server_flag.isdigit()):
            names = list(self.servers.keys())
            index = int(server_flag) - 1
            if 0 <= index < len(names):
                return self.servers[names[index]]
        return self.servers.get(server_flag, None)

    def check_online(self):
        '''是否有 Minecraft 服务器在线'''
        return bool(self.servers)

    async def execute(self, command: str, server_flag: str | int | None = None):
        '''执行 Minecraft 指令，server_flag 为 None 时广播到所有服务器'''
        if self.servers is None:
            return None
        if server_flag is not None:
            bot = self.get_server(server_flag)
            if bot is not None:
                return {bot.self_id: await bot.send_rcon_command(command=command)}
            return None

        results = {}
        for name, bot in self.servers.items():
            try:
                results[name] = await bot.send_rcon_command(command=command)
            except Exception as e:
                logger.warning(f'向服务器 [{name}] 发送指令失败：{e}')
                results[name] = None
        return results

    async def send_message(self, message: Message | str):
        '''发送消息到所有 Minecraft 服务器'''
        if self.servers is None:
            return
        for name, bot in self.servers.items():
            try:
                await bot.send_msg(message=message)
                logger.debug(f'已向服务器 [{name}] 发送消息')
            except Exception as e:
                logger.warning(f'向服务器 [{name}] 发送消息失败：{e}')

    async def broadcast(self, message: Message | str, except_server: str = ''):
        '''广播消息到所有服务器（除 except_server 外）'''
        if self.servers is None:
            return
        for name, bot in self.servers.items():
            if name == except_server:
                continue
            try:
                await bot.send_msg(message=message)
            except Exception as e:
                logger.warning(f'向服务器 [{name}] 广播消息失败：{e}')


server_manager = ServerManager()
