from future.utils import string_types

from telegram import Update, MessageEntity
from telegram.ext import CommandHandler, RegexHandler, MessageHandler, Filters

import SaitamaRobot.modules.sql.blacklistusers_sql as sql
from SaitamaRobot import ALLOW_EXCL, dispatcher

if ALLOW_EXCL:
    CMD_STARTERS = ('/', '!')
else:
    CMD_STARTERS = ('/',)


class CustomCommandHandler(CommandHandler):

    def __init__(self, command, callback, admin_ok=False, filters=None, **kwargs):
        super().__init__(command, callback, **kwargs)
        if filters:
            self.filters = Filters.update.messages & filters
        else:
            self.filters = Filters.update.messages

    def check_update(self, update):
        if isinstance(update, Update) and update.effective_message:
            message = update.effective_message

            if sql.is_user_blacklisted(update.effective_user.id):
                return False

            if message.text and len(message.text) > 1:
                fst_word = message.text_html.split(None, 1)[0]

                if len(fst_word) > 1 and any(fst_word.startswith(start) for start in CMD_STARTERS):
                    command = fst_word[1:].split('@')
                    command.append(message.bot.username)  # in case the command was sent without a username
                    args = message.text.split()[1:]

                    if not (command[0].lower() in self.command and command[1].lower() == message.bot.username.lower()):
                        return None

                    res = self.filters(update)
                    if res:
                        return args, res
                    else:
                        return False

            return False


class CustomRegexHandler(RegexHandler):
    def __init__(self, pattern, callback, friendly="", **kwargs):
        super().__init__(pattern, callback, **kwargs)


class CustomMessageHandler(MessageHandler):
    def __init__(self, filters, callback, friendly="", **kwargs):
        super().__init__(filters, callback, **kwargs)
