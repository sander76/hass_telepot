# hass_telepot

Inspired by: https://github.com/GussyH/hass-telebot

A home assistant custom component which allows for sending and receiving telegram commands to control HomeAsisstant.

## Installation
Put the `hass_telepot.py` file in your `custom_components` folder which should by default be in the same folder as your `configuration.yaml` file. Create the folder if it is not there.

## Configuration

Put the following in your `configuration.yaml` file.

```yaml
hass_telepot:
    bot_token : your bot token
    allowed_chat_ids :
    - id1
    - id2
    commands:
    -   command: /away  # The command you send using your telegram client.
        allowed_ids:  # Optional
        - id1  # This commands is only allowed for id1
        script:  # A hass script you activate when you send the above command.
            service: input_boolean.turn_on
            entity_id: input_boolean.away
    -   command: /athome
        script:
            service: input_boolean.turn_off
            entity_id: input_boolean.away
    -   command: /presence
        response:  # Response you send back to the client.
            text: Please choose whether you are at home or not  # Text response
            keyboard:  # Keyboard which is displayed in your client with available buttons to press.
            -   /away
            -   /athome
```

