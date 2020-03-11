import html

from typing import List

from telegram import Bot, Update, ParseMode
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import user_admin, bot_can_delete, dev_plus, connection_status
from tg_bot.modules.sql import cleaner_sql as sql

BLUE_TEXT_CLEAN_GROUP = 15


@run_async
def clean_blue_text_must_click(bot: Bot, update: Update):

    chat = update.effective_chat
    message = update.effective_message
    cmd = message.text.strip().split(None, 1)[0].split("/")[1]

    if sql.is_enable(chat.id):
        if not sql.is_command_ignored(cmd):
            message.delete()


@run_async
@connection_status
@bot_can_delete
@user_admin
def set_blue_text_must_click(bot: Bot, update: Update, args: List[str]):

    chat = update.effective_chat
    message = update.effective_message

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no":
            sql.set_cleanbt(chat.id, False)
            reply = "Bluetext cleaning has been disabled for <b>{}</b>".format(html.escape(chat.title))
            message.reply_text(reply, parse_mode=ParseMode.HTML)

        elif val == "yes" or val == "on":
            sql.set_cleanbt(chat.id, True)
            reply = "Bluetext cleaning has been enabled for <b>{}</b>".format(html.escape(chat.title))
            message.reply_text(reply, parse_mode=ParseMode.HTML)

        else:
            reply = "Invalid argument.Accepted values are 'yes', 'on', 'no', 'off'"
            message.reply_text(reply)
    else:
        clean_status = sql.is_enable(chat.id)
        if clean_status:
            clean_status = "Enabled"
        else:
            clean_status = "Disabled"
        reply = "Bluetext cleaning for <b>{}</b> : <b>{}</b>".format(chat.title, clean_status)
        message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@dev_plus
def add_bluetext_ignore(bot: Bot, update: Update, args: List[str]):

    message = update.effective_message

    if len(args) >= 1:
        val = args[0].lower()
        added = sql.add_clean_ignorecommand(val)
        if added:
            reply = "<b>{}</b> has been added to bluetext cleaner ignore list.".format(args[0])
        else:
            reply = "Command is already ignored."
        message.reply_text(reply, parse_mode=ParseMode.HTML)
        
    else:
        reply = "No command supplied to be ignored."
        message.reply_text(reply)


@run_async
@dev_plus
def remove_bluetext_ignore(bot: Bot, update: Update, args: List[str]):

    message = update.effective_message

    if len(args) >= 1:
        val = args[0].lower()
        removed = sql.remove_clean_ignorecommand(val)
        if removed:
            reply = "<b>{}</b> has been removed from bluetext cleaner ignore list.".format(args[0])
        else:
            reply = "Command isn't ignored currently."
        message.reply_text(reply, parse_mode=ParseMode.HTML)
        
    else:
        reply = "No command supplied to be unignored."
        message.reply_text(reply)


@run_async
@dev_plus
def bluetext_ignore_list(bot: Bot, update: Update):

    message = update.effective_message
    ignored_list = sql.get_all_ignored()
    text = "The following commands are currently ignored from bluetext cleaning :\n"

    if ignored_list:
        for ignored_command in ignored_list:
            text += f"- {ignored_command}\n"
        
        message.reply_text(text)
        return

    text = "No commands are currently ignored from bluetext cleaning."
    message.reply_text(text)
    return

__help__ = """
 - /cleanbluetext <on/off/yes/no> - clean commands after sending
"""

SET_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("cleanbluetext", set_blue_text_must_click, pass_args=True)
ADD_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("addcleanbluetext", add_bluetext_ignore, pass_args=True)
REMOVE_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("removecleanbluetext", remove_bluetext_ignore, pass_args=True)
LIST_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("listcleanbluetext", bluetext_ignore_list)
CLEAN_BLUE_TEXT_HANDLER = MessageHandler(Filters.command & Filters.group, clean_blue_text_must_click)

dispatcher.add_handler(SET_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(ADD_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(REMOVE_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(LIST_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP)

__mod_name__ = "Bluetext Cleaning"
__handlers__ = [SET_CLEAN_BLUE_TEXT_HANDLER, ADD_CLEAN_BLUE_TEXT_HANDLER, REMOVE_CLEAN_BLUE_TEXT_HANDLER,
                LIST_CLEAN_BLUE_TEXT_HANDLER, (CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP)]
