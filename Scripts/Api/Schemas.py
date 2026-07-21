from pydantic import BaseModel


# ===== Auth =====

class SetupRequest(BaseModel):
    username: str
    password: str
    nickname: str = '管理员'


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str = ''


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    nickname: str


# ===== Users =====

class CreateUserRequest(BaseModel):
    username: str
    password: str
    nickname: str
    role: str = 'viewer'


class UpdateUserRequest(BaseModel):
    nickname: str | None = None
    role: str | None = None


class ResetPasswordRequest(BaseModel):
    password: str


# ===== Servers =====

class ExecuteCommandRequest(BaseModel):
    command: str


class BroadcastRequest(BaseModel):
    message: str


# ===== Players =====

class BindPlayerRequest(BaseModel):
    user: str
    player: str


# ===== Plugins =====

class InstallPluginRequest(BaseModel):
    name: str
    version: str = ''


class UpgradePluginRequest(BaseModel):
    name: str
