import random
from datetime import date
from hashlib import md5

from nonebot.log import logger
from nonebot_plugin_alconna import Command
from nonebot_plugin_uninfo import Uninfo

from Scripts.Utils import turn_message_text
from Scripts.Rules import command_group_rule

bad_things = (
    '造世吞（直接放飞', '修机器（一修就炸', '挖矿（只挖到原石', '造建筑（啥都没有', '钓鱼（全部是垃圾', '刷附魔（刷的垃圾'
)
good_things = (
    '造世吞（完美运行', '修机器（一修就好', '挖矿（挖到十钻石', '造建筑（要啥都有', '钓鱼（钓到把神弓', '刷附魔（一发就中'
)

logger.debug('加载命令 Luck 完毕！')

matcher = Command('luck').build(rule=command_group_rule, use_cmd_start=True)


@matcher.handle()
async def handle(session: Uninfo):
    message = await turn_message_text(luck_handler(session))
    await matcher.finish(message)


def luck_handler(session: Uninfo):
    user_id = str(session.user.id)
    scene_id = str(session.scene.id)
    seed_hash = md5(f'{date.today()} {scene_id} {user_id}'.encode())
    random.seed(seed := int(seed_hash.hexdigest(), 16))
    luck_point = random.randint(10, 100)
    tips = '啧……'
    if luck_point > 90:
        tips = '哇！'
    elif luck_point > 60:
        tips = '喵~'
    elif luck_point > 30:
        tips = '呜……'
    yield f'你今天的人品为 {luck_point}，{tips}'
    bad_thing = bad_things[(seed & int(scene_id.replace('-', '0'), 32)) % len(bad_things)]
    good_thing = good_things[(seed ^ int(scene_id.replace('-', '0'), 32)) % len(good_things)]
    yield f'今日宜：{good_thing}'
    if bad_thing.startswith(good_thing[:2]):
        bad_thing = bad_things[bad_things.index(bad_thing) - 1]
    yield f'今日忌：{bad_thing}'
