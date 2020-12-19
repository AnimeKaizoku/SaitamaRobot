import html

from SaitamaRobot import (LOGGER, DRAGONS, TIGERS, WOLVES, dispatcher)
from SaitamaRobot.modules.helper_funcs.chat_status import (user_admin,
                                                           user_not_admin)
from SaitamaRobot.modules.log_channel import loggable
from SaitamaRobot.modules.sql import reporting_sql as sql
from telegram import (Chat, InlineKeyboardButton, InlineKeyboardMarkup,
                      ParseMode, Update)
from telegram.error import BadRequest, Unauthorized
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler,
                          Filters, MessageHandler, run_async)
from telegram.utils.helpers import mention_html

REPORT_GROUP = 12
REPORT_IMMUNE_USERS = DRAGONS + TIGERS + WOLVES



@user_admin
def report_setting(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text(
                    "Turned on reporting! You'll be notified whenever anyone reports something."
                )

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text(
                    "Turned off reporting! You wont get any reports.")
        else:
            msg.reply_text(
                f"Your current report preference is: `{sql.user_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN)

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text(
                    "Turned on reporting! Admins who have turned on reports will be notified when /report "
                    "or @admin is called.")

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text(
                    "Turned off reporting! No admins will be notified on /report or @admin."
                )
        else:
            msg.reply_text(
                f"This group's current setting is: `{sql.chat_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN)



@user_not_admin
@loggable
def report(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()
        message = update.effective_message

        if not args:
            message.reply_text("Add a reason for reporting first.")
            return ""

        if user.id == reported_user.id:
            message.reply_text("Uh yeah, Sure sure...maso much?")
            return ""

        if user.id == bot.id:
            message.reply_text("Nice try.")
            return ""

        if reported_user.id in REPORT_IMMUNE_USERS:
            message.reply_text("Uh? You reporting a disaster?")
            return ""

        if chat.username and chat.type == Chat.SUPERGROUP:

            reported = f"{mention_html(user.id, user.first_name)} reported {mention_html(reported_user.id, reported_user.first_name)} to the admins!"

            msg = (
                f"<b>⚠️ Report: </b>{html.escape(chat.title)}\n"
                f"<b> • Report by:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
                f"<b> • Reported user:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
            )
            link = f'<b> • Reported message:</b> <a href="https://t.me/{chat.username}/{message.reply_to_message.message_id}">click here</a>'
            should_forward = False
            keyboard = [
                [
                    InlineKeyboardButton(
                        u"➡ Message",
                        url=f"https://t.me/{chat.username}/{message.reply_to_message.message_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        u"⚠ Kick",
                        callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}"
                    ),
                    InlineKeyboardButton(
                        u"⛔️ Ban",
                        callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        u"❎ Delete Message",
                        callback_data=f"report_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reported = f"{mention_html(user.id, user.first_name)} reported " \
                       f"{mention_html(reported_user.id, reported_user.first_name)} to the admins!"

            msg = f'{mention_html(user.id, user.first_name)} is calling for admins in "{html.escape(chat_name)}"!'
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    if not chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(
                                    message.text.split()
                            ) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)
                    if not chat.username:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(
                                    message.text.split()
                            ) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                    if chat.username and chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(
                                    message.text.split()
                            ) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    LOGGER.exception("Exception while reporting user")

        message.reply_to_message.reply_text(
            f"{mention_html(user.id, user.first_name)} reported the message to the admins.",
            parse_mode=ParseMode.HTML)
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(update, context, chat, chatP, user):
    return f"This chat is setup to send user reports to admins, via /report and @admin: `{sql.chat_should_report(chat_id)}`"


def __user_settings__(update, context, user):
    if sql.user_should_report(user.id) is True:
        text = "You will receive reports from chats you're admin."
        keyboard = [[
            InlineKeyboardButton(
                text="Disable reporting",
                callback_data="panel_reporting_U_disable")
        ]]
    else:
        text = "You will *not* receive reports from chats you're admin."
        keyboard = [[
            InlineKeyboardButton(
                text="Enable reporting",
                callback_data="panel_reporting_U_enable")
        ]]

    return text, keyboard


def buttons(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    if splitter[1] == "kick":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            bot.unbanChatMember(splitter[0], splitter[2])
            query.answer("✅ Succesfully kicked")
            return ""
        except Exception as err:
            query.answer("🛑 Failed to Punch")
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML)
    elif splitter[1] == "banned":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            query.answer("✅  Succesfully Banned")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML)
            query.answer("🛑 Failed to Ban")
    elif splitter[1] == "delete":
        try:
            bot.deleteMessage(splitter[0], splitter[3])
            query.answer("✅ Message Deleted")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML)
            query.answer("🛑 Failed to delete message!")


__help__ = """
 • `/report <reason>`*:* reply to a message to report it to admins.
 • `@admin`*:* reply to a message to report it to admins.
*NOTE:* Neither of these will get triggered if used by admins.

*Admins only:*
 • `/reports <on/off>`*:* change report setting, or view current status.
   • If done in pm, toggles your status.
   • If in group, toggles that groups's status.
"""

SETTING_HANDLER = CommandHandler("reports", report_setting)
REPORT_HANDLER = CommandHandler("report", report, filters=Filters.chat_type.groups)
ADMIN_REPORT_HANDLER = MessageHandler(Filters.regex(r"(?i)@admin(s)?"), report)

REPORT_BUTTON_USER_HANDLER = CallbackQueryHandler(buttons, pattern=r"report_")
dispatcher.add_handler(REPORT_BUTTON_USER_HANDLER)

dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)

__mod_name__ = "Reporting"
__handlers__ = [(REPORT_HANDLER, REPORT_GROUP),
                (ADMIN_REPORT_HANDLER, REPORT_GROUP), (SETTING_HANDLER)]
