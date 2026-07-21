from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException
from nonebot.log import logger

from Scripts.Managers import user_manager
from .Schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SetupRequest,
    UpdateProfileRequest,
)

router = APIRouter(prefix='/api/auth', tags=['Auth'])

ACCESS_TOKEN_EXPIRE_HOURS = 2
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 已注销的 refresh_token 集合
revoked_tokens: set[str] = set()


def create_access_token(user_id: str, role: str) -> str:
    '''签发 access_token'''
    payload = {
        'sub': user_id,
        'role': role,
        'type': 'access',
        'exp': datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, user_manager.secret_key, algorithm='HS256')


def create_refresh_token(user_id: str) -> str:
    '''签发 refresh_token'''
    payload = {
        'sub': user_id,
        'type': 'refresh',
        'exp': datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, user_manager.secret_key, algorithm='HS256')


async def get_current_user(authorization: str | None = Header(None)) -> dict:
    '''解析 JWT，返回当前用户对象'''
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='未认证')
    token = authorization[7:]
    try:
        payload = jwt.decode(token, user_manager.secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token 已过期')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='无效的 Token')
    if payload.get('type') != 'access':
        raise HTTPException(status_code=401, detail='无效的 Token 类型')
    user_data = user_manager.get_by_id(payload['sub'])
    if not user_data:
        raise HTTPException(status_code=401, detail='用户不存在')
    return user_data


def require_role(*roles: str):
    '''角色校验依赖工厂'''
    async def checker(user: dict = Depends(get_current_user)):
        if user['role'] not in roles:
            raise HTTPException(status_code=403, detail='权限不足')
        return user
    return checker


@router.post('/setup', summary='首次初始化')
async def setup(body: SetupRequest):
    '''首次初始化：创建管理员账户，仅在无任何用户时可用'''
    if user_manager.is_initialized:
        return {'code': 1, 'data': None, 'message': '系统已初始化'}
    user_info = await user_manager.create_user(body.username, body.password, body.nickname, role='admin')
    logger.success(f'WebUI 管理员账户 [{body.username}] 创建成功！')
    return {'code': 0, 'data': {'user_id': user_info['user_id']}, 'message': '初始化成功'}


@router.post('/login', summary='用户登录')
async def login(body: LoginRequest):
    '''用户名密码登录，返回 JWT'''
    user_data = user_manager.get_by_username(body.username)
    if not user_data or not user_manager.verify_password(body.password, user_data['password_hash']):
        return {'code': 1, 'data': None, 'message': '用户名或密码错误'}
    await user_manager.update_last_login(user_data['user_id'])
    access_token = create_access_token(user_data['user_id'], user_data['role'])
    refresh_token = create_refresh_token(user_data['user_id'])
    return {
        'code': 0,
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            'user': user_manager.public_info(user_data),
        },
        'message': 'ok',
    }


@router.post('/refresh', summary='刷新 Token')
async def refresh(body: RefreshRequest):
    '''使用 refresh_token 换取新的 access_token'''
    if body.refresh_token in revoked_tokens:
        return {'code': 401, 'data': None, 'message': 'Token 已失效'}
    try:
        payload = jwt.decode(body.refresh_token, user_manager.secret_key, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return {'code': 401, 'data': None, 'message': '无效的 refresh_token'}
    if payload.get('type') != 'refresh':
        return {'code': 401, 'data': None, 'message': '无效的 Token 类型'}
    user_data = user_manager.get_by_id(payload['sub'])
    if not user_data:
        return {'code': 401, 'data': None, 'message': '用户不存在'}
    access_token = create_access_token(user_data['user_id'], user_data['role'])
    return {
        'code': 0,
        'data': {'access_token': access_token, 'expires_in': ACCESS_TOKEN_EXPIRE_HOURS * 3600},
        'message': 'ok',
    }


@router.post('/logout', summary='退出登录')
async def logout(body: LogoutRequest):
    '''使当前 refresh_token 失效'''
    if body.refresh_token:
        revoked_tokens.add(body.refresh_token)
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.get('/me', summary='获取当前用户信息')
async def get_me(user: dict = Depends(get_current_user)):
    '''获取当前登录用户信息'''
    return {'code': 0, 'data': user_manager.public_info(user), 'message': 'ok'}


@router.put('/password', summary='修改密码')
async def change_password(body: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    '''修改当前用户密码'''
    if not user_manager.verify_password(body.old_password, user['password_hash']):
        return {'code': 1, 'data': None, 'message': '原密码错误'}
    await user_manager.reset_password(user['user_id'], body.new_password)
    return {'code': 0, 'data': None, 'message': 'ok'}


@router.put('/profile', summary='修改昵称')
async def update_profile(body: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    '''修改当前用户昵称'''
    await user_manager.update_user(user['user_id'], nickname=body.nickname)
    return {'code': 0, 'data': None, 'message': 'ok'}
