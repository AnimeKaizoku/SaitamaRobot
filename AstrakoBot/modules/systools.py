import subprocess
import os

from telegram import Update, Bot
from telegram.ext import CommandHandler, run_async, Filters

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS
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
