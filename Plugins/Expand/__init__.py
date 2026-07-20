from importlib import import_module

from Scripts.Config import config

if config.ai.enabled:
    import_module('Plugins.Expand.Ai')
if config.auto_reply.enabled:
    import_module('Plugins.Expand.Keywords')
