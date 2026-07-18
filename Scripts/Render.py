from nonebot import require

from .Config import config

require('nonebot_plugin_htmlrender')
from nonebot_plugin_htmlrender import template_to_pic  # noqa: E402

template_path = './Resources/Images'


async def render_template(template_name: str, size: tuple, **kwargs):
    width, height = size
    kwargs.setdefault('background', config.image_background)
    page = {'viewport': {'width': width, 'height': height}, 'base_url': 'file://' + template_path}
    return await template_to_pic(template_path, template_name, kwargs, pages=page, wait=1)
