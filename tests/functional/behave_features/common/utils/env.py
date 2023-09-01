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

def get_dry_run():
    # Accepts 'true' or 'false', depending on whether we want to notify
    # Don't notify on dry runs, default to True
    dry_run = False if os.environ.get("DRY_RUN") == 'false' else True
    # Don't notify if not triggerd on PROD_REPO and PROD_BRANCH
    if not dry_run:
        triggered_branch = os.environ.get("GITHUB_REF").split('/')[-1]
        triggered_repo = os.environ.get("GITHUB_REPOSITORY")
        if triggered_repo != PROD_REPO or triggered_branch != PROD_BRANCH:
            dry_run = True
    return dry_run

def get_notify_id():
    # Accepts comma separated Github IDs or empty strings to override people to tag in notifications
    notify_id = os.environ.get("NOTIFY_ID")
    if notify_id:
        notify_id = [vt.strip() for vt in notify_id.split(',')]
    else:
        notify_id = ["dperaza","mmulholla"]
    return notify_id

def get_software_name_version():
    software_name = os.environ.get("SOFTWARE_NAME")
    if not software_name:
        raise Exception("SOFTWARE_NAME environment variable not defined")

    software_version = os.environ.get("SOFTWARE_VERSION").strip('\"')
    if not software_version:
        raise Exception("SOFTWARE_VERSION environment variable not defined")
    elif software_version.startswith("sha256"):
        software_version = software_version[-8:]

    return software_name, software_version

def get_vendor_type():
    vendor_type = os.environ.get("VENDOR_TYPE")
    if not vendor_type:
        logging.info(
            f"VENDOR_TYPE environment variable not defined, default to `all`")
        vendor_type = 'all'
    return vendor_type