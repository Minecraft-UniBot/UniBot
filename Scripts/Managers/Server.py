import re
import asyncio

from nonebot import get_adapter
from nonebot.internal import adapter
from nonebot.log import logger

from nonebot.adapters.minecraft.message import Message
from nonebot.adapters.minecraft import Adapter as MCAdapter, Bot

from ..Config import config


class ServerManager:
    '''Minecraft 服务器管理器，封装与 Minecraft 的交互'''
    def init(self):
        self.adatper = get_adapter(MCAdapter)
        self.servers = self.adatper.bots

    def get_server(self, server_flag: str | int):
        '''通过名称或编号获取 Minecraft 机器人'''
        if self.servers is None:
            return
        if isinstance(server_flag, int) or (isinstance(server_flag, str) and server_flag.isdigit()):
            names = list(self.servers.keys())
            index = int(server_flag) - 1
            if 0 <= index < len(names):
                return self.servers[names[index]]
        return self.servers.get(str(server_flag), None)

    def check_online(self):
        '''是否有 Minecraft 服务器在线'''
        return bool(self.servers)

    async def gather(self, get_task, filter = None):
        if self.servers is None:
            return
        names, tasks = [], []
        for name, server in self.servers.items():
            if filter is None or filter(server):
                names.append(name)
                tasks.append(get_task(server))
        results = await asyncio.gather(*tasks)
        return {names[index]: result for index, result in enumerate(results)}

    async def execute(self, command: str, server_flag: str | int | None = None):
        '''执行 Minecraft 指令，server_flag 为 None 时广播到所有服务器'''

        async def get_task(server: Bot):
            try:
                return await server.send_rcon_command(command=command)
            except Exception as error:
                logger.warning(f'向服务器 [{server.self_id}] 发送指令失败：{error}')

        if server_flag is not None:
            bot = self.get_server(server_flag)
            if bot is not None:
                return {bot.self_id: await bot.send_rcon_command(command=command)}
            return
        return await self.gather(get_task)

    async def get_status(self, server: Bot) -> dict:
        '''获取 Minecraft 服务器状态'''
        try:
            status = await self.adatper.send_websocket_message(server.self_id, 'get_status', {})
        except Exception as error:
            logger.warning(f'获取服务器 [{server.self_id}] 状态失败：{error}')
            return {
                'online': False,
                'server_type': '',
                'players': 0,
                'max_players': 0,
                'version': '',
                'motd': '',
                'cpu_load': 0.0,
                'memory_percent': 0.0,
                'jvm_memory_used': 0,
                'jvm_memory_max': 0,
            }

        status_data = status.get('data', status) if isinstance(status, dict) else {}
        server_ping = status_data.get('server_list_ping') or {}
        player_status = server_ping.get('players') or {}
        version_status = server_ping.get('version') or {}

        cpu_info = status_data.get('cpu_information') or {}
        memory_info = status_data.get('memory_information') or {}
        jvm_memory = memory_info.get('jvm_memory') or {}

        return {
            'online': bool(server_ping.get('available', True)),
            'server_type': status_data.get('server_type', ''),
            'players': int(player_status.get('online', 0)),
            'max_players': int(player_status.get('max', 0)),
            'version': version_status.get('name', status_data.get('server_version', '')),
            'motd': server_ping.get('description', ''),
            'cpu_load': round(max(cpu_info.get('system_load', 0), cpu_info.get('process_load', 0)), 1),
            'memory_percent': round(jvm_memory.get('percentage', 0), 1),
            'jvm_memory_used': round(jvm_memory.get('used', 0) / 1024 / 1024, 1),
            'jvm_memory_max': round(jvm_memory.get('max', 0) / 1024 / 1024, 1),
        }

    async def get_player_list(self, server: Bot) -> tuple[list[str], int]:
        '''通过 RCON 指令获取并解析服务器玩家列表'''
        try:
            result = await server.send_rcon_command(command='list')
        except Exception as error:
            logger.warning(f'获取服务器 [{server.self_id}] 玩家列表失败：{error}')
            return [], 0
        if not result:
            return [], 0

        match = re.search(r'^There are \d+ of (?:a )?max(?: of)? (\d+) players online:\s*(.*)$', result.strip())
        if match is None:
            logger.warning(f'解析服务器 [{server.self_id}] 玩家列表失败：{result}')
            return [], 0
        max_players = int(match.group(1))
        players = [player.strip() for player in match.group(2).split(',') if player.strip()]
        return players, max_players

    async def broadcast(self, message: Message | str, except_server: str = ''):
        '''广播消息到所有服务器（除 except_server 外）'''

        async def get_task(server: Bot):
            try:
                return await server.send_msg(message=message)
            except Exception as e:
                logger.warning(f'向服务器 [{server.self_id}] 广播消息失败：{e}')

        return await self.gather(get_task, lambda server: server.self_id != except_server)


server_manager = ServerManager()
