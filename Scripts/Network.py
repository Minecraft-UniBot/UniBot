from io import BytesIO

from httpx import AsyncClient
from nonebot.log import logger

from Scripts.Globals import uuid_caches

client = AsyncClient()


async def request(url: str):
    try:
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
        logger.warning(f'请求 {url} 失败：错误的状态代码 {response.status_code}')
    except Exception as error:
        logger.warning(f'请求 {url} 失败：{error}')


async def get_player_uuid(name: str):
    if name in uuid_caches:
        return uuid_caches[name]
    uuid = '8667ba71b85a4004af54457a9734eed7'
    if response := await request(f'https://api.mojang.com/users/profiles/minecraft/{name}'):
        uuid = response.get('id') or '8667ba71b85a4004af54457a9734eed7'
    uuid_caches[name] = uuid
    return uuid


async def download(url: str):
    download_bytes = BytesIO()
    if 'github' in url:
        url = 'https://mirror.ghproxy.com/' + url
    async with client.stream('GET', url) as stream:
        if stream.status_code != 200:
            return False
        async for chunk in stream.aiter_bytes():
            download_bytes.write(chunk)
        download_bytes.seek(0)
        return download_bytes
