import asyncio
from datetime import datetime

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from nonebot.log import logger

from Scripts.Managers import data_manager

router = APIRouter(tags=['WebSocket'])

# 已连接的 WebSocket 客户端及其订阅的事件
ws_clients: dict[WebSocket, set[str]] = {}


async def broadcast_event(event_type: str, data: dict):
    '''向所有订阅了该事件的 WebSocket 客户端推送消息'''
    message = {'type': event_type, 'data': data}
    disconnected = []
    for websocket, subscribed_events in ws_clients.items():
        if event_type in subscribed_events:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
    for websocket in disconnected:
        ws_clients.pop(websocket, None)


def log_sink(message):
    '''loguru sink，将日志推送到 WebSocket 客户端'''
    record = message.record
    log_data = {
        'level': record['level'].name,
        'time': datetime.fromtimestamp(record['time'].timestamp()).strftime('%H:%M:%S'),
        'message': record['message'],
        'module': record['name'],
    }
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(broadcast_event('log', log_data))
    except RuntimeError:
        pass


@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    '''WebSocket 端点，支持订阅日志、服务器、玩家、系统事件'''
    # 通过 query 参数中的 JWT 验证身份
    token = websocket.query_params.get('token', '')
    if not token:
        await websocket.close(code=4001, reason='Unauthorized')
        return
    try:
        payload = jwt.decode(token, data_manager.secret_key, algorithms=['HS256'])
        if payload.get('type') != 'access':
            raise jwt.InvalidTokenError()
    except jwt.InvalidTokenError:
        await websocket.close(code=4001, reason='Unauthorized')
        return

    await websocket.accept()
    ws_clients[websocket] = set()
    logger.debug('WebUI WebSocket 客户端已连接！')

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get('type', '')

            if message_type == 'subscribe':
                events = data.get('events', [])
                ws_clients[websocket] = set(events)
                await websocket.send_json({'type': 'subscribed', 'events': list(ws_clients[websocket])})

            elif message_type == 'unsubscribe':
                events = data.get('events', [])
                ws_clients[websocket] -= set(events)
                await websocket.send_json({'type': 'subscribed', 'events': list(ws_clients[websocket])})

            elif message_type == 'ping':
                await websocket.send_json({'type': 'pong'})

    except WebSocketDisconnect:
        logger.debug('WebUI WebSocket 客户端已断开！')
    except Exception as error:
        logger.warning(f'WebSocket 异常：{error}')
    finally:
        ws_clients.pop(websocket, None)
