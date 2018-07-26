import html
from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html
from tg_bot import dispatcher, OWNER_ID, SUPPORT_USERS
import tg_bot.modules.sql.gsupport_sql as sql

@run_async
def listsupport(bot: Bot, update: Update):
    chat = update.effective_chat
    message = update.effective_message
    reply_msg = ""
    support_list = sql.get_support_list()
    for i in support_list:
       reply_msg += "\n" + str(i['name'])

    message.reply_text("<b>SUPPORT USERS:</b> {}\n".format(html.escape(reply_msg)), parse_mode=ParseMode.HTML)
    return

__mod_name__ = "Support users"
SUPPORT_HANDLER = CommandHandler("listsupport", listsupport)
dispatcher.add_handler(SUPPORT_HANDLER)
