# Haruka Aya  
# Copyright (C) 2020  HarukaNetwork https://github.com/HarukaNetwork
import html
from typing import Optional, List
import re
from telegram import Message, Chat, Update, Bot, User, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, RegexHandler, run_async, Filters, CallbackQueryHandler
from telegram.utils.helpers import mention_html

from tg_bot.modules.helper_funcs.chat_status import user_not_admin, user_admin
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import reporting_sql as sql
from tg_bot import dispatcher, LOGGER, SUDO_USERS, TIGER_USERS

REPORT_GROUP = 5
REPORT_IMMUNE_USERS = SUDO_USERS + TIGER_USERS

@run_async
@user_admin
def report_setting(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text("Turned on reporting! You'll be notified whenever anyone reports something.")

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text("Turned off reporting! You wont get any reports.")
        else:
            msg.reply_text("Your current report preference is: `{}`".format(sql.user_should_report(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text("Turned on reporting! Admins who have turned on reports will be notified when /report "
                               "or @admin are called.")

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text("Turned off reporting! No admins will be notified on /report or @admin.")
        else:
            msg.reply_text("This chat's current setting is: `{}`".format(sql.chat_should_report(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)


@run_async
@user_not_admin
@loggable
def report(bot: Bot, update: Update) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user  # type: Optional[User]
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()

        if reported_user.id in REPORT_IMMUNE_USERS:
            message.reply_text("Uh? You reporting whitelisted users?")
            return ""

        if chat.username and chat.type == Chat.SUPERGROUP:
            msg = "<b>{}:</b>" \
                  "\n<b>Reported user:</b> {} (<code>{}</code>)" \
                  "\n<b>Reported by:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                                      mention_html(
                                                                          reported_user.id,
                                                                          reported_user.first_name),
                                                                      reported_user.id,
                                                                      mention_html(user.id,
                                                                                   user.first_name),
                                                                      user.id)
            link = "\n<b>Link:</b> " \
                   "<a href=\"http://telegram.me/{}/{}\">click here</a>".format(chat.username, message.message_id)

            should_forward = False
            keyboard = [
                [InlineKeyboardButton(u"➡ Message", url="https://t.me/{}/{}".format(chat.username, str(
                    message.reply_to_message.message_id)))],
                [InlineKeyboardButton(u"⚠ Kick",
                                      callback_data="report_{}=kick={}={}".format(chat.id, reported_user.id,
                                                                                  reported_user.first_name)),
                 InlineKeyboardButton(u"⛔️ Ban",
                                      callback_data="report_{}=banned={}={}".format(chat.id, reported_user.id,
                                                                                    reported_user.first_name))],
                [InlineKeyboardButton(u"❎ Delete Message",
                                      callback_data="report_{}=delete={}={}".format(chat.id, reported_user.id,
                                                                                    message.reply_to_message.message_id))]]
            reply_markup = InlineKeyboardMarkup(keyboard)

        else:
            msg = "{} is calling for admins in \"{}\"!".format(mention_html(user.id, user.first_name),
                                                               html.escape(chat_name))
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    if not chat.type == Chat.SUPERGROUP:
                        bot.send_message(admin.user.id, msg + link, parse_mode=ParseMode.HTML)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(message.text.split()) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                    if not chat.username:
                        bot.send_message(admin.user.id, msg + link, parse_mode=ParseMode.HTML)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(message.text.split()) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                    if chat.username and chat.type == Chat.SUPERGROUP:
                        bot.send_message(admin.user.id, msg + link, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(message.text.split()) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    LOGGER.exception("Exception while reporting user")

        message.reply_to_message.reply_text("{} reported the message to the admins.".
                                            format(mention_html(user.id, user.first_name)),
                                            parse_mode=ParseMode.HTML)
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(bot, update, chat, chatP, user):
    return "This chat is setup to send user reports to admins, via /report and @admin: `{}`".format(
        sql.chat_should_report(chat.id))


def __user_settings__(bot, update, user):
    if sql.user_should_report(user.id) == True:
        text = "You will receive reports from chats you're admin."
        keyboard = [[InlineKeyboardButton(text="Disable reporting", callback_data="panel_reporting_U_disable")]]
    else:
        text = "You will *not* receive reports from chats you're admin."
        keyboard = [[InlineKeyboardButton(text="Enable reporting", callback_data="panel_reporting_U_enable")]]

    return text, keyboard

    
def control_panel_user(bot, update):
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat
    query = update.callback_query
    enable = re.match(r"panel_reporting_U_enable", query.data)
    disable = re.match(r"panel_reporting_U_disable", query.data)

    query.message.delete()

    if enable:
        sql.set_user_setting(chat.id, True)
        text = "Enabled reporting in your pm!"
    else:
        sql.set_user_setting(chat.id, False)
        text = "Disabled reporting in your pm!"

    keyboard = [[InlineKeyboardButton(text="⬅️ Back", callback_data="cntrl_panel_U(1)")]]

    update.effective_message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


def buttons(bot: Bot, update):
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    if splitter[1] == "kick":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            bot.unbanChatMember(splitter[0], splitter[2])
            query.answer("✅ Succesfully kicked")
            return ""
        except Exception as err:
            query.answer("❎ Failed to kick")
            bot.sendMessage(text="Error: {}".format(err),
                            chat_id=query.message.chat_id,
                            parse_mode=ParseMode.HTML)
    elif splitter[1] == "banned":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            query.answer("✅  Succesfully Banned")
            return ""
        except Exception as err:
            bot.sendMessage(text="Error: {}".format(err),
                            chat_id=query.message.chat_id,
                            parse_mode=ParseMode.HTML)
            query.answer("❎ Failed to ban")
    elif splitter[1] == "delete":
        try:
            bot.deleteMessage(splitter[0], splitter[3])
            query.answer("✅ Message Deleted")
            return ""
        except Exception as err:
            bot.sendMessage(text="Error: {}".format(err),
                                  chat_id=query.message.chat_id,
                                  parse_mode=ParseMode.HTML)
            query.answer("❎ Failed to delete message!")


__mod_name__ = "Reporting"

__help__ = """
 - /report <reason>: reply to a message to report it to admins.
 - @admin: reply to a message to report it to admins.
NOTE: neither of these will get triggered if used by admins
*Admin only:*
 - /reports <on/off>: change report setting, or view current status.
   - If done in pm, toggles your status.
   - If in chat, toggles that chat's status.
"""

REPORT_HANDLER = CommandHandler("report", report, filters=Filters.group)
SETTING_HANDLER = CommandHandler("reports", report_setting, pass_args=True)
ADMIN_REPORT_HANDLER = RegexHandler("(?i)@admin(s)?", report)

cntrl_panel_user_callback_handler = CallbackQueryHandler(control_panel_user, pattern=r"panel_reporting_U")
report_button_user_handler = CallbackQueryHandler(buttons, pattern=r"report_")
dispatcher.add_handler(cntrl_panel_user_callback_handler)
dispatcher.add_handler(report_button_user_handler)

dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(SETTING_HANDLER)
