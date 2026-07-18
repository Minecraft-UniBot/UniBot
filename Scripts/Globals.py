from Scripts.Config import config

uuid_caches: dict[str, str] = {}

render_template = None

if config.image_mode:
    from .Render import render_template
