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

RESPONSE_SCHEMA = vol.Schema({
    vol.Required(RESPONSE_TEXT): cv.string,
    vol.Optional(RESPONSE_KEYBOARD): vol.All(cv.ensure_list, [cv.string])
})

COMMAND_SCHEMA = vol.Schema({
    vol.Required(COMMAND): cv.string,
    vol.Optional(SCRIPT): cv.SCRIPT_SCHEMA,
    vol.Optional(RESPONSE): RESPONSE_SCHEMA,
    vol.Optional(ALLOWED_CHAT_IDS): vol.All(cv.ensure_list, [cv.string])
}, extra=vol.ALLOW_EXTRA)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(BOT_TOKEN): cv.string,
        vol.Required(ALLOWED_CHAT_IDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(COMMANDS): vol.All(cv.ensure_list, [COMMAND_SCHEMA])
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    import telepot
    bot_token = config[DOMAIN].get(BOT_TOKEN)
    # instance the Telegram bot
    bot = telepot.Bot(bot_token)
    _setup(hass, config, bot, telepot)


def _setup(hass, config, bot, telepot):
    """Setup is called when Home Assistant is loading our component."""
    logger = logging.getLogger(__name__)

    allowed_chat_ids = config[DOMAIN].get(ALLOWED_CHAT_IDS)

    # Build a list of telegram commands.
    commands = [Instruction(hass, bot, _command) for _command in
                config[DOMAIN].get(COMMANDS)]
    not_found_command = BaseInstruction(bot)

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

    def get_command(command, chat_id):
        """Gets the proper command"""
        for _cmd in commands:
            if _cmd.contains(command, chat_id):
                return _cmd
        return not_found_command

    def handle(msg):
        """Callback function which handles incoming telegram messages."""

        # glance to get some meta on the message
        content_type, chat_type, chat_id = telepot.glance(msg)
        chat_id = str(chat_id)

        # we only want to process text messages from our specified chat
        if (content_type == 'text') and (chat_id in allowed_chat_ids):
            command = msg['text']
            try:
                _cmd = get_command(command, chat_id)
            except UserWarning as ex:
                logger.error(ex)
                raise
            _cmd.execute(chat_id)
        else:
            not_found_command.execute(chat_id)

    # Return boolean to indicate that initialization was successfully.
    return True


class BaseInstruction:
    def __init__(self, bot):
        self.script = None
        self.response = {RESPONSE_TEXT: "Command not found or not allowed",
                         RESPONSE_KEYBOARD: None}
        self.bot = bot
        self.allowed_ids = None
        self.command = None

    def contains(self, command, chat_id):
        if command == self.command:
            if self.allowed_ids is None:
                return True
            elif chat_id in self.allowed_ids:
                return True
        return False

    def execute(self, chat_id):
        if self.script:
            self.script.run()
        if self.response:
            self.bot.sendMessage(chat_id,
                                 self.response[RESPONSE_TEXT],
                                 parse_mode="Markdown",
                                 reply_markup=self.response[RESPONSE_KEYBOARD])


class Instruction(BaseInstruction):
    def __init__(self, hass, bot, command):
        BaseInstruction.__init__(self, bot)
        self.hass = hass
        self.response = None
        self.command = command[COMMAND]
        self.allowed_ids = command.get(ALLOWED_CHAT_IDS, None)

        _script = command.get(SCRIPT, None)
        if _script is not None:
            self.script = Script(hass, _script)
        _response = command.get(RESPONSE, None)
        if _response is not None:
            self.response = {
                RESPONSE_TEXT: _response.get(RESPONSE_TEXT, None)}
            _keyboard = _response.get(RESPONSE_KEYBOARD, None)
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
            else:
                self.response[RESPONSE_KEYBOARD] = None
