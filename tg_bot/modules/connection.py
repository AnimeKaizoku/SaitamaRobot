import time
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, error
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, CallbackQueryHandler
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.connection_sql as sql
from tg_bot import dispatcher, LOGGER, SUDO_USERS, spamfilters

from tg_bot.modules.helper_funcs.alternate import send_message

def disconnect_chat(bot, update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id)
    if spam == True:
        return

    if update.effective_chat.type == 'private':
        disconnection_status = sql.disconnect(update.effective_message.from_user.id)
        if disconnection_status:
           sql.disconnected_chat = send_message(update.effective_message, "Disconnected from chat!")
        else:
           send_message(update.effective_message, "You're not connected!")
    else:
        send_message(update.effective_message, "This command only available in PM")

def connected(bot, update, chat, user_id, need_admin=True):
    user = update.effective_user  # type: Optional[User]
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id)
    if spam == True:
        return
        
    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):
        conn_id = sql.get_connected_chat(user_id).chat_id
        getstatusadmin = bot.get_chat_member(conn_id, update.effective_message.from_user.id)
        isadmin = getstatusadmin.status in ('administrator', 'creator')
        ismember = getstatusadmin.status in ('member')
        isallow = sql.allow_connect_to_chat(conn_id)
        if (isadmin) or (isallow and ismember) or (user.id in SUDO_USERS):
            if need_admin == True:
                if getstatusadmin.status in ('administrator', 'creator') or user_id in SUDO_USERS:
                    return conn_id
                else:
                    send_message(update.effective_message, "You must be an admin in the connected group!")
                    raise Exception("Not admin!")
            else:
                return conn_id
        else:
            send_message(update.effective_message, "The group changed the connection rights or you are no longer an admin.\nI've disconnected you.")
            disconnect_chat(bot, update)
            raise Exception("Not admin!")
    else:
        return False

__help__ = "connection_help"

__mod_name__ = "Connection"

DISCONNECT_CHAT_HANDLER = CommandHandler("disconnect", disconnect_chat, allow_edited=True)

dispatcher.add_handler(DISCONNECT_CHAT_HANDLER)
