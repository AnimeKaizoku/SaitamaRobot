from pyrogram import filters
from SaitamaRobot import app
import asyncio
from pyrogram import raw

async def user_can_purge(_, c, m):
    mem = await c.get_chat_member(chat_id=m.chat.id, user_id=m.from_user.id)
    if mem.can_delete_messages or mem.status in ("creator"):
        return True
    await m.reply("You Don't Have Permission To Delete Messages")
   
can_purge = filters.create(user_can_purge)

@app.on_message(filters.command("purge")& filters.reply & can_purge, group=0)
async def purge(c, m):
    messages = list(range(m.message_id + 1, m.reply_to_message.message_id, -1))
    while len(messages) != 0:
        await c.send(
            raw.functions.channels.DeleteMessages(
                channel=await c.resolve_peer(m.chat.id), id=messages))
        del messages[0:100]
    await c.send_message(
        text="**Fast Purge Completed!!!**",
        chat_id=m.chat.id)

@app.on_message(filters.command('purge')& ~filters.reply & can_purge)
async def int_purge(c, m):
    try:
        count = int(m.command[1])
    except IndexError:
        await m.reply("__specifiy number of messages to delete__")
        return
    messages = list(range(m.message_id - 1, m.message_id - 1 - count, -1))
    start, end = messages[-1], messages[0]
    while len(messages) != 0:
        await c.send(
            raw.functions.channels.DeleteMessages(
                channel=await c.resolve_peer(m.chat.id), id=messages))
        del messages[0:100]
    await c.send_message(
        text=f"Purged {count} messages from {start} to {end}",chat_id=m.chat.id)

