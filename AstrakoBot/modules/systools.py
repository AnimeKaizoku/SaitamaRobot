from typing import Optional, List
import requests
import subprocess
import os
import sys

from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html
from tg_bot.modules.helper_funcs.extraction import extract_text

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.filters import CustomFilters

@run_async
def poweroff(bot: Bot, update: Update):
    msg = update.effective_message
    pid = os.getpid()
    msg.reply_text("Powering off")
    subprocess.check_output('kill '+str(pid), shell=True)
    return


SHUTDOWN_HANDLER = CommandHandler("shutdown", poweroff, filters=Filters.chat(OWNER_ID)) #safety...

dispatcher.add_handler(SHUTDOWN_HANDLER)
