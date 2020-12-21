from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot import dispatcher, DRAGONS, telethn
from SaitamaRobot.modules.helper_funcs.extraction import extract_user
from telegram.ext import CallbackContext, run_async
import SaitamaRobot.modules.sql.approve_sql as sql
from SaitamaRobot.modules.helper_funcs.chat_status import bot_admin, user_admin
from telegram import ParseMode
from telethon import events, Button
from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantCreator


async def is_administrator(user_id: int, message):
    admin = False
    async for user in message.client.iter_participants(
        message.chat_id, filter=ChannelParticipantsAdmins
    ):
        if user_id == user.id or user_id in DRAGONS:
            admin = True
            break
    return admin


async def c(event):
    msg = 0
    async for x in event.client.iter_participants(
        event.chat_id, filter=ChannelParticipantsAdmins
    ):
        if isinstance(x.participant, ChannelParticipantCreator):
            msg += x.id
    return msg


@user_admin
@run_async
def approve(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!"
        )
        return ""
    member = chat.get_member(int(user_id))
    if member.status == "administrator" or member.status == "creator":
        message.reply_text(
            f"User is already admin - locks, blocklists, and antiflood already don't apply to them."
        )
        return
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"[{member.user['first_name']}](tg://user?id={member.user['id']}) is already approved in {chat_title}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    sql.approve(message.chat_id, user_id)
    message.reply_text(
        f"[{member.user['first_name']}](tg://user?id={member.user['id']}) has been approved in {chat_title}! They will now be ignored by automated admin actions like locks, blocklists, and antiflood.",
        parse_mode=ParseMode.MARKDOWN,
    )


@user_admin
@run_async
def disapprove(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!"
        )
        return ""
    member = chat.get_member(int(user_id))
    if member.status == "administrator" or member.status == "creator":
        message.reply_text("This user is an admin, they can't be unapproved.")
        return
    if not sql.is_approved(message.chat_id, user_id):
        message.reply_text(f"{member.user['first_name']} isn't approved yet!")
        return
    sql.disapprove(message.chat_id, user_id)
    message.reply_text(
        f"{member.user['first_name']} is no longer approved in {chat_title}."
    )


@user_admin
@run_async
def approved(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    no_users = False
    msg = "The following users are approved.\n"
    x = sql.list_approved(message.chat_id)
    for i in x:
        try:
            member = chat.get_member(int(i.user_id))
        except:
            pass
        msg += f"- `{i.user_id}`: {member.user['first_name']}\n"
    if msg.endswith("approved.\n"):
        message.reply_text(f"No users are approved in {chat_title}.")
        return
    else:
        message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@user_admin
@run_async
def approval(update, context):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(message, args)
    member = chat.get_member(int(user_id))
    if not user_id:
        message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!"
        )
        return ""
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"{member.user['first_name']} is an approved user. Locks, antiflood, and blocklists won't apply to them."
        )
    else:
        message.reply_text(
            f"{member.user['first_name']} is not an approved user. They are affected by normal commands."
        )


@telethn.on(events.CallbackQuery)
async def _(event):
    rights = await is_administrator(event.query.user_id, event)
    creator = await c(event)
    if event.data == b"rmapp":
        if not rights:
            await event.answer("You need to be admin to do this.")
            return
        if creator != event.query.user_id and event.query.user_id not in DRAGONS:
            await event.answer("Only owner of the chat can do this.")
            return
        users = []
        x = sql.all_app(event.chat_id)
        for i in x:
            users.append(int(i.user_id))
        for j in users:
            sql.disapprove(event.chat_id, j)
        await event.client.edit_message(
            event.chat_id,
            event.query.msg_id,
            f"Unapproved all users in chat. All users will now be affected by locks, blocklists, and antiflood.",
        )

    if event.data == b"can":
        if not rights:
            await event.answer("You need to be admin to do this.")
            return
        if creator != event.query.user_id and event.query.user_id not in DRAGONS:
            await event.answer("Only owner of the chat can cancel this operation.")
            return
        await event.client.edit_message(
            event.chat_id,
            event.query.msg_id,
            f"Removing of all unapproved users has been cancelled.",
        )


@telethn.on(events.NewMessage(pattern="^/unapproveall"))
async def _(event):
    chat = await event.get_chat()
    creator = await c(event)
    if creator != event.from_id and event.from_id not in DRAGONS:
        await event.reply("Only the chat owner can unapprove all users at once.")
        return
    msg = f"Are you sure you would like to unapprove ALL users in {event.chat.title}? This action cannot be undone."
    await event.client.send_message(
        event.chat_id,
        msg,
        buttons=[
            [Button.inline("Unapprove all users", b"rmapp")],
            [Button.inline("Cancel", b"can")],
        ],
        reply_to=event.id,
    )


__help__ = """
Sometimes, you might trust a user not to send unwanted content.
Maybe not enough to make them admin, but you might be ok with locks, blacklists, and antiflood not applying to them.

That's what approvals are for - approve of trustworthy users to allow them to send 

*Admin commands:*
- `/approval`*:* Check a user's approval status in this chat.
- `/approve`*:* Approve of a user. Locks, blacklists, and antiflood won't apply to them anymore.
- `/unapprove`*:* Unapprove of a user. They will now be subject to locks, blacklists, and antiflood again.
- `/approved`*:* List all approved users.
- `/unapproveall`*:* Unapprove *ALL* users in a chat. This cannot be undone.
"""

APPROVE = DisableAbleCommandHandler("approve", approve)
DISAPPROVE = DisableAbleCommandHandler("unapprove", disapprove)
LIST_APPROVED = DisableAbleCommandHandler("approved", approved)
APPROVAL = DisableAbleCommandHandler("approval", approval)

dispatcher.add_handler(APPROVE)
dispatcher.add_handler(DISAPPROVE)
dispatcher.add_handler(LIST_APPROVED)
dispatcher.add_handler(APPROVAL)

__mod_name__ = "Approvals"
__command_list__ = ["approve", "unapprove", "approved", "approval"]
__handlers__ = [APPROVE, DISAPPROVE, ALL, APPROVAL]
