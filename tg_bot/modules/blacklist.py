import html
import re
from typing import List

from telegram import Bot, Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async

import tg_bot.modules.sql.blacklist_sql as sql
from tg_bot import dispatcher, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin, user_not_admin, connection_status
from tg_bot.modules.helper_funcs.extraction import extract_text
from tg_bot.modules.helper_funcs.misc import split_message

BLACKLIST_GROUP = 11


@run_async
@connection_status
@user_admin
def blacklist(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    chat = update.effective_chat

    update_chat_title = chat.title
    message_chat_title = update.effective_message.chat.title

    if update_chat_title == message_chat_title:
        base_blacklist_string = "Current <b>blacklisted</b> words:\n"
    else:
        base_blacklist_string = f"Current <b>blacklisted</b> words in <b>{update_chat_title}</b>:\n"

    all_blacklisted = sql.get_chat_blacklist(chat.id)

    filter_list = base_blacklist_string

    if len(args) > 0 and args[0].lower() == 'copy':
        for trigger in all_blacklisted:
            filter_list += f"<code>{html.escape(trigger)}</code>\n"
    else:
        for trigger in all_blacklisted:
            filter_list += f" - <code>{html.escape(trigger)}</code>\n"

    split_text = split_message(filter_list)
    for text in split_text:
        if text == base_blacklist_string:
            if update_chat_title == message_chat_title:
                msg.reply_text("There are no blacklisted messages here!")
            else:
                msg.reply_text(f"There are no blacklisted messages in <b>{update_chat_title}</b>!",
                               parse_mode=ParseMode.HTML)
            return
        msg.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
@connection_status
@user_admin
def add_blacklist(bot: Bot, update: Update):
    msg = update.effective_message
    chat = update.effective_chat
    words = msg.text.split(None, 1)

    if len(words) > 1:
        text = words[1]
        to_blacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))

        for trigger in to_blacklist:
            try:
                re.compile(trigger)
            except Exception as exce:
                msg.reply_text(f"Couldn't add regex, Error: {exce}")
                return
            sql.add_to_blacklist(chat.id, trigger.lower())

        if len(to_blacklist) == 1:
            msg.reply_text(f"Added <code>{html.escape(to_blacklist[0])}</code> to the blacklist!",
                           parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(f"Added <code>{len(to_blacklist)}</code> triggers to the blacklist.",
                           parse_mode=ParseMode.HTML)

    else:
        msg.reply_text("Tell me which words you would like to remove from the blacklist.")


@run_async
@connection_status
@user_admin
def unblacklist(bot: Bot, update: Update):
    msg = update.effective_message
    chat = update.effective_chat
    words = msg.text.split(None, 1)

    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
        successful = 0

        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat.id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                msg.reply_text(f"Removed <code>{html.escape(to_unblacklist[0])}</code> from the blacklist!",
                               parse_mode=ParseMode.HTML)
            else:
                msg.reply_text("This isn't a blacklisted trigger...!")

        elif successful == len(to_unblacklist):
            msg.reply_text(f"Removed <code>{successful}</code> triggers from the blacklist.", parse_mode=ParseMode.HTML)

        elif not successful:
            msg.reply_text("None of these triggers exist, so they weren't removed.", parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(f"Removed <code>{successful}</code> triggers from the blacklist."
                           f" {len(to_unblacklist) - successful} did not exist, so were not removed.",
                           parse_mode=ParseMode.HTML)
    else:
        msg.reply_text("Tell me which words you would like to remove from the blacklist.")


@run_async
@connection_status
@user_not_admin
def del_blacklist(bot: Bot, update: Update):
    chat = update.effective_chat
    message = update.effective_message
    to_match = extract_text(message)
    msg = update.effective_message
    if not to_match:
        return

    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + trigger + r"( |$|[^\w])"
        try:
          match = re.search(pattern, to_match, flags=re.IGNORECASE)
        except Exception:
          sql.rm_from_blacklist(chat.id, trigger)
          msg.reply_text(f'Removed {trigger} from blacklist because of broken regex')
          return
        if match:
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("Error while deleting blacklist message.")
            break


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return "There are {} blacklisted words.".format(blacklisted)


def __stats__():
    return "{} blacklist triggers, across {} chats.".format(sql.num_blacklist_filters(),
                                                            sql.num_blacklist_filter_chats())


__help__ = """
Blacklists are used to stop certain triggers from being said in a group. Any time the trigger is mentioned, \
the message will immediately be deleted. A good combo is sometimes to pair this up with warn filters!

*NOTE:* blacklists do not affect group admins.

 - /blacklist: View the current blacklisted words.

*Admin only:*
 - /addblacklist <triggers>: Add a trigger to the blacklist. Each line is considered one trigger, so using different \
lines will allow you to add multiple triggers.
 - /unblacklist <triggers>: Remove triggers from the blacklist. Same newline logic applies here, so you can remove \
multiple triggers at once.
 - /rmblacklist <triggers>: Same as above.
"""

BLACKLIST_HANDLER = DisableAbleCommandHandler("blacklist", blacklist, pass_args=True)
ADD_BLACKLIST_HANDLER = CommandHandler("addblacklist", add_blacklist)
UNBLACKLIST_HANDLER = CommandHandler(["unblacklist", "rmblacklist"], unblacklist)
BLACKLIST_DEL_HANDLER = MessageHandler((Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.group, del_blacklist, edited_updates=True)
dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)

__mod_name__ = "Blacklist Word"
__handlers__ = [BLACKLIST_HANDLER, ADD_BLACKLIST_HANDLER, UNBLACKLIST_HANDLER, (BLACKLIST_DEL_HANDLER, BLACKLIST_GROUP)]
