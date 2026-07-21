from io import BytesIO

from httpx import AsyncClient
from nonebot.log import logger

from Scripts.Globals import uuid_caches

client = AsyncClient()

# GitHub 加速镜像列表（依次尝试，全部失败后回退到原始地址直连）
GITHUB_MIRRORS = [
    'https://ghproxy.net/',
    'https://gh-proxy.com/',
    'https://ghfast.top/',
    'https://ghproxy.cc/',
]


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
    '''下载文件，GitHub 地址会依次尝试加速镜像，全部失败后回退到原始地址直连'''
    candidate_urls = []
    if 'github' in url:
        candidate_urls = [mirror + url for mirror in GITHUB_MIRRORS]
    candidate_urls.append(url)
    for candidate_url in candidate_urls:
        try:
            download_bytes = BytesIO()
            async with client.stream('GET', candidate_url) as stream:
                if stream.status_code != 200:
                    logger.warning(f'下载 {candidate_url} 失败：错误的状态代码 {stream.status_code}')
                    continue
                async for chunk in stream.aiter_bytes():
                    download_bytes.write(chunk)
            download_bytes.seek(0)
            return download_bytes
        except Exception as error:
            logger.warning(f'下载 {candidate_url} 失败：{error}')
    return False
