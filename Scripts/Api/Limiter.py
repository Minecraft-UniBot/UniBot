import time
import asyncio
from collections import defaultdict

from fastapi import HTTPException, Request
from nonebot.log import logger


class RateLimiter:
    '''IP 限流器：监测访问频率，异常 IP 自动封禁一段时间'''

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: int = 60,
        ban_seconds: int = 300,
        cleanup_interval: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.ban_seconds = ban_seconds
        self.cleanup_interval = cleanup_interval

        # {ip: {"timestamps": [float, ...], "banned_until": float | None}}
        self.records: dict[str, dict] = defaultdict(
            lambda: {'timestamps': [], 'banned_until': None}
        )
        self.cleanup_task: asyncio.Task | None = None

    def get_client_ip(self, request: Request) -> str:
        '''从请求中获取客户端真实 IP'''
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        client = request.client
        if client:
            return client.host
        return 'unknown'

    def is_banned(self, ip: str) -> bool:
        '''检查 IP 是否在封禁期内'''
        record = self.records.get(ip)
        if not record or not record['banned_until']:
            return False
        if time.time() >= record['banned_until']:
            record['banned_until'] = None
            return False
        return True

    def record_request(self, ip: str):
        '''记录一次请求，清理过期时间戳，判断是否触发封禁'''
        now = time.time()
        record = self.records[ip]
        timestamps = record['timestamps']

        # 移除超出时间窗口的旧记录
        cutoff = now - self.window_seconds
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

        # 添加当前请求
        timestamps.append(now)

        # 判断是否超出阈值
        if len(timestamps) > self.max_requests:
            record['banned_until'] = now + self.ban_seconds
            logger.warning(f'IP [{ip}] 请求频率异常（{len(timestamps)} 次/{self.window_seconds}s），已封禁 {self.ban_seconds}s！')
            return False

        return True

    async def check(self, request: Request):
        '''FastAPI 依赖：检查当前 IP 是否触发限流'''
        client_ip = self.get_client_ip(request)

        # 若本地则忽略
        if client_ip == '127.0.0.1':
            return

        if self.is_banned(client_ip):
            record = self.records[client_ip]
            remain = int(record['banned_until'] - time.time())
            raise HTTPException(
                status_code=429,
                detail=f'请求过于频繁，请 {remain} 秒后再试',
            )

        allowed = self.record_request(client_ip)
        if not allowed:
            remain = int(self.records[client_ip]['banned_until'] - time.time())
            raise HTTPException(
                status_code=429,
                detail=f'请求过于频繁，已封禁 {remain} 秒',
            )

    async def cleanup_loop(self):
        '''定时清理过期数据，防止内存泄漏'''
        while True:
            await asyncio.sleep(self.cleanup_interval)
            now = time.time()
            cutoff = now - self.window_seconds
            expired_ips: list[str] = []

            for ip, record in list(self.records.items()):
                # 清理过期时间戳
                timestamps = record['timestamps']
                while timestamps and timestamps[0] < cutoff:
                    timestamps.pop(0)

                # 如果 IP 已无记录且未封禁，彻底清理
                if not timestamps and not record['banned_until']:
                    expired_ips.append(ip)

                # 清理已过期的封禁状态
                if record['banned_until'] and now >= record['banned_until']:
                    record['banned_until'] = None
                    if not timestamps:
                        expired_ips.append(ip)

            for ip in expired_ips:
                del self.records[ip]

            if expired_ips:
                logger.debug(f'限流器清理了 {len(expired_ips)} 个过期 IP 记录。')

    def start(self):
        '''启动后台清理任务'''
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self.cleanup_loop())
            logger.debug('限流器后台清理任务已启动。')

    def stop(self):
        '''停止后台清理任务'''
        if self.cleanup_task is not None:
            self.cleanup_task.cancel()
            self.cleanup_task = None
            logger.debug('限流器后台清理任务已停止。')


rate_limiter = RateLimiter()
