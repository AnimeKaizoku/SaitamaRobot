from typing import Optional

import SaitamaRobot.modules.sql.rules_sql as sql
from SaitamaRobot import dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin
from SaitamaRobot.modules.helper_funcs.string_handling import markdown_parser
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Message,
                      ParseMode, Update, User)
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import escape_markdown



def get_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(
                user.id,
                "The rules shortcut for this chat hasn't been set properly! Ask admins to "
                "fix this.\nMaybe they forgot the hyphen in ID")
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = f"The rules for *{escape_markdown(chat.title)}* are:\n\n{rules}"

    if from_pm and rules:
        bot.send_message(
            user.id,
            text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
    elif from_pm:
        bot.send_message(
            user.id,
            "The group admins haven't set any rules for this chat yet. "
            "This probably doesn't mean it's lawless though...!")
    elif rules:
        update.effective_message.reply_text(
            "Please click the button below to see the rules.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text="Rules", url=f"t.me/{bot.username}?start={chat_id}")
            ]]))
    else:
        update.effective_message.reply_text(
            "The group admins haven't set any rules for this chat yet. "
            "This probably doesn't mean it's lawless though...!")



@user_admin
def set_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None,
                          1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(
            raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset)

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text(
            "Successfully set rules for this group.")



@user_admin
def clear_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Successfully cleared rules!")


def __stats__():
    return f"• {sql.num_chats()} chats have rules set."


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get('info', {}).get('rules', "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"This chat has had it's rules set: `{bool(sql.get_rules(chat_id))}`"


__help__ = """
 • `/rules`*:* get the rules for this chat.

*Admins only:*
 • `/setrules <your rules here>`*:* set the rules for this chat.
 • `/clearrules`*:* clear the rules for this chat.
"""

__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=Filters.chat_type.groups)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules, filters=Filters.chat_type.groups)
RESET_RULES_HANDLER = CommandHandler(
    "clearrules", clear_rules, filters=Filters.chat_type.groups)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
