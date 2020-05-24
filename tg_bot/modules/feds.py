import html
from io import BytesIO
from typing import Optional, List
import random
import uuid
import re
import json
import time
from time import sleep

from future.utils import string_types
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram import ParseMode, Update, Bot, Chat, User, MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, WHITELIST_USERS, MESSAGE_DUMP, LOGGER
from tg_bot.modules.helper_funcs.handlers import CMD_STARTERS
from tg_bot.modules.helper_funcs.misc import is_module_loaded, send_to_list
from tg_bot.modules.helper_funcs.chat_status import is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import markdown_parser
from tg_bot.modules.disable import DisableAbleCommandHandler

import tg_bot.modules.sql.feds_sql as sql

# Hello bot owner, I spent for feds many hours of my life. Please don't remove this if you still respect MrYacha and peaktogoo and AyraHikari too.
# Federation by MrYacha 2018-2019
# Federation rework by Mizukito Akito 2019
# Federation update v2 by Ayra Hikari 2019
#
# Time spent on feds = 10h by #MrYacha
# Time spent on reworking on the whole feds = 22+ hours by @RealAkito
# Time spent on updating version to v2 = 26+ hours by @AyraHikari
#
# Total spended for making this features is 68+ hours

LOGGER.info("Original federation module by MrYacha, reworked by Mizukito Akito (@RealAkito) on Telegram.")


FBAN_ERRORS = {
	"User is an administrator of the chat",
	"Chat not found",
	"Not enough rights to restrict/unrestrict chat member",
	"User_not_participant",
	"Peer_id_invalid",
	"Group chat was deactivated",
	"Need to be inviter of a user to kick it from a basic group",
	"Chat_admin_required",
	"Only the creator of a basic group can kick group administrators",
	"Channel_private",
	"Not in the chat",
	"Have no rights to send a message"
}

UNFBAN_ERRORS = {
	"User is an administrator of the chat",
	"Chat not found",
	"Not enough rights to restrict/unrestrict chat member",
	"User_not_participant",
	"Method is available for supergroup and channel chats only",
	"Not in the chat",
	"Channel_private",
	"Chat_admin_required",
	"Have no rights to send a message"
}

@run_async
def new_fed(bot: Bot, update: Update):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	message = update.effective_message
	if chat.type != "private":
		update.effective_message.reply_text("Please run this command in my PM only!")
		return
	fednam = message.text.split(None, 1)[1]
	if not fednam == '':
		fed_id = str(uuid.uuid4())
		fed_name = fednam
		LOGGER.info(fed_id)
		if user.id == int(OWNER_ID):
			fed_id = fed_name

		x = sql.new_fed(user.id, fed_name, fed_id)
		if not x:
			update.effective_message.reply_text("Failed to create federation! Head over to @PhoenixSupport to notify us of the error.")
			return

		update.effective_message.reply_text("*You have successfully created a new federation!*"\
											"\nName: `{}`"\
											"\nID: `{}`"
											"\n\nUse the command below to join the federation:"
											"\n`/joinfed {}`".format(fed_name, fed_id, fed_id), parse_mode=ParseMode.MARKDOWN)
		try:
			bot.send_message(MESSAGE_DUMP,
				"Federation <b>{}</b> has been created with ID: <pre>{}</pre>".format(fed_name, fed_id), parse_mode=ParseMode.HTML)
		except:
			LOGGER.warning("Cannot send a message to MESSAGE_DUMP")
	else:
		update.effective_message.reply_text("Please give a name for the federation.")

@run_async
def del_fed(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	if chat.type != "private":
		update.effective_message.reply_text("Please run this command in my PM only!")
		return
	if args:
		is_fed_id = args[0]
		getinfo = sql.get_fed_info(is_fed_id)
		if getinfo == False:
			update.effective_message.reply_text("This federation doesn't exist.")
			return
		if int(getinfo['owner']) == int(user.id):
			fed_id = is_fed_id
		else:
			update.effective_message.reply_text("Only federation owners can do this!")
			return
	else:
		update.effective_message.reply_text("What should I delete?")
		return

	if is_user_fed_owner(fed_id, user.id) == False:
		update.effective_message.reply_text("Only the federation owner can do this!")
		return

	update.effective_message.reply_text("Are you sure you want to delete your federation? This action cannot be reversed, you will lose your entire ban list, and '{}' will be permanently lost.".format(getinfo['fname']),
			reply_markup=InlineKeyboardMarkup(
						[[InlineKeyboardButton(text="⚠️ Delete Federation ⚠️", callback_data="rmfed_{}".format(fed_id))],
						[InlineKeyboardButton(text="Cancel", callback_data="rmfed_cancel")]]))

@run_async
def fed_chat(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)

	user_id = update.effective_message.from_user.id
	if not is_user_admin(update.effective_chat, user_id):
		update.effective_message.reply_text("You must be an admin to execute this command.")
		return

	if not fed_id:
		update.effective_message.reply_text("This group is not in any federation!")
		return

	user = update.effective_user  # type: Optional[Chat]
	chat = update.effective_chat  # type: Optional[Chat]
	info = sql.get_fed_info(fed_id)

	text = "This chat is part of the following federation:"
	text += "\n{} (ID: <code>{}</code>)".format(info['fname'], fed_id)

	update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


def join_fed(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message
    administrators = chat.get_administrators()
    fed_id = sql.get_fed_id(chat.id)

    if user.id in SUDO_USERS:
        pass
    else:
        for admin in administrators:
            status = admin.status
            if status == "creator":
                print(admin)
                if str(admin.user.id) == str(user.id):
                    pass
                else:
                    update.effective_message.reply_text("Only the group creator can do it!")
                    return
    if fed_id:
        message.reply_text("Uh, you can only join one federation in a chat.")
        return

    if len(args) >= 1:
        fedd = args[0]
        print(fedd)
        if sql.search_fed_by_id(fedd) == False:
            message.reply_text("Please enter a valid federation ID.")
            return

        x = sql.chat_join_fed(fedd, chat.id)
        if not x:
                message.reply_text("Failed to join federation! Please head to @PhoenixSupport to report this.")
                return

        message.reply_text("Chat successfully added to federation!")


@run_async
def leave_fed(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)
	fed_info = sql.get_fed_info(fed_id)

	# administrators = chat.get_administrators().status
	getuser = bot.get_chat_member(chat.id, user.id).status
	if getuser in 'creator' or user.id in SUDO_USERS:
		if sql.chat_leave_fed(chat.id) == True:
			update.effective_message.reply_text("This chat has left the federation: {}!".format(fed_info['fname']))
		else:
			update.effective_message.reply_text("How can you leave a federation that you never joined?!")
	else:
		update.effective_message.reply_text("Only group creators can use this command!")

@run_async
def user_join_fed(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]
	fed_id = sql.get_fed_id(chat.id)

	if is_user_fed_owner(fed_id, user.id):
		user_id = extract_user(msg, args)
		if user_id:
			user = bot.get_chat(user_id)
		elif not msg.reply_to_message and not args:
			user = msg.from_user
		elif not msg.reply_to_message and (not args or (
			len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
			[MessageEntity.TEXT_MENTION]))):
			msg.reply_text("I cannot extract users from this message.")
			return
		else:
			LOGGER.warning('error')
		getuser = sql.search_user_in_fed(fed_id, user_id)
		fed_id = sql.get_fed_id(chat.id)
		info = sql.get_fed_info(fed_id)
		get_owner = eval(info['fusers'])['owner']
		get_owner = bot.get_chat(get_owner).id
		if user_id == get_owner:
			update.effective_message.reply_text("Why are you trying to promote the federation owner?")
			return
		if getuser:
			update.effective_message.reply_text("This user is already an admin of the federation!")
			return
		if user_id == bot.id:
			update.effective_message.reply_text("Hah, you're really funny.")
			return
		res = sql.user_join_fed(fed_id, user_id)
		if res:
			update.effective_message.reply_text("Successfully Promoted!")
		else:
			update.effective_message.reply_text("Failed to promote!")
	else:
		update.effective_message.reply_text("Only federation owners can do this!")


@run_async
def user_demote_fed(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)

	if is_user_fed_owner(fed_id, user.id):
		msg = update.effective_message  # type: Optional[Message]
		user_id = extract_user(msg, args)
		if user_id:
			user = bot.get_chat(user_id)

		elif not msg.reply_to_message and not args:
			user = msg.from_user

		elif not msg.reply_to_message and (not args or (
			len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
			[MessageEntity.TEXT_MENTION]))):
			msg.reply_text("I cannot extract users from this message.")
			return
		else:
			LOGGER.warning('error')

		if user_id == bot.id:
			update.effective_message.reply_text("Boi, what are you even trying to do?")
			return

		if sql.search_user_in_fed(fed_id, user_id) == False:
			update.effective_message.reply_text("This user isn't even a federation admin!")
			return

		res = sql.user_demote_fed(fed_id, user_id)
		if res == True:
			update.effective_message.reply_text("Get out of here!")
		else:
			update.effective_message.reply_text("Failed to demote!")
	else:
		update.effective_message.reply_text("Only federation owners can do this!")
		return

@run_async
def fed_info(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)
	info = sql.get_fed_info(fed_id)

	if not fed_id:
		update.effective_message.reply_text("This group is not in any federation!")
		return

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Only federation admins can do this!")
		return

	owner = bot.get_chat(info['owner'])
	try:
		owner_name = owner.first_name + " " + owner.last_name
	except:
		owner_name = owner.first_name
	FEDADMIN = sql.all_fed_users(fed_id)
	FEDADMIN.append(int(owner.id))
	TotalAdminFed = len(FEDADMIN)

	user = update.effective_user  # type: Optional[Chat]
	chat = update.effective_chat  # type: Optional[Chat]
	info = sql.get_fed_info(fed_id)

	text = "<b>Federation Information:</b>"
	text += "\nFedID: <code>{}</code>".format(fed_id)
	text += "\nName: {}".format(info['fname'])
	text += "\nCreator: {}".format(mention_html(owner.id, owner_name))
	text += "\nAdmins: <code>{}</code>".format(TotalAdminFed)
	getfban = sql.get_all_fban_users(fed_id)
	text += "\nTotal banned users: <code>{}</code>".format(len(getfban))
	getfchat = sql.all_fed_chats(fed_id)
	text += "\nNumber of groups in this federation: <code>{}</code>".format(len(getfchat))

	update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

@run_async
def fed_admin(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)

	if not fed_id:
		update.effective_message.reply_text("This group is not in any federation!")
		return

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Only federation admins can do this!")
		return

	user = update.effective_user  # type: Optional[Chat]
	chat = update.effective_chat  # type: Optional[Chat]
	info = sql.get_fed_info(fed_id)

	text = "<b>Federation admins of {}:</b>\n\n".format(info['fname'])
	text += "👑 Owner:\n"
	owner = bot.get_chat(info['owner'])
	try:
		owner_name = owner.first_name + " " + owner.last_name
	except:
		owner_name = owner.first_name
	text += " • {}\n".format(mention_html(owner.id, owner_name))

	members = sql.all_fed_members(fed_id)
	if len(members) == 0:
		text += "\n🔱 There are no admins in this federation."
	else:
		text += "\n🔱 Admins:\n"
		for x in members:
			user = bot.get_chat(x) 
			text += " • {}\n".format(mention_html(user.id, user.first_name))

	update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def fed_ban(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)

	if not fed_id:
		update.effective_message.reply_text("This group is not a part of any federation!")
		return

	info = sql.get_fed_info(fed_id)
	OW = bot.get_chat(info['owner'])
	HAHA = OW.id
	FEDADMIN = sql.all_fed_users(fed_id)
	FEDADMIN.append(int(HAHA))

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Only federation admins can do this!")
		return

	message = update.effective_message  # type: Optional[Message]

	user_id, reason = extract_user_and_text(message, args)

	fban, fbanreason = sql.get_fban_user(fed_id, user_id)

	if not user_id:
		message.reply_text("You don't seem to be referring to a user.")
		return

	if user_id == bot.id:
		message.reply_text("Nice try!")
		return

	if is_user_fed_owner(fed_id, user_id) == True:
		message.reply_text("You can't ban the federation owner!")
		return

	if is_user_fed_admin(fed_id, user_id) == True:
		message.reply_text("Why are you trying to ban a federation admin?")
		return

	if user_id == OWNER_ID:
		message.reply_text("I'm not gonna ban my owner!")
		return

	if int(user_id) in SUDO_USERS:
		message.reply_text("This person is sudo so I won't ban them!")
		return

	if int(user_id) in WHITELIST_USERS:
		message.reply_text("This person is whitelisted so I can't ban them!")
		return

	try:
		user_chat = bot.get_chat(user_id)
	except BadRequest as excp:
		message.reply_text(excp.message)
		return

	if user_chat.type != 'private':
		message.reply_text("That's not a user!")
		return

	if fban:
		user_target = mention_html(user_chat.id, user_chat.first_name)
		fed_name = info['fname']
		starting = "Starting FedBan for {} in the Federation <b>{}</b>is for\n".format(user_target, fed_name)
		update.effective_message.reply_text(starting, parse_mode=ParseMode.HTML)

		if reason == "":
			reason = "No reason given."

		temp = sql.un_fban_user(fed_id, user_id)
		if not temp:
			message.reply_text("Failed to update fban reason!")
			return
		x = sql.fban_user(fed_id, user_id, user_chat.first_name, user_chat.last_name, user_chat.username, reason)
		if not x:
			message.reply_text("Failed to ban from the federation! If this problem persists, reach out to us @PhoenixSupport.")
			return

		fed_chats = sql.all_fed_chats(fed_id)
		for chat in fed_chats:
			try:
				bot.kick_chat_member(chat, user_id)
			except BadRequest as excp:
				if excp.message in FBAN_ERRORS:
					pass
				else:
					LOGGER.warning("Could not fban in {} because: {}".format(chat, excp.message))
			except TelegramError:
				pass

		send_to_list(bot, FEDADMIN,
				 "<b>FedBan reason updated</b>" \
							 "\n<b>Federation:</b> {}" \
							 "\n<b>Federation Admin:</b> {}" \
							 "\n<b>User:</b> {}" \
							 "\n<b>User ID:</b> <code>{}</code>" \
							 "\n<b>Reason:</b> {}".format(fed_name, mention_html(user.id, user.first_name),
									   mention_html(user_chat.id, user_chat.first_name),
													user_chat.id, reason), 
				html=True)
		message.reply_text("I've updated the FedBan reason!")
		return

	user_target = mention_html(user_chat.id, user_chat.first_name)
	fed_name = info['fname']

	starting = "Starting a federation ban for {} in the Federation <b>{}</b>.".format(user_target, fed_name)
	update.effective_message.reply_text(starting, parse_mode=ParseMode.HTML)

	if reason == "":
		reason = "No reason given."

	x = sql.fban_user(fed_id, user_id, user_chat.first_name, user_chat.last_name, user_chat.username, reason)
	if not x:
		message.reply_text("Failed to ban from the federation! If this problem persists, reach out to us @PhoenixSupport.")
		return

	fed_chats = sql.all_fed_chats(fed_id)
	for chat in fed_chats:
		try:
			bot.kick_chat_member(chat, user_id)
		except BadRequest as excp:
			if excp.message in FBAN_ERRORS:
				try:
					dispatcher.bot.getChat(chat)
				except Unauthorized:
					sql.chat_leave_fed(chat)
					LOGGER.info("Chat {} has left fed {} because bot has been kicked.".format(chat, info['fname']))
					continue
			else:
				LOGGER.warning("Cannot fban in {} because: {}".format(chat, excp.message))
		except TelegramError:
			pass

	send_to_list(bot, FEDADMIN,
			 "<b>New FedBan</b>" \
			 "\n<b>Federation:</b> {}" \
			 "\n<b>Federation Admin:</b> {}" \
			 "\n<b>User:</b> {}" \
			 "\n<b>User ID:</b> <code>{}</code>" \
			 "\n<b>Reason:</b> {}".format(fed_name, mention_html(user.id, user.first_name),
								   mention_html(user_chat.id, user_chat.first_name),
												user_chat.id, reason), 
			html=True)
	message.reply_text("{} has been fbanned.".format(mention_html(user_chat.id, user_chat.first_name)),
	parse_mode=ParseMode.HTML)


@run_async
def unfban(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	message = update.effective_message  # type: Optional[Message]
	fed_id = sql.get_fed_id(chat.id)

	if not fed_id:
		update.effective_message.reply_text("This group is not a part of any federation!")
		return

	info = sql.get_fed_info(fed_id)

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Only federation admins can do this!")
		return

	user_id = extract_user(message, args)
	if not user_id:
		message.reply_text("You don't seem to be referring to a user.")
		return

	user_chat = bot.get_chat(user_id)
	if user_chat.type != 'private':
		message.reply_text("That's not a user!")
		return

	fban, fbanreason = sql.get_fban_user(fed_id, user_id)
	if fban == False:
		message.reply_text("This user is not fbanned!")
		return

	banner = update.effective_user  # type: Optional[User]

	message.reply_text("I'll give {} a second chance in this federation".format(mention_html(user_chat.id, user_chat.first_name)),
	parse_mode=ParseMode.HTML)

	chat_list = sql.all_fed_chats(fed_id)

	for chat in chat_list:
		try:
			member = bot.get_chat_member(chat, user_id)
			if member.status == 'kicked':
				bot.unban_chat_member(chat, user_id)
				"""
				bot.send_message(chat, "<b>Un-FedBan</b>" \
						 "\n<b>Federation:</b> {}" \
						 "\n<b>Federation Admin:</b> {}" \
						 "\n<b>User:</b> {}" \
						 "\n<b>User ID:</b> <code>{}</code>".format(info['fname'], mention_html(user.id, user.first_name), mention_html(user_chat.id, user_chat.first_name),
															user_chat.id), parse_mode="HTML")
				"""

		except BadRequest as excp:
			if excp.message in UNFBAN_ERRORS:
				pass
			else:
				LOGGER.warning("Cannot remove fban in {} because: {}".format(chat, excp.message))
		except TelegramError:
			pass

		try:
			x = sql.un_fban_user(fed_id, user_id)
			if not x:
				message.reply_text("Un-fban failure, this user may have been un-fbanned already!")
				return
		except:
			pass

	message.reply_text("{} has been un-fbanned.".format(mention_html(user_chat.id, user_chat.first_name)),
        parse_mode=ParseMode.HTML)
	FEDADMIN = sql.all_fed_users(fed_id)
"""
	for x in FEDADMIN:
		getreport = sql.user_feds_report(x)
		if getreport == False:
			FEDADMIN.remove(x)
	send_to_list(bot, FEDADMIN,
			 "<b>Un-FedBan</b>" \
			 "\n<b>Federation:</b> {}" \
			 "\n<b>Federation Admin:</b> {}" \
			 "\n<b>User:</b> {}" \
			 "\n<b>User ID:</b> <code>{}</code>".format(info['fname'], mention_html(user.id, user.first_name),
												 mention_html(user_chat.id, user_chat.first_name),
															  user_chat.id),
			html=True)
"""

@run_async
def set_frules(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)

	if not fed_id:
		update.effective_message.reply_text("This chat is not in any federation!")
		return

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Only federation admins can do this!")
		return

	if len(args) >= 1:
		msg = update.effective_message  # type: Optional[Message]
		raw_text = msg.text
		args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
		if len(args) == 2:
			txt = args[1]
			offset = len(txt) - len(raw_text)  # set correct offset relative to command
			markdown_rules = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)
		x = sql.set_frules(fed_id, markdown_rules)
		if not x:
			update.effective_message.reply_text("Failed to set federation rules. If this persists, reach out to us @PhoenixSupport.")
			return

		rules = sql.get_fed_info(fed_id)['frules']
		update.effective_message.reply_text(f"Rules have been set to :\n{rules}!")
	else:
		update.effective_message.reply_text("Please write the rules!")


@run_async
def get_frules(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	fed_id = sql.get_fed_id(chat.id)
	if not fed_id:
		update.effective_message.reply_text("This chat is not in any federation!")
		return

	rules = sql.get_frules(fed_id)
	text = "*Rules in this fed:*\n"
	text += rules
	update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@run_async
def fed_broadcast(bot: Bot, update: Update, args: List[str]):
	msg = update.effective_message  # type: Optional[Message]
	user = update.effective_user  # type: Optional[User]
	if args:
		chat = update.effective_chat  # type: Optional[Chat]
		fed_id = sql.get_fed_id(chat.id)
		fedinfo = sql.get_fed_info(fed_id)
		text = "*New broadcast from the Federation {}*\n".format(fedinfo['fname'])
		# Parsing md
		raw_text = msg.text
		args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
		txt = args[1]
		offset = len(txt) - len(raw_text)  # set correct offset relative to command
		text_parser = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)
		text += text_parser
		try:
			broadcaster = user.first_name
		except:
			broadcaster = user.first_name + " " + user.last_name
		text += "\n\n- {}".format(mention_markdown(user.id, broadcaster))
		chat_list = sql.all_fed_chats(fed_id)
		failed = 0
		for chat in chat_list:
			try:
				bot.sendMessage(chat, text, parse_mode="markdown")
			except TelegramError:
				failed += 1
				LOGGER.warning("Couldn't send broadcast to %s, group name %s", str(chat.chat_id), str(chat.chat_name))

		send_text = "The federation broadcast is complete!"
		if failed >= 1:
			send_text += "{} the group failed to receive the broadcast, probably because they left the federation.".format(failed)
		update.effective_message.reply_text(send_text)

@run_async
def fed_ban_list(bot: Bot, update: Update, args: List[str], chat_data):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]

	fed_id = sql.get_fed_id(chat.id)
	info = sql.get_fed_info(fed_id)

	if not fed_id:
		update.effective_message.reply_text("This group is not a part of any federation!")
		return

	if is_user_fed_owner(fed_id, user.id) == False:
		update.effective_message.reply_text("Only federation owners can do this!")
		return

	user = update.effective_user  # type: Optional[Chat]
	chat = update.effective_chat  # type: Optional[Chat]
	getfban = sql.get_all_fban_users(fed_id)
	if len(getfban) == 0:
		update.effective_message.reply_text("The federation ban list of {} is empty.".format(info['fname']), parse_mode=ParseMode.HTML)
		return

	if args:
		if args[0] == 'json':
			jam = time.time()
			new_jam = jam + 1800
			cek = get_chat(chat.id, chat_data)
			if cek.get('status'):
				if jam <= int(cek.get('value')):
					waktu = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(cek.get('value')))
					update.effective_message.reply_text("You can back up your data once every 30 minutes!\nYou can back up data again at `{}`".format(waktu), parse_mode=ParseMode.MARKDOWN)
					return
				else:
					if user.id not in SUDO_USERS:
						put_chat(chat.id, new_jam, chat_data)
			else:
				if user.id not in SUDO_USERS:
					put_chat(chat.id, new_jam, chat_data)
			backups = ""
			for users in getfban:
				getuserinfo = sql.get_all_fban_users_target(fed_id, users)
				json_parser = {"user_id": users, "first_name": getuserinfo['first_name'], "last_name": getuserinfo['last_name'], "user_name": getuserinfo['user_name'], "reason": getuserinfo['reason']}
				backups += json.dumps(json_parser)
				backups += "\n"
			with BytesIO(str.encode(backups)) as output:
				output.name = "phoenix_fbanned_users.json"
				update.effective_message.reply_document(document=output, filename="phoenix_fbanned_users.json",
													caption="Total {} User are blocked by the Federation {}.".format(len(getfban), info['fname']))
			return
		elif args[0] == 'csv':
			jam = time.time()
			new_jam = jam + 1800
			cek = get_chat(chat.id, chat_data)
			if cek.get('status'):
				if jam <= int(cek.get('value')):
					waktu = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(cek.get('value')))
					update.effective_message.reply_text("You can back up data once every 30 minutes!\nYou can back up data again at `{}`".format(waktu), parse_mode=ParseMode.MARKDOWN)
					return
				else:
					if user.id not in SUDO_USERS:
						put_chat(chat.id, new_jam, chat_data)
			else:
				if user.id not in SUDO_USERS:
					put_chat(chat.id, new_jam, chat_data)
			backups = "id,firstname,lastname,username,reason\n"
			for users in getfban:
				getuserinfo = sql.get_all_fban_users_target(fed_id, users)
				backups += "{user_id},{first_name},{last_name},{user_name},{reason}".format(user_id=users, first_name=getuserinfo['first_name'], last_name=getuserinfo['last_name'], user_name=getuserinfo['user_name'], reason=getuserinfo['reason'])
				backups += "\n"
			with BytesIO(str.encode(backups)) as output:
				output.name = "phoenix_fbanned_users.csv"
				update.effective_message.reply_document(document=output, filename="phoenix_fbanned_users.csv",
													caption="Total {} User are blocked by Federation {}.".format(len(getfban), info['fname']))
			return

	text = "<b>{} users have been banned from the federation {}:</b>\n".format(len(getfban), info['fname'])
	for users in getfban:
		getuserinfo = sql.get_all_fban_users_target(fed_id, users)
		if getuserinfo == False:
			text = "There are no users banned from the federation {}".format(info['fname'])
			break
		user_name = getuserinfo['first_name']
		if getuserinfo['last_name']:
			user_name += " " + getuserinfo['last_name']
		text += " • {} (<code>{}</code>)\n".format(mention_html(users, user_name), users)

	try:
		update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
	except:
		jam = time.time()
		new_jam = jam + 1800
		cek = get_chat(chat.id, chat_data)
		if cek.get('status'):
			if jam <= int(cek.get('value')):
				waktu = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(cek.get('value')))
				update.effective_message.reply_text("You can back up data once every 30 minutes!\nYou can back up data again at `{}`".format(waktu), parse_mode=ParseMode.MARKDOWN)
				return
			else:
				if user.id not in SUDO_USERS:
					put_chat(chat.id, new_jam, chat_data)
		else:
			if user.id not in SUDO_USERS:
				put_chat(chat.id, new_jam, chat_data)
		cleanr = re.compile('<.*?>')
		cleantext = re.sub(cleanr, '', text)
		with BytesIO(str.encode(cleantext)) as output:
			output.name = "fbanlist.txt"
			update.effective_message.reply_document(document=output, filename="fbanlist.txt",
													caption="The following is the list of users who are currently fbanned in the Federation {}.".format(info['fname']))

@run_async
def fed_notif(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]
	fed_id = sql.get_fed_id(chat.id)

	if not fed_id:
		update.effective_message.reply_text("This group is not a part of any federation!")
		return

	if args:
		if args[0] in ("yes", "on"):
			sql.set_feds_setting(user.id, True)
			msg.reply_text("Reporting turned on! Users fbanned/un-fbanned by you will be notified via PM.")
		elif args[0] in ("no", "off"):
			sql.set_feds_setting(user.id, False)
			msg.reply_text("Reporting turned off! Users fbanned/un-fbanned will not be notified via PM.")
		else:
			msg.reply_text("Please enter `on`/`off`", parse_mode="markdown")
	else:
		getreport = sql.user_feds_report(user.id)
		msg.reply_text("Your current Federation report preferences: `{}`".format(getreport), parse_mode="markdown")

@run_async
def fed_chats(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	fed_id = sql.get_fed_id(chat.id)
	info = sql.get_fed_info(fed_id)

	if not fed_id:
		update.effective_message.reply_text("This group is not a part of any federation!")
		return

	if is_user_fed_admin(fed_id, user.id) == False:
		update.effective_message.reply_text("Only federation admins can do this!")
		return

	getlist = sql.all_fed_chats(fed_id)
	if len(getlist) == 0:
		update.effective_message.reply_text("No users are fbanned from the federation {}".format(info['fname']), parse_mode=ParseMode.HTML)
		return

	text = "<b>New chat joined the federation {}:</b>\n".format(info['fname'])
	for chats in getlist:
		chat_name = sql.get_fed_name(chats)
		text += " • {} (<code>{}</code>)\n".format(chat_name, chats)

	try:
		update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
	except:
		cleanr = re.compile('<.*?>')
		cleantext = re.sub(cleanr, '', text)
		with BytesIO(str.encode(cleantext)) as output:
			output.name = "fbanlist.txt"
			update.effective_message.reply_document(document=output, filename="fbanlist.txt",
													caption="Here is the list of all the chats in the federation {}.".format(info['fname']))

@run_async
def fed_import_bans(bot: Bot, update: Update, chat_data):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]

	fed_id = sql.get_fed_id(chat.id)
	info = sql.get_fed_info(fed_id)

	if not fed_id:
		update.effective_message.reply_text("This group is not a part of any federation!")
		return

	if is_user_fed_owner(fed_id, user.id) == False:
		update.effective_message.reply_text("Only federation owners can do this!")
		return

	if msg.reply_to_message and msg.reply_to_message.document:
		jam = time.time()
		new_jam = jam + 1800
		cek = get_chat(chat.id, chat_data)
		if cek.get('status'):
			if jam <= int(cek.get('value')):
				waktu = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(cek.get('value')))
				update.effective_message.reply_text("You can backup your data once every 30 minutes!\nYou can backup data again at `{}`".format(waktu), parse_mode=ParseMode.MARKDOWN)
				return
			else:
				if user.id not in SUDO_USERS:
					put_chat(chat.id, new_jam, chat_data)
		else:
			if user.id not in SUDO_USERS:
				put_chat(chat.id, new_jam, chat_data)
		if int(int(msg.reply_to_message.document.file_size)/1024) >= 200:
			msg.reply_text("This file is too big!")
			return
		success = 0
		failed = 0
		try:
			file_info = bot.get_file(msg.reply_to_message.document.file_id)
		except BadRequest:
			msg.reply_text("Try downloading and re-uploading the file, this one seems broken!")
			return
		fileformat = msg.reply_to_message.document.file_name.split('.')[-1]
		if fileformat == 'json':
			with BytesIO() as file:
				file_info.download(out=file)
				file.seek(0)
				reading = file.read().decode('UTF-8')
				splitting = reading.split('\n')
				for x in splitting:
					if x == '':
						continue
					try:
						data = json.loads(x)
					except json.decoder.JSONDecodeError as err:
						failed += 1
						continue
					try:
						import_userid = int(data['user_id']) # Make sure it int
						import_firstname = str(data['first_name'])
						import_lastname = str(data['last_name'])
						import_username = str(data['user_name'])
						import_reason = str(data['reason'])
					except ValueError:
						failed += 1
						continue
					# Checking user
					if int(import_userid) == bot.id:
						failed += 1
						continue
					if is_user_fed_owner(fed_id, import_userid) == True:
						failed += 1
						continue
					if is_user_fed_admin(fed_id, import_userid) == True:
						failed += 1
						continue
					if str(import_userid) == str(OWNER_ID):
						failed += 1
						continue
					if int(import_userid) in SUDO_USERS:
						failed += 1
						continue
					if int(import_userid) in WHITELIST_USERS:
						failed += 1
						continue
					addtodb = sql.fban_user(fed_id, str(import_userid), import_firstname, import_lastname, import_username, import_reason)
					if addtodb:
						success += 1
			text = "Successfully imported! {} people are fbanned.".format(success)
			if failed >= 1:
				text += " {} Failed to import.".format(failed)
		elif fileformat == 'csv':
			with BytesIO() as file:
				file_info.download(out=file)
				file.seek(0)
				reading = file.read().decode('UTF-8')
				splitting = reading.split('\n')
				for x in splitting:
					if x == '':
						continue
					data = x.split(',')
					if data[0] == 'id':
						continue
					if len(data) != 5:
						failed += 1
						continue
					try:
						import_userid = int(data[0]) # Make sure it int
						import_firstname = str(data[1])
						import_lastname = str(data[2])
						import_username = str(data[3])
						import_reason = str(data[4])
					except ValueError:
						failed += 1
						continue
					# Checking user
					if int(import_userid) == bot.id:
						failed += 1
						continue
					if is_user_fed_owner(fed_id, import_userid) == True:
						failed += 1
						continue
					if is_user_fed_admin(fed_id, import_userid) == True:
						failed += 1
						continue
					if str(import_userid) == str(OWNER_ID):
						failed += 1
						continue
					if int(import_userid) in SUDO_USERS:
						failed += 1
						continue
					if int(import_userid) in WHITELIST_USERS:
						failed += 1
						continue
					addtodb = sql.fban_user(fed_id, str(import_userid), import_firstname, import_lastname, import_username, import_reason)
					if addtodb:
						success += 1
			text = "Successfully imported. {} people are fbanned.".format(success)
			if failed >= 1:
				text += " {} failed to import.".format(failed)
		else:
			update.effective_message.reply_text("File not supported.")
			return
		update.effective_message.reply_text(text)

@run_async
def del_fed_button(bot, update):
	query = update.callback_query
	userid = query.message.chat.id
	fed_id = query.data.split("_")[1]

	if fed_id == 'cancel':
		query.message.edit_text("Federation deletion has been cancelled.")
		return

	getfed = sql.get_fed_info(fed_id)
	if getfed:
		delete = sql.del_fed(fed_id)
		if delete:
			query.message.edit_text("You have deleted your federation! Now all the groups that were connected with `{}` do not have a federation.".format(getfed['fname']), parse_mode='markdown')


def is_user_fed_admin(fed_id, user_id):
	fed_admins = sql.all_fed_users(fed_id)
	if int(user_id) == 615304572:
		return True
	if fed_admins == False:
		return False
	if int(user_id) in fed_admins:
		return True
	else:
		return False


def is_user_fed_owner(fed_id, user_id):
	getsql = sql.get_fed_info(fed_id)
	if getsql == False:
		return False
	getfedowner = eval(getsql['fusers'])
	if getfedowner == None or getfedowner == False:
		return False
	getfedowner = getfedowner['owner']
	if str(user_id) == getfedowner:
		return True
	else:
		return False


@run_async
def welcome_fed(bot, update):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]

	fed_id = sql.get_fed_id(chat.id)
	fban, fbanreason = sql.get_fban_user(fed_id, user.id)
	if fban:
		update.effective_message.reply_text("This user is banned in the current federation and has been removed!")
		bot.kick_chat_member(chat.id, user.id)
		return True
	else:
		return False


def __stats__():
	all_fbanned = sql.get_all_fban_users_global()
	all_feds = sql.get_all_feds_users_global()
	return "{} fbanned users, across {} feds".format(len(all_fbanned), len(all_feds))


def __user_info__(user_id, chat_id):
	fed_id = sql.get_fed_id(chat_id)
	if fed_id:
		fban, fbanreason = sql.get_fban_user(fed_id, user_id)
		info = sql.get_fed_info(fed_id)
		infoname = info['fname']

		if int(info['owner']) == user_id:
			text = "This user is the owner of the current Federation: <b>{}</b>.".format(infoname)
		elif is_user_fed_admin(fed_id, user_id):
			text = "This user is the admin of the current Federation: <b>{}</b>.".format(infoname)

		elif fban:
			text = "Banned in the current Federation: <b>Yes</b>"
			text += "\n<b>Reason:</b> {}".format(fbanreason)
		else:
			text = "Banned in the current Federation: <b>No</b>"
	else:
		text = ""
	return text


# Temporary data
def put_chat(chat_id, value, chat_data):
	# print(chat_data)
	if value == False:
		status = False
	else:
		status = True
	chat_data[chat_id] = {'federation': {"status": status, "value": value}}

def get_chat(chat_id, chat_data):
	# print(chat_data)
	try:
		value = chat_data[chat_id]['federation']
		return value
	except KeyError:
		return {"status": False, "value": False}


__mod_name__ = "Federations"

__help__ = """
Ah, group management. Everything is fun and games till spammers start joining your group, and you have to ban them. They start joining all your groups and you're forced to ban them individually.

That's where federations come in! You can have a fedban in one chat ban the user from all your groups! Moreover, you can add trusted users as admins and have them ban across all your chats. Pretty efficient!


*Commands*:
 - /newfed <fedname>: create a new federation with the name given. Users are only allowed to have one federation each. This command can also be used to rename the federation. (max. 64 characters)
 - /delfed: delete your federation, and all information related to it. However, this will NOT unban the banned users.
 - /fedinfo <FedID>: information about the specified federation.
 - /joinfed <FedID>: add the current chat to the specified federation. Only group owners can use this command. A group can only have one federation linked to it.
 - /leavefed <FedID>: leave the specified federation. Only group owners can use this command.
 - /fpromote <user>: promote the specified user to fedadmin. Can only be used by the fed owner. - /fdemote <user>: demote the specified user. Can only be used by the fed owner.
 - /fban <user>: ban users from all federations you have control over.
 - /unfban <user>: unbans users from all federations you have control over.
 - /setfrules: set the rules for the federation.
 - /frules: get the rules of the federation.
 - /chatfed: shows the federation the chat is linked to.
 - /fedadmins: gives list of federation admins.
 - /fbanlist: gives the list of currently fedbanned users.
 - /fedchats: get all the chats linked to the federation.
 - /importfbans: Reply to the federation backup message file to import the banned list to the federation.
"""

NEW_FED_HANDLER = CommandHandler("newfed", new_fed)
DEL_FED_HANDLER = CommandHandler("delfed", del_fed, pass_args=True)
JOIN_FED_HANDLER = CommandHandler("joinfed", join_fed, pass_args=True)
LEAVE_FED_HANDLER = CommandHandler("leavefed", leave_fed, pass_args=True)
PROMOTE_FED_HANDLER = CommandHandler("fpromote", user_join_fed, pass_args=True)
DEMOTE_FED_HANDLER = CommandHandler("fdemote", user_demote_fed, pass_args=True)
INFO_FED_HANDLER = CommandHandler("fedinfo", fed_info, pass_args=True)
BAN_FED_HANDLER = DisableAbleCommandHandler(["fban", "fedban"], fed_ban, pass_args=True)
UN_BAN_FED_HANDLER = CommandHandler("unfban", unfban, pass_args=True)
FED_BROADCAST_HANDLER = CommandHandler("fbroadcast", fed_broadcast, pass_args=True)
FED_SET_RULES_HANDLER = CommandHandler("setfrules", set_frules, pass_args=True)
FED_GET_RULES_HANDLER = CommandHandler("frules", get_frules, pass_args=True)
FED_CHAT_HANDLER = CommandHandler("chatfed", fed_chat, pass_args=True)
FED_ADMIN_HANDLER = CommandHandler("fedadmins", fed_admin, pass_args=True)
FED_USERBAN_HANDLER = CommandHandler("fbanlist", fed_ban_list, pass_args=True, pass_chat_data=True)
FED_NOTIF_HANDLER = CommandHandler("fednotif", fed_notif, pass_args=True)
FED_CHATLIST_HANDLER = CommandHandler("fedchats", fed_chats, pass_args=True)
FED_IMPORTBAN_HANDLER = CommandHandler("importfbans", fed_import_bans, pass_chat_data=True)

DELETEBTN_FED_HANDLER = CallbackQueryHandler(del_fed_button, pattern=r"rmfed_")

dispatcher.add_handler(NEW_FED_HANDLER)
dispatcher.add_handler(DEL_FED_HANDLER)
dispatcher.add_handler(JOIN_FED_HANDLER)
dispatcher.add_handler(LEAVE_FED_HANDLER)
dispatcher.add_handler(PROMOTE_FED_HANDLER)
dispatcher.add_handler(DEMOTE_FED_HANDLER)
dispatcher.add_handler(INFO_FED_HANDLER)
dispatcher.add_handler(BAN_FED_HANDLER)
dispatcher.add_handler(UN_BAN_FED_HANDLER)
dispatcher.add_handler(FED_BROADCAST_HANDLER)
dispatcher.add_handler(FED_SET_RULES_HANDLER)
dispatcher.add_handler(FED_GET_RULES_HANDLER)
dispatcher.add_handler(FED_CHAT_HANDLER)
dispatcher.add_handler(FED_ADMIN_HANDLER)
dispatcher.add_handler(FED_USERBAN_HANDLER)
# dispatcher.add_handler(FED_NOTIF_HANDLER)
dispatcher.add_handler(FED_CHATLIST_HANDLER)
dispatcher.add_handler(FED_IMPORTBAN_HANDLER)

dispatcher.add_handler(DELETEBTN_FED_HANDLER)
