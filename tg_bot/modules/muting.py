import html

from typing import Optional, List

from telegram import Bot, Chat, Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import (bot_admin, user_admin, is_user_admin, can_restrict,
                                                     connection_status)
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


def check_user(user_id: int, bot: Bot, chat: Chat) -> Optional[str]:
    if not user_id:
        reply = "You don't seem to be referring to a user."
        return reply

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            reply = "I can't seem to find this user"
            return reply
        else:
            raise

    if user_id == bot.id:
        reply = "I'm not gonna MUTE myself, How high are you?"
        return reply

    if is_user_admin(chat, user_id, member):
        reply = "I really wish I could mute admins...Perhaps a Punch?"
        return reply

    return None


@run_async
@connection_status
@bot_admin
@user_admin
@loggable
def mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    log = (f"<b>{html.escape(chat.title)}:</b>\n"
           f"#MUTE\n"
           f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
           f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}")

    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    if member.can_send_messages is None or member.can_send_messages:
        bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
        bot.sendMessage(chat.id, f"Muted <b>{html.escape(member.user.first_name)}</b> with no expiration date!",
                        parse_mode=ParseMode.HTML)
        return log

    else:
        message.reply_text("This user is already muted!")

    return ""


@run_async
@connection_status
@bot_admin
@user_admin
@loggable
def unmute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You'll need to either give me a username to unmute, or reply to someone to be unmuted.")
        return ""

    member = chat.get_member(int(user_id))

    if member.status != 'kicked' and member.status != 'left':
        if (member.can_send_messages
                and member.can_send_media_messages
                and member.can_send_other_messages
                and member.can_add_web_page_previews):
            message.reply_text("This user already has the right to speak.")
        else:
            bot.restrict_chat_member(chat.id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)
            bot.sendMessage(chat.id, f"I shall allow <b>{html.escape(member.user.first_name)}</b> to text!",
                            parse_mode=ParseMode.HTML)
            return (f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#UNMUTE\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}")
    else:
        message.reply_text("This user isn't even in the chat, unmuting them won't make them talk more than they "
                           "already do!")

    return ""


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    if not reason:
        message.reply_text("You haven't specified a time to mute this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (f"<b>{html.escape(chat.title)}:</b>\n"
           f"#TEMP MUTED\n"
           f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
           f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
           f"<b>Time:</b> {time_val}")
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    try:
        if member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, until_date=mutetime, can_send_messages=False)
            bot.sendMessage(chat.id, f"Muted <b>{html.escape(member.user.first_name)}</b> for {time_val}!",
                            parse_mode=ParseMode.HTML)
            return log
        else:
            message.reply_text("This user is already muted.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(f"Muted for {time_val}!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR muting user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't mute that user.")

    return ""


__help__ = """
*Admin only:*
 - /mute <userhandle>: silences a user. Can also be used as a reply, muting the replied to user.
 - /tmute <userhandle> x(m/h/d): mutes a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unmute <userhandle>: unmutes a user. Can also be used as a reply, muting the replied to user.
"""

MUTE_HANDLER = CommandHandler("mute", mute, pass_args=True)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, pass_args=True)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute, pass_args=True)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)

__mod_name__ = "Muting"
__handlers__ = [MUTE_HANDLER, UNMUTE_HANDLER, TEMPMUTE_HANDLER]
