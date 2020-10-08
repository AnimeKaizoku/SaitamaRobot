import html
# AI module using Intellivoid's Coffeehouse API by @TheRealPhoenix
from time import sleep, time

import SaitamaRobot.modules.sql.chatbot_sql as sql
from coffeehouse.api import API
from coffeehouse.exception import CoffeeHouseError as CFError
from coffeehouse.lydia import LydiaAI
from SaitamaRobot import AI_API_KEY, OWNER_ID, SUPPORT_CHAT, dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin
from SaitamaRobot.modules.helper_funcs.filters import CustomFilters
from SaitamaRobot.modules.log_channel import gloggable
from telegram import Update
from telegram.error import BadRequest, RetryAfter, Unauthorized
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)
from telegram.utils.helpers import mention_html

CoffeeHouseAPI = API(AI_API_KEY)
api_client = LydiaAI(CoffeeHouseAPI)


@run_async
@user_admin
@gloggable
def add_chat(update: Update, context: CallbackContext):
    global api_client
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    is_chat = sql.is_chat(chat.id)
    if not is_chat:
        ses = api_client.create_session()
        ses_id = str(ses.id)
        expires = str(ses.expires)
        sql.set_ses(chat.id, ses_id, expires)
        msg.reply_text("AI successfully enabled for this chat!")
        message = (f"<b>{html.escape(chat.title)}:</b>\n"
                   f"#AI_ENABLED\n"
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        return message
    else:
        msg.reply_text("AI is already enabled for this chat!")
        return ""


@run_async
@user_admin
@gloggable
def remove_chat(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    is_chat = sql.is_chat(chat.id)
    if not is_chat:
        msg.reply_text("AI isn't enabled here in the first place!")
        return ""
    else:
        sql.rem_chat(chat.id)
        msg.reply_text("AI disabled successfully!")
        message = (f"<b>{html.escape(chat.title)}:</b>\n"
                   f"#AI_DISABLED\n"
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        return message


def check_message(context: CallbackContext, message):
    reply_msg = message.reply_to_message
    if message.text.lower() == "saitama":
        return True
    if reply_msg:
        if reply_msg.from_user.id == context.bot.get_me().id:
            return True
    else:
        return False


@run_async
def chatbot(update: Update, context: CallbackContext):
    global api_client
    msg = update.effective_message
    chat_id = update.effective_chat.id
    is_chat = sql.is_chat(chat_id)
    bot = context.bot
    if not is_chat:
        return
    if msg.text and not msg.document:
        if not check_message(context, msg):
            return
        sesh, exp = sql.get_ses(chat_id)
        query = msg.text
        try:
            if int(exp) < time():
                ses = api_client.create_session()
                ses_id = str(ses.id)
                expires = str(ses.expires)
                sql.set_ses(chat_id, ses_id, expires)
                sesh, exp = sql.get_ses(chat_id)
        except ValueError:
            pass
        try:
            bot.send_chat_action(chat_id, action='typing')
            rep = api_client.think_thought(sesh, query)
            sleep(0.3)
            msg.reply_text(rep, timeout=60)
        except CFError as e:
            bot.send_message(OWNER_ID,
                             f"Chatbot error: {e} occurred in {chat_id}!")


@run_async
def list_chatbot_chats(update: Update, context: CallbackContext):
    chats = sql.get_all_chats()
    text = "<b>AI-Enabled Chats</b>\n"
    for chat in chats:
        try:
            x = context.bot.get_chat(int(*chat))
            name = x.title if x.title else x.first_name
            text += f"• <code>{name}</code>\n"
        except BadRequest:
            sql.rem_chat(*chat)
        except Unauthorized:
            sql.rem_chat(*chat)
        except RetryAfter as e:
            sleep(e.retry_after)
    update.effective_message.reply_text(text, parse_mode="HTML")


__help__ = f"""
Chatbot utilizes the CoffeeHouse API and allows Saitama to talk and provides a more interactive group chat experience.

*Commands:* 
*Admins only:*
 • `/addchat`*:* Enables Chatbot mode in the chat.
 • `/rmchat`*:* Disables Chatbot mode in the chat.

Reports bugs at @{SUPPORT_CHAT}
*Powered by CoffeeHouse* (https://coffeehouse.intellivoid.net/) from @Intellivoid
"""

ADD_CHAT_HANDLER = CommandHandler("addchat", add_chat)
REMOVE_CHAT_HANDLER = CommandHandler("rmchat", remove_chat)
CHATBOT_HANDLER = MessageHandler(
    Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!")
                    & ~Filters.regex(r"^\/")), chatbot)
LIST_CB_CHATS_HANDLER = CommandHandler(
    "listaichats", list_chatbot_chats, filters=CustomFilters.dev_filter)
# Filters for ignoring #note messages, !commands and sed.

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(REMOVE_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)
dispatcher.add_handler(LIST_CB_CHATS_HANDLER)

__mod_name__ = "Chatbot"
__command_list__ = ["addchat", "rmchat", "listaichats"]
__handlers__ = [
    ADD_CHAT_HANDLER, REMOVE_CHAT_HANDLER, CHATBOT_HANDLER,
    LIST_CB_CHATS_HANDLER
]
