from asyncio import sleep
from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, CommandHandler
from telegram.ext import CallbackContext, run_async
from telethon import events
from AstrakoBot import dispatcher
from AstrakoBot import telethn as AstrakoBotTelethonClient
from AstrakoBot.modules.helper_funcs.telethn.chatstatus import user_is_admin


@AstrakoBotTelethonClient.on(events.NewMessage(pattern=f"^[!/]zombies ?(.*)"))
async def zombies(event):
    chat = await event.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    if not await user_is_admin(
        user_id = event.sender_id, message = event
    ):
        msg = f"Only Admins are allowed to use this command"

    elif not admin and not creator:
        msg = f"I am not an admin here!"

    else:

        count = 0
        arg = event.pattern_match.group(1).lower()

        if not arg:
                msg = f"**Searching for zombies...**\n"
                async for user in event.client.iter_participants(event.chat):
                    if user.deleted:
                        count += 1

                if count == 0:
                    msg += f"No deleted accounts found. Group is clean"
                else:
                    msg += f"Found **{count}** zombies in this group\n"
                    msg += f"Clean them by using - `/zombies clean`"
        
        elif arg == "clean":
            msg = f"**Cleaning zombies...**\n"
            async for user in event.client.iter_participants(event.chat):
                if user.deleted:
                    count += 1
                    await event.client.kick_participant(chat, user)

            if count == 0:
                msg += f"No zombies account found. Group is clean"
            else:
                msg += f"Cleaned `{count}` zombies"
      
        else:
            msg = "Wrong parameter. You can use only `/zombies clean`"


    delmsg = await event.reply(msg)
    await sleep(60)
    await delmsg.delete()

