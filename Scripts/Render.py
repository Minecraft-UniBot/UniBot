import json
import html
import asyncio
from io import BytesIO
from pathlib import Path

from html2pic import Html2Pic
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from nonebot.log import logger

from .Config import config

RESOURCES_DIR = Path(__file__).parent.parent / 'Resources'
FONT_PATH: Path = RESOURCES_DIR / 'Font.ttf'
TEMPLATES_DIR = RESOURCES_DIR / 'Images'

environment = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), enable_async=True)

logger.debug('图片渲染器加载完毕！')


def render(html: str, css: str) -> bytes:
    renderer = Html2Pic(html, css)
    image = renderer.render()
    pil_image = image.to_pillow()
    buffer = BytesIO()
    pil_image.save(buffer, format='PNG', compress_level=1)
    return buffer.getvalue()


def encode_context(context: dict) -> dict:
    string = json.dumps(context)
    return json.loads(html.escape(string, False))


async def load_style(name: str, **context) -> str:
    """加载 base.css + 模板专属 css，并通过 Jinja2 异步渲染"""
    parts = []
    for css_name in ('Base.css', f'{name}/{name}.css'):
        try:
            template = environment.get_template(css_name)
            parts.append(await template.render_async(**context))
        except TemplateNotFound:
            continue
    return '\n'.join(parts)


async def render_template(template_name: str, size: tuple[int, int], **kwargs) -> bytes:
    """渲染模板为 PNG 图片字节

    template_name: 模板名称，如 'List'，对应 Resources/Images/List/List.html 和 List.css
    size: (width, height)
    """
    width, height = size
    background = config.image.background or 'linear-gradient(150deg, #2e4a30 0%, #1d3524 55%, #12241a 100%)'
    context = dict(
        width=width, height=height,
        background=background,
        font_uri=str(FONT_PATH),
        **encode_context(kwargs),
    )
    template = environment.get_template(f'{template_name}/{template_name}.html')
    html_content, css_content = await asyncio.gather(
        template.render_async(**context),
        load_style(template_name, **context),
    )
    logger.debug(f'渲染图片：{html_content}\n{css_content}')
    return await asyncio.to_thread(render, html_content, css_content)
