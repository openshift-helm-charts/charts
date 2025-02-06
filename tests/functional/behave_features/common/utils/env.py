# -*- coding: utf-8 -*-
"""Utility class to reading environments."""
import logging
import os

from common.utils.setttings import *

def get_bot_name_and_token():
    bot_name = os.environ.get("BOT_NAME")
    logging.debug(f"Enviroment variable value BOT_NAME: {bot_name}")
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_name and not bot_token:
        bot_name = "github-actions[bot]"
        bot_token = os.environ.get("GITHUB_TOKEN")
        if not bot_token:
            raise Exception("BOT_TOKEN environment variable not defined")
    elif not bot_name:
        raise Exception("BOT_TOKEN set but BOT_NAME not specified")
    elif not bot_token:
        raise Exception("BOT_NAME set but BOT_TOKEN not specified")
    return bot_name, bot_token
