import asyncio
from asyncio import sleep

from telethon import events
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsAdmins
from AstrakoBot.modules.helper_funcs.telethn.chatstatus import user_is_admin
from AstrakoBot import telethn, OWNER_ID, DEV_USERS, DRAGONS, DEMONS

# =================== CONSTANT ===================

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)


UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

OFFICERS = [OWNER_ID] + DEV_USERS + DRAGONS + DEMONS

@telethn.on(events.NewMessage(pattern=f"^[!/]zombies ?(.*)"))
async def zombies(event):
    # Here laying the sanity check
    chat = await event.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not await user_is_admin(
        user_id=event.sender_id, message=event
    ):
        await event.reply("Only Admins are allowed to use this command")
        return

    if not admin and not creator:
        await event.respond("I am not an admin here!")
        return
    con = event.pattern_match.group(1).lower()
    del_u = 0
    del_status = "No deleted accounts found, group is clean."

    if con != "clean":
        find_zombies = await event.respond("Searching for zombies...")
        async for user in event.client.iter_participants(event.chat_id):

            if user.deleted:
                del_u += 1
                await sleep(1)
        if del_u > 0:
            del_status = f"Found **{del_u}** zombies in this group.\
            \nClean them by using - `/zombies clean`"
        await find_zombies.edit(del_status)
        return

    cleaning_zombies = await event.respond("Cleaning zombies...")
    del_u = 0
    del_a = 0

    async for user in event.client.iter_participants(event.chat_id):
        if user.deleted:
            try:
                await event.client(
                    EditBannedRequest(event.chat_id, user.id, BANNED_RIGHTS)
                )
            except ChatAdminRequiredError:
                await cleaning_zombies.edit("I don't have ban rights in this group.")
                return
            except UserAdminInvalidError:
                del_u -= 1
                del_a += 1
            await event.client(EditBannedRequest(event.chat_id, user.id, UNBAN_RIGHTS))
            del_u += 1

    if del_u > 0:
        del_status = f"Cleaned `{del_u}` zombies"

    if del_a > 0:
        del_status = f"Cleaned `{del_u}` zombies \
        \n`{del_a}` Zombie admin accounts are not removed!"

    await cleaning_zombies.edit(del_status)
