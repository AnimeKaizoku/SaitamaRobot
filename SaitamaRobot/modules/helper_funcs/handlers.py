from telegram import Update
from telegram.ext import CommandHandler, MessageHandler

import SaitamaRobot.modules.sql.blacklistusers_sql as sql
from SaitamaRobot import ALLOW_EXCL

if ALLOW_EXCL:
    CMD_STARTERS = ('/', '!')
else:
    CMD_STARTERS = ('/',)


class CustomCommandHandler(CommandHandler):

    def __init__(self, command, callback, **kwargs):

        if "admin_ok" in kwargs:
            del kwargs["admin_ok"]
        super().__init__(command, callback, **kwargs)
