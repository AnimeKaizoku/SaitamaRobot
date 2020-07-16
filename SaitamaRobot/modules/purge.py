from asyncio import sleep
from SaitamaRobot.modules.helper_funcs.telethn.chatstatus import user_is_admin 
from SaitamaRobot.modules.helper_funcs.telethn.chatstatus import can_delete_messages
from SaitamaRobot.saitamabot import saitama


@saitama(pattern="^/purge")
async def purge_messages(event):
    if event.from_id is None:
        return

    if not await user_is_admin(user_id=event.from_id, message=event):
        await event.reply("Only Admins are allowed to use this command")
        return

    if not await can_delete_messages(message=event):
        await event.reply("Can't seem to purge the message")
        return

    message = await event.get_reply_message()
    if not message:
        await event.reply(
            "Reply to a message to select where to start purging from."
        )
        return
    messages = []
    message_id = message.id
    delete_to = event.message.id - 1
    await event.client.delete_messages(event.chat_id, event.message.id)

    messages.append(event.reply_to_msg_id)
    for message_id in range(delete_to, message_id - 1, -1):
        messages.append(message_id)
        if len(messages) == 100:
            await event.client.delete_messages(event.chat_id, messages)
            messages = []

    message_count = len(messages)
    await event.client.delete_messages(event.chat_id, messages)
    msg = await event.reply(f"Purged {message_count} messages successfully!", parse_mode='markdown')
    await sleep(5)
    await msg.delete()


@saitama(pattern="^/del$")
async def delete_messages(event):
    if event.from_id == None:
        return

    if not await user_is_admin(user_id=event.from_id, message=event):
        await event.reply("Only Admins are allowed to use this command")
        return

    if not await can_delete_messages(message=event):
        await event.reply("Can't seem to delete this?")
        return

    message = await event.get_reply_message()
    if not message:
        await event.reply("Whadya want to delete?")
        return
    chat = await event.get_input_chat()
    del_message = [message, event.message]
    await event.client.delete_messages(chat, del_message)

__help__ = """
*Admin only:*
 - /del: deletes the message you replied to
 - /purge: deletes all messages between this and the replied to message.
 - /purge <integer X>: deletes the replied message, and X messages following it if replied to a message.
"""

__mod_name__ = "Purges"
