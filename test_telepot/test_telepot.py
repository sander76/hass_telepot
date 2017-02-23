import yaml

from hass_telepot import Instruction, DOMAIN, COMMANDS, _setup, CONFIG_SCHEMA
from test_telepot.mock_bot import MockBot
from test_telepot.mock_hass import MockHass
import test_telepot.telepot as telepot

CONFIG = """
hass_telepot:
    bot_token : abc
    allowed_chat_ids :
    - 123
    - 456
    - 333
    commands:
    -   command: /hello
        allowed_chat_ids: 123
        response:
          text: Hi stranger.
    -   command: /hello
        allowed_chat_ids: 456
        response:
          text: Hi Sander.
    -   command: /hello
        response:
          text: Hi All!
"""

config = yaml.load(CONFIG)

config = CONFIG_SCHEMA(config)

hass = MockHass()
bot = MockBot()

_setup(hass, config, bot, telepot)

cmd1 = {"text": "/hello", "chat_id": 123}
cmd2 = {"text": "/hello", "chat_id": 456}
cmd3 = {"text": "/hello", "chat_id": 789}
cmd4 = {"text": "/hello", "chat_id": 333}

hass.start_hass()


def test_cmd1():
    bot.handle(cmd1)
    assert bot.chat_id == '123'
    assert bot.text == "Hi stranger."


def test_cmd2():
    bot.handle(cmd2)
    assert bot.chat_id == '456'
    assert bot.text == 'Hi Sander.'


def test_cmd3():
    bot.handle(cmd3)
    assert bot.chat_id == '789'
    assert bot.text == 'Command not found or not allowed'


def test_cmd4():
    bot.handle(cmd4)
    assert bot.chat_id == '333'
    assert bot.text == 'Hi All!'
