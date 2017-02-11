"""A telegram bot which allows you to send and receive commands."""

import voluptuous as vol
from homeassistant.const import EVENT_HOMEASSISTANT_START, \
    EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.script import Script
from homeassistant.helpers import config_validation as cv
import logging

REQUIREMENTS = [
    'telepot==10.4'
]

# The domain of your component. Should be equal to the name of your component.
DOMAIN = 'hass_telepot'
BOT_TOKEN = 'bot_token'
ALLOWED_CHAT_IDS = 'allowed_chat_ids'
COMMANDS = 'commands'

COMMAND = 'command'
SCRIPT = 'script'
RESPONSE = 'response'
RESPONSE_TEXT = 'text'
RESPONSE_KEYBOARD = 'keyboard'

RESPONSE_KEYS_SCHEMA = vol.Schema({
    vol.Required(vol.Any(RESPONSE_TEXT, RESPONSE_KEYBOARD)): object
}, extra=vol.ALLOW_EXTRA)

RESPONSE_DATA_SCHEMA = vol.Schema({
    vol.Optional(RESPONSE_TEXT): cv.string,
    vol.Optional(RESPONSE_KEYBOARD): vol.All(cv.ensure_list, [cv.string])
})

RESPONSE_SCHEMA = vol.All(RESPONSE_KEYS_SCHEMA, RESPONSE_DATA_SCHEMA)

COMMAND_SCHEMA = vol.Schema({
    vol.Required(COMMAND): cv.string,
    vol.Optional(SCRIPT): cv.SCRIPT_SCHEMA,
    vol.Optional(RESPONSE): RESPONSE_SCHEMA
}, extra=vol.ALLOW_EXTRA)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(BOT_TOKEN): cv.string,
        vol.Required(ALLOWED_CHAT_IDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(COMMANDS): vol.All(cv.ensure_list, [COMMAND_SCHEMA])
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Setup is called when Home Assistant is loading our component."""
    logger = logging.getLogger(__name__)
    import telepot

    bot_token = config[DOMAIN].get(BOT_TOKEN)
    allowed_chat_ids = config[DOMAIN].get(ALLOWED_CHAT_IDS)

    # instance the Telegram bot
    bot = telepot.Bot(bot_token)
    # Build a list of telegram commands.
    commands = [Instruction(hass, bot, _command) for _command in
                config[DOMAIN].get(COMMANDS)]

    def _start_bot(_event):
        bot.message_loop(handle)

    def _stop_bot(_event):
        """Stops the bot. Unfortunately no clean stopping of
        the telepot instance available yet (?)"""
        pass

    hass.bus.listen_once(
        EVENT_HOMEASSISTANT_START,
        _start_bot
    )
    hass.bus.listen_once(
        EVENT_HOMEASSISTANT_STOP,
        _stop_bot
    )

    def get_command(command):
        for _cmd in commands:
            if _cmd.command == command:
                return _cmd
        raise UserWarning("telegram command not found.")

    def handle(msg):
        """Callback function which handles incoming telegram messages."""

        # glance to get some meta on the message
        content_type, chat_type, chat_id = telepot.glance(msg)
        chat_id = str(chat_id)

        # we only want to process text messages from our specified chat
        if (content_type == 'text') and (chat_id in allowed_chat_ids):
            command = msg['text']
            try:
                _cmd = get_command(command)
            except UserWarning as ex:
                logger.error(ex)
                raise
            _cmd.execute(chat_id)

    # Return boolean to indicate that initialization was successfully.
    return True


class Instruction:
    def __init__(self, hass, bot, command):
        self.hass = hass
        self.bot = bot
        self.script = None
        self.response = None
        self.command = command[COMMAND]

        _script = command.get(SCRIPT, None)
        if _script is not None:
            self.script = Script(hass, _script)

        _response = command.get(RESPONSE, None)
        if _response is not None:
            self.response = {}
            _text = _response.get(RESPONSE_TEXT, None)
            _keyboard = _response.get(RESPONSE_KEYBOARD, None)
            if _text:
                self.response[RESPONSE_TEXT] = _text
            if _keyboard:
                self.response[RESPONSE_KEYBOARD] = {
                    "keyboard": [],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
                for _key in _keyboard:
                    self.response[RESPONSE_KEYBOARD]["keyboard"].append(
                        [{"text": _key}]
                    )

    def execute(self, chat_id):
        if self.script:
            self.script.run()
        if self.response:
            self.bot.sendMessage(chat_id,
                                 self.response[RESPONSE_TEXT],
                                 reply_markup=self.response[RESPONSE_KEYBOARD])
