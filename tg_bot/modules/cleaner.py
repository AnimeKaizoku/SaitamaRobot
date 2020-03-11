import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async
from telegram.utils.helpers import mention_html, escape_markdown

from emilia import dispatcher, spamfilters
from emilia.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict
from emilia.modules.helper_funcs.string_handling import extract_time
from emilia.modules.disable import DisableAbleCommandHandler
from emilia.modules.log_channel import loggable
from emilia.modules.sql import cleaner_sql as sql
from emilia.modules.connection import connected

from emilia.modules.languages import tl
from emilia.modules.helper_funcs.alternate import send_message


@run_async
def clean_blue_text_must_click(bot: Bot, update: Update):
	if sql.is_enable(update.effective_chat.id):
		update.effective_message.delete()

@run_async
@user_admin
def set_blue_text_must_click(bot: Bot, update: Update, args):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	message = update.effective_message  # type: Optional[Message]
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return

	conn = connected(bot, update, chat, user.id, need_admin=True)
	if conn:
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		if update.effective_message.chat.type == "private":
			send_message(update.effective_message, tl(update.effective_message, "Anda bisa lakukan command ini pada grup, bukan pada PM"))
			return ""
		chat_id = update.effective_chat.id
		chat_name = update.effective_message.chat.title

	if len(args) >= 1:
		val = args[0].lower()
		if val == "off" or val == "no":
			sql.set_cleanbt(chat_id, False)
			if conn:
				text = tl(update.effective_message, "Penghapus pesan biru telah di non-aktifkan di *{}*.").format(chat_name)
			else:
				text = tl(update.effective_message, "Penghapus pesan biru telah di non-aktifkan.")
			send_message(update.effective_message, text, parse_mode="markdown")

		elif val == "yes" or val == "ya" or val == "on":
			sql.set_cleanbt(chat_id, True)
			if conn:
				text = tl(update.effective_message, "Penghapus pesan biru telah di *aktifkan* di *{}*.").format(chat_name)
			else:
				text = tl(update.effective_message, "Penghapus pesan biru telah di *aktifkan*.")
			send_message(update.effective_message, text, parse_mode="markdown")

		else:
			send_message(update.effective_message, tl(update.effective_message, "Argumen tidak dikenal - harap gunakan 'yes', atau 'no'."))
	else:
		send_message(update.effective_message, tl(update.effective_message, "Pengaturan untuk penghapus pesan biru saat ini: *{}*").format("Enabled" if sql.is_enable(chat_id) else "Disabled"), parse_mode="markdown")


SET_CLEAN_BLUE_TEXT_HANDLER = DisableAbleCommandHandler("cleanbluetext", set_blue_text_must_click, pass_args=True)
CLEAN_BLUE_TEXT_HANDLER = MessageHandler(Filters.command & Filters.group, clean_blue_text_must_click)


dispatcher.add_handler(SET_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(CLEAN_BLUE_TEXT_HANDLER, 15)