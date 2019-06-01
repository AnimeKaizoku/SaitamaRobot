import logging
import sys
from contextlib import contextmanager
from telegram import Update, Bot, ParseMode
from telegram.ext import run_async

from telegram.ext import Updater, CommandHandler
from telegram.error import TimedOut, NetworkError
from telegram import ParseMode

from tg_bot.modules.disable import DisableAbleCommandHandler
from telegram.ext.dispatcher import run_async
from tg_bot.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin, sudo_plus
from tg_bot import dispatcher, LOGGER

from requests import get

# Common imports for eval
import sys
import inspect
import os
import shutil
import glob
import math
import textwrap
import os
import requests
import json
import gc
import datetime
import time
import traceback
import prettytable
import re
import io
import asyncio
import random
import subprocess
import urllib
import psutil

namespaces = {}

def namespace_of(chat):
    if chat not in namespaces:
        namespaces[chat] = {'__builtins__': globals()['__builtins__']}

    return namespaces[chat]

@contextmanager
def redirected_stdout():
    old = sys.stdout
    stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


def log_input(update):
    user = update.effective_user.id
    chat = update.effective_chat.id
    LOGGER.info("IN: {} (user={}, chat={})".format(update.effective_message.text, user, chat))

def send(msg, bot, update):
    LOGGER.info("OUT: '{}'".format(msg))
    bot.send_message(chat_id=update.effective_chat.id, text="`{}`".format(msg), parse_mode=ParseMode.MARKDOWN)

@sudo_plus
@run_async
def evaluate(bot, update):
    do(eval, bot, update)

@sudo_plus
@run_async
def execute(bot, update):
    do(exec, bot, update)


def do(func, bot, update):
    log_input(update)
    content = update.message.text.split(' ', 1)[-1]

    output = ""

    try:
        with redirected_stdout() as stdout:
            func_return = func(content, namespace_of(update.message.chat_id))

            if stdout.getvalue():
                output += str(stdout.getvalue()) + "\n"

            if func_return is not None:
                output += str(func_return)

    except Exception as e:
        output = str(e)

    output = output.strip()

    if output == "":
        output = "No output."

    send(output, bot, update)

@sudo_plus
@run_async
def clear(bot, update):
    log_input(update)
    global namespaces
    if update.message.chat_id in namespaces:
        del namespaces[update.message.chat_id]
    send("Cleared locals.", bot, update)


def error_callback(bot, update, error):
    try:
        raise error
    except (TimedOut, NetworkError):
        log.debug(error, exc_info=True)
    except:
        log.info(error, exc_info=True)

__mod_name__ = "Eval Module"

eval_handle = CommandHandler(('e', 'ev', 'eva', 'eval'), evaluate)
exec_handle = CommandHandler(('x', 'ex', 'exe', 'exec'), execute)
clear_handle = CommandHandler('clear', clear)

#dispatcher.add_handler(eval_handle)
#dispatcher.add_handler(exec_handle)
#dispatcher.add_handler(clear_handle)
#To be uncommented after testing