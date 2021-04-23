import re
import requests
from time import sleep
from SaitamaRobot import AI_BID, AI_API_KEY, dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin
from SaitamaRobot.modules.helper_funcs.filters import CustomFilters
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)

# This is just a temporary implementation to
# enable and disable chatbot as idk SQL
CHATBOT_ENABLED_CHATS = []


@run_async
@user_admin
def add_chat(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    is_chat = chat.id in CHATBOT_ENABLED_CHATS
    if chat.type == "private":
        msg.reply_text("You can't enable AI in PM.")
        return

    if not is_chat:
        CHATBOT_ENABLED_CHATS.append(chat.id)
        msg.reply_text("AI successfully enabled for this chat!")
    else:
        msg.reply_text("AI is already enabled for this chat!")


@run_async
@user_admin
def remove_chat(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    is_chat = chat.id in CHATBOT_ENABLED_CHATS
    if not is_chat:
        msg.reply_text("AI isn't enabled here in the first place!")
    else:
        CHATBOT_ENABLED_CHATS.remove(chat.id)
        msg.reply_text("AI disabled successfully!")


def chatbot_response(query: str, chat_id: int) -> str:
    data = requests.get(f"http://api.brainshop.ai/get?bid={AI_BID}&"
                        + f"key={AI_API_KEY}&uid={chat_id}&msg={query}")
    response = data.json()['cnt']
    return response


def check_message(context: CallbackContext, message):
    reply_msg = message.reply_to_message
    text = message.text
    if re.search("[.|\n]{0,}[s|A][a|A][i|I][t|T][a|A][m|M][a|A][.|\n]{0,}", text):
        return True
    if reply_msg:
        """
        Calling get_me() here will slow down the bot, it was initially
        like this, i did no changes However, i recommend that you should
        call this in some other file like saitama/utils/bot_info.py So
        that you can use it anywhere and whenever you want without
        making an extra request.
        """
        if reply_msg.from_user.id == context.bot.get_me().id:
            return True
    else:
        return False


@run_async
def chatbot(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    is_chat = chat_id in CHATBOT_ENABLED_CHATS
    bot = context.bot
    if not is_chat:
        return
    if msg.text and not msg.document:
        if not check_message(context, msg):
            return
        query = msg.text
        bot.send_chat_action(chat_id, action="typing")
        response = chatbot_response(query, chat_id)
        sleep(0.3)
        msg.reply_text(response, timeout=60)


@run_async
def list_chatbot_chats(update: Update, context: CallbackContext):
    text = "<b>AI-Enabled Chats</b>\n"
    for chat in CHATBOT_ENABLED_CHATS:
        x = context.bot.get_chat(chat)
        name = x.title or x.first_name
        text += f"• <code>{name}</code>\n"
    update.effective_message.reply_text(text, parse_mode="HTML")


__help__ = """
Chatbot utilizes the Branshop's API and allows Saitama to talk and provides a more interactive group chat experience.
*Commands:*
*Admins only:*
 • `/addchat`*:* Enables Chatbot mode in the chat.
 • `/rmchat`*:* Disables Chatbot mode in the chat.
*Powered by Brainshop* (brainshop.ai)
"""

ADD_CHAT_HANDLER = CommandHandler("addchat", add_chat)
REMOVE_CHAT_HANDLER = CommandHandler("rmchat", remove_chat)
CHATBOT_HANDLER = MessageHandler(
    Filters.text
    & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!") & ~Filters.regex(r"^\/")),
    chatbot,
)
LIST_CB_CHATS_HANDLER = CommandHandler(
    "listaichats", list_chatbot_chats, filters=CustomFilters.dev_filter,
)
# Filters for ignoring #note messages, !commands and sed.

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(REMOVE_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)
dispatcher.add_handler(LIST_CB_CHATS_HANDLER)

__mod_name__ = "Chatbot"
__command_list__ = ["addchat", "rmchat", "listaichats"]
__handlers__ = [
    ADD_CHAT_HANDLER,
    REMOVE_CHAT_HANDLER,
    CHATBOT_HANDLER,
    LIST_CB_CHATS_HANDLER,
]
