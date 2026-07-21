import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Query

from .Auth import get_current_user, require_role

router = APIRouter(prefix='/api/logs', tags=['Logs'])

LOGS_DIR = Path('Logs')

# 日志行解析正则：匹配 loguru 格式 "2026-07-20 12:00:01.123 | INFO     | module - message"
LOG_LINE_PATTERN = re.compile(
    r'^(?P<time>\d{2}:\d{2}:\d{2})\s*\|\s*(?P<level>\w+)\s*\|\s*(?P<message>.*)$'
)


@router.get('', summary='获取日志文件列表')
async def get_logs(current_user: dict = Depends(get_current_user)):
    '''获取日志文件列表'''
    if not LOGS_DIR.exists():
        return {'code': 0, 'data': [], 'message': 'ok'}

    log_files = []
    for file in sorted(LOGS_DIR.glob('*.log'), reverse=True):
        stat = file.stat()
        log_files.append({
            'name': file.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        })
    return {'code': 0, 'data': log_files, 'message': 'ok'}


@router.get('/{name}', summary='获取日志内容')
async def get_log_content(
    name: str,
    level: str = Query(''),
    keyword: str = Query(''),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    '''获取指定日志文件内容，支持按级别和关键词过滤'''
    log_file = LOGS_DIR / name
    if not log_file.exists() or not name.endswith('.log'):
        return {'code': 404, 'data': None, 'message': '日志文件不存在'}

    try:
        content = log_file.read_text('Utf-8')
    except Exception as error:
        return {'code': 500, 'data': None, 'message': f'读取日志失败：{error}'}

    raw_lines = content.splitlines()
    parsed_items = []

    for index, line in enumerate(raw_lines, start=1):
        match = LOG_LINE_PATTERN.match(line)
        if match:
            item = {
                'line': index,
                'time': match.group('time'),
                'level': match.group('level'),
                'message': match.group('message'),
            }
        else:
            item = {'line': index, 'time': '', 'level': '', 'message': line}
        parsed_items.append(item)

    # 按级别过滤
    if level:
        level_upper = level.upper()
        parsed_items = [item for item in parsed_items if item['level'] == level_upper]

    # 按关键词过滤
    if keyword:
        parsed_items = [item for item in parsed_items if keyword in item['message']]

    total = len(parsed_items)
    start = (page - 1) * page_size
    items = parsed_items[start:start + page_size]

    return {
        'code': 0,
        'data': {'items': items, 'total': total, 'page': page, 'page_size': page_size},
        'message': 'ok',
    }


@router.delete('/{name}', summary='删除日志文件')
async def delete_log(name: str, current_user: dict = Depends(require_role('admin'))):
    '''删除指定日志文件'''
    log_file = LOGS_DIR / name
    if not log_file.exists() or not name.endswith('.log'):
        return {'code': 404, 'data': None, 'message': '日志文件不存在'}
    log_file.unlink()
    return {'code': 0, 'data': None, 'message': 'ok'}
