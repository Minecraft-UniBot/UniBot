from asyncio import Lock
from json import loads, dump
from pathlib import Path

from nonebot.log import logger

from ..Config import config


class DataManager:
    players: dict = {}

    data_dir = Path('Data')
    resources_dir = Path('Resources')

    lock = Lock()

    def load(self):
        self.load_bot_data()
        logger.info('加载数据文件……')
        if not self.data_dir.exists():
            logger.warning('数据文件目录不存在，正在创建数据目录……')
            self.data_dir.mkdir()
        player_file = (self.data_dir / 'Player.json')
        if player_file.exists():
            try:
                self.players = loads(player_file.read_text('Utf-8'))
            except Exception:
                logger.warning('玩家数据文件损坏，使用空数据！')
                self.players = {}
        logger.success('加载数据文件完毕！')

    def load_bot_data(self):
        logger.debug('正在加载机器人数据……')
        logger.success('加载机器人数据完毕！')

    async def save(self):
        async with self.lock:
            logger.debug('正在保存数据文件……')
            player_file = (self.data_dir / 'Player.json')
            with player_file.open('w', encoding='Utf-8') as file:
                dump(self.players, file)
            logger.success('保存数据文件完毕！')

    async def append_player(self, user: str, player: str):
        if user not in self.players:
            self.players[user] = [player]
            await self.save()
            return True
        if config.qq_bound_max_number == 0:
            self.players[user].append(player)
            await self.save()
            return True
        if len(self.players[user]) < config.qq_bound_max_number:
            self.players[user].append(player)
            await self.save()
            return True
        return False

    async def remove_player(self, user: str, player: str = ''):
        if not player:
            bounded = self.players.pop(user, None)
            await self.save()
            return bounded
        if player in self.players[user]:
            self.players[user].remove(player)
            if not self.players[user]:
                self.players.pop(user)
            await self.save()
            return player
        return False

    async def check_player_occupied(self, player: str):
        player = player.lower()
        for bounded_players in self.players.values():
            if player in (bounded_player.lower() for bounded_player in bounded_players):
                return True
        return False


data_manager = DataManager()