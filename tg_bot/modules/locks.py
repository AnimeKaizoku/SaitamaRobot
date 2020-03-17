import html
from typing import List

import telegram.ext as tg
from telegram import Bot, Update, ParseMode, MessageEntity
from telegram import TelegramError
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.locks_sql as sql
from tg_bot import dispatcher, SUDO_USERS, DEV_USERS, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import (can_delete, is_user_admin, user_not_admin, user_admin,
                                                     bot_can_delete, is_bot_admin, connection_status)
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.log_channel import loggable

LOCK_TYPES = {
    'sticker': Filters.sticker,
    'audio': Filters.audio,
    'voice': Filters.voice,
    'document': Filters.document,
    'video': Filters.video,
    'contact': Filters.contact,
    'photo': Filters.photo,
    'gif': Filters.document & CustomFilters.mime_type("video/mp4"),
    'url': Filters.entity(MessageEntity.URL) | Filters.caption_entity(MessageEntity.URL),
    'bots': Filters.status_update.new_chat_members,
    'forward': Filters.forwarded,
    'game': Filters.game,
    'location': Filters.location,
}

GIF = Filters.document & CustomFilters.mime_type("video/mp4")
OTHER = Filters.game | Filters.sticker | GIF
MEDIA = Filters.audio | Filters.document | Filters.video | Filters.voice | Filters.photo
MESSAGES = Filters.text | Filters.contact | Filters.location | Filters.venue | Filters.command | MEDIA | OTHER
PREVIEWS = Filters.entity("url")

RESTRICTION_TYPES = {
    'messages': MESSAGES,
    'media': MEDIA,
    'other': OTHER,
    # 'previews': PREVIEWS, # NOTE: this has been removed cos its useless atm.
    'all': Filters.all
}

PERM_GROUP = 1
REST_GROUP = 2


class CustomCommandHandler(tg.CommandHandler):
    def __init__(self, command, callback, **kwargs):
        super().__init__(command, callback, **kwargs)

    def check_update(self, update):
        return super().check_update(update) and not (
                sql.is_restr_locked(update.effective_chat.id, 'messages') and not is_user_admin(update.effective_chat,
                                                                                                update.effective_user.id))


tg.CommandHandler = CustomCommandHandler


# NOT ASYNC
def restr_members(bot, chat_id, members, messages=False, media=False, other=False, previews=False):
    for mem in members:
        if mem.user in SUDO_USERS or mem.user in DEV_USERS:
            pass
        try:
            bot.restrict_chat_member(chat_id, mem.user,
                                     can_send_messages=messages,
                                     can_send_media_messages=media,
                                     can_send_other_messages=other,
                                     can_add_web_page_previews=previews)
        except TelegramError:
            pass


# NOT ASYNC
def unrestr_members(bot, chat_id, members, messages=True, media=True, other=True, previews=True):
    for mem in members:
        try:
            bot.restrict_chat_member(chat_id, mem.user,
                                     can_send_messages=messages,
                                     can_send_media_messages=media,
                                     can_send_other_messages=other,
                                     can_add_web_page_previews=previews)
        except TelegramError:
            pass


@run_async
@connection_status
def locktypes(bot: Bot, update: Update):
    update.effective_message.reply_text("\n - ".join(["Locks: "] + list(LOCK_TYPES) + list(RESTRICTION_TYPES)))


@user_admin
@connection_status
@bot_can_delete
@loggable
def lock(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if can_delete(chat, bot.id):
        if len(args) >= 1:
            if args[0] in LOCK_TYPES:
                sql.update_lock(chat.id, args[0], locked=True)
                message.reply_text("Locked {} messages for all non-admins!".format(args[0]))

                return (f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#LOCK\n"
                        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                        f"Locked <code>{args[0]}</code>.")

            elif args[0] in RESTRICTION_TYPES:
                sql.update_restriction(chat.id, args[0], locked=True)
                """
                if args[0] == "messages":
                    chat.set_permissions(can_send_messages=False)

                elif args[0] == "media":
                    chat.set_permissions(can_send_media_messages=False)

                elif args[0] == "other":
                    chat.set_permissions(can_send_other_messages=False)

                elif args[0] == "previews":
                    chat.set_permissions(can_add_web_page_previews=False)

                elif args[0] == "all":
                    chat.set_permissions(can_send_messages=False)
                """
                message.reply_text("Locked {} for all non-admins!".format(args[0]))
                return (f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#LOCK\n"
                        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                        f"Locked <code>{args[0]}</code>.")

            else:
                message.reply_text("What are you trying to lock...? Try /locktypes for the list of lockables")

    else:
        message.reply_text("I'm not an administrator, or haven't got delete rights.")

    return ""


@run_async
@connection_status
@user_admin
@loggable
def unlock(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if is_user_admin(chat, message.from_user.id):
        if len(args) >= 1:
            if args[0] in LOCK_TYPES:
                sql.update_lock(chat.id, args[0], locked=False)
                message.reply_text(f"Unlocked {args[0]} for everyone!")
                return (f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#UNLOCK\n"
                        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                        f"Unlocked <code>{args[0]}</code>.")

            elif args[0] in RESTRICTION_TYPES:
                sql.update_restriction(chat.id, args[0], locked=False)
                """
                #members = users_sql.get_chat_members(chat.id)
                if args[0] == "messages":
                    chat.set_permissions(can_send_messages=True)

                elif args[0] == "media":
                    chat.set_permissions(can_send_media_messages=True)

                elif args[0] == "other":
                    chat.set_permissions(can_send_other_messages=True)

                elif args[0] == "previews":
                    chat.set_permissions(can_add_web_page_previews=True)

                elif args[0] == "all":
                    chat.set_permissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True, can_send_polls=True)
                """
                message.reply_text("Unlocked {} for everyone!".format(args[0]))

                return (f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#UNLOCK\n"
                        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                        f"Unlocked <code>{args[0]}</code>.")
            else:
                message.reply_text("What are you trying to unlock...? Try /locktypes for the list of lockables")

        else:
            bot.sendMessage(chat.id, "What are you trying to unlock...?")

    return ""


@run_async
@user_not_admin
def del_lockables(bot: Bot, update: Update):
    chat = update.effective_chat
    message = update.effective_message

    for lockable, filter in LOCK_TYPES.items():
        if filter(message) and sql.is_locked(chat.id, lockable) and can_delete(chat, bot.id):
            if lockable == "bots":
                new_members = update.effective_message.new_chat_members
                for new_mem in new_members:
                    if new_mem.is_bot:
                        if not is_bot_admin(chat, bot.id):
                            message.reply_text("I see a bot, and I've been told to stop them joining... "
                                               "but I'm not admin!")
                            return

                        chat.kick_member(new_mem.id)
                        message.reply_text("Only admins are allowed to add bots to this chat! Behave or I'll punch you.")
            else:
                try:
                    message.delete()
                except BadRequest as excp:
                    if excp.message == "Message to delete not found":
                        pass
                    else:
                        LOGGER.exception("ERROR in lockables")

            break


@run_async
@user_not_admin
def rest_handler(bot: Bot, update: Update):
    msg = update.effective_message
    chat = update.effective_chat
    for restriction, _filter in RESTRICTION_TYPES.items():
        if _filter(msg) and sql.is_restr_locked(chat.id, restriction) and can_delete(chat, bot.id):
            try:
                msg.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("ERROR in restrictions")
            break


def format_lines(lst, spaces):
    widths = [max([len(str(lst[i][j])) for i in range(len(lst))]) for j in range(len(lst[0]))]

    lines = [(" " * spaces).join(
        [" " * int((widths[i] - len(str(r[i]))) / 2) + str(r[i])
         + " " * int((widths[i] - len(str(r[i])) + (1 if widths[i] % 2 != len(str(r[i])) % 2 else 0)) / 2)
         for i in range(len(r))]) for r in lst]

    return "\n".join(lines)


def repl(lst, index, true_val, false_val):
    return [t[0:index] + [true_val if t[index] else false_val] + t[index + 1:len(t)] for t in lst]


def build_lock_message(chat_id):
    locks = sql.get_locks(chat_id)
    restr = sql.get_restr(chat_id)

    if not (locks or restr):
        res = "There are no current locks in this chat."
    else:
        res = "These are the locks in this chat:\n"
        ls = []
        if locks:
            ls += repl([["sticker", "=", locks.sticker], ["audio", "=", locks.audio], ["voice", "=", locks.voice],
                        ["document", "=", locks.document], ["video", "=", locks.video], ["contact", "=", locks.contact],
                        ["photo", "=", locks.photo], ["gif", "=", locks.gif], ["url", "=", locks.url],
                        ["bots", "=", locks.bots], ["forward", "=", locks.forward], ["game", "=", locks.game],
                        ["location", "=", locks.location]]
                       , 2, "Locked", "Unlocked")
        if restr:
            ls += repl([["messages", "=", restr.messages], ["media", "=", restr.media],
                        ["other", "=", restr.other], ["previews", "=", restr.preview],
                        ["all", "=", all([restr.messages, restr.media, restr.other, restr.preview])]]
                       , 2, "Restricted", "Unrestricted")
        # DON'T REMOVE THE NEWLINE BELOW
        res += "```\n" + format_lines(ls, 1) + "```"
    return res


@run_async
@connection_status
@user_admin
def list_locks(bot: Bot, update: Update):
    chat = update.effective_chat

    res = build_lock_message(chat.id)

    update.effective_message.reply_text(res, parse_mode=ParseMode.MARKDOWN)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return build_lock_message(chat_id)


__help__ = """
 - /locktypes: a list of possible locktypes

*Admin only:*
 - /lock <type>: lock items of a certain type (not available in private)
 - /unlock <type>: unlock items of a certain type (not available in private)
 - /locks: the current list of locks in this chat.

Locks can be used to restrict a group's users.
eg:
Locking urls will auto-delete all messages with urls which haven't been whitelisted, locking stickers will delete all \
stickers, etc.
Locking bots will stop non-admins from adding bots to the chat.
"""

LOCKTYPES_HANDLER = DisableAbleCommandHandler("locktypes", locktypes)
LOCK_HANDLER = CommandHandler("lock", lock, pass_args=True)
UNLOCK_HANDLER = CommandHandler("unlock", unlock, pass_args=True)
LOCKED_HANDLER = CommandHandler("locks", list_locks)
LOCKABLE_HANDLER = MessageHandler(Filters.all & Filters.group, del_lockables)
RESTRICTION_HANDLER = MessageHandler(Filters.all & Filters.group, rest_handler)

dispatcher.add_handler(LOCK_HANDLER)
dispatcher.add_handler(UNLOCK_HANDLER)
dispatcher.add_handler(LOCKTYPES_HANDLER)
dispatcher.add_handler(LOCKED_HANDLER)
dispatcher.add_handler(LOCKABLE_HANDLER, PERM_GROUP)
dispatcher.add_handler(RESTRICTION_HANDLER, REST_GROUP)

__mod_name__ = "Locks"
__handlers__ = [LOCKTYPES_HANDLER, LOCK_HANDLER, UNLOCK_HANDLER, LOCKED_HANDLER, (LOCKABLE_HANDLER, PERM_GROUP),
                (RESTRICTION_HANDLER, REST_GROUP)]
