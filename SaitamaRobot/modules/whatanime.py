import os
import time
import html
import aiohttp
import asyncio
import datetime
import tempfile
from decimal import Decimal
from urllib.parse import quote as urlencode
from pyrogram import Client, filters
from telegram.ext import CallbackContext, run_async
from SaitamaRobot import DEV_USERS, OWNER_ID, DRAGONS, dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler

session = aiohttp.ClientSession()

@run_async.on_message(~filters.me & filters.command('wa', prefixes='/'), group=8)
async def whatanime(client, message):
    media = message.photo or message.animation or message.video or message.document
    if not media:
        reply = message.reply_to_message
        if not getattr(reply, 'empty', True):
            media = reply.photo or reply.animation or reply.video or reply.document
    if not media:
        await message.reply_text('Photo or GIF or Video required')
        return
    with tempfile.TemporaryDirectory() as tempdir:
        reply = await message.reply_text('Downloading...')
        path = await client.download_media(media, file_name=os.path.join(tempdir, '0'), progress=progress_callback, progress_args=(reply,))
        new_path = os.path.join(tempdir, '1.png')
        proc = await asyncio.create_subprocess_exec('ffmpeg', '-i', path, '-frames:v', '1', new_path)
        await proc.communicate()
        await reply.edit_text('Uploading...')
        with open(new_path, 'rb') as file:
            async with session.post('https://trace.moe/api/search', data={'image': file}) as resp:
                json = await resp.json()
    if isinstance(json, str):
        await reply.edit_text(html.escape(json))
    else:
        try:
            match = next(iter(json['docs']))
        except StopIteration:
            await reply.edit_text('No match')
        else:
            nsfw = match['is_adult']
            title_native = match['title_native']
            title_english = match['title_english']
            title_romaji = match['title_romaji']
            synonyms = ', '.join(match['synonyms'])
            filename = match['filename']
            tokenthumb = match['tokenthumb']
            anilist_id = match['anilist_id']
            episode = match['episode']
            similarity = match['similarity']
            from_time = str(datetime.timedelta(seconds=match['from'])).split('.', 1)[0].rjust(8, '0')
            to_time = str(datetime.timedelta(seconds=match['to'])).split('.', 1)[0].rjust(8, '0')
            at_time = match['at']
            text = f'<a href="https://anilist.co/anime/{anilist_id}">{title_romaji}</a>'
            if title_english:
                text += f' ({title_english})'
            if title_native:
                text += f' ({title_native})'
            if synonyms:
                text += f'\n<b>Synonyms:</b> {synonyms}'
            text += f'\n<b>Similarity:</b> {(Decimal(similarity) * 100).quantize(Decimal(".01"))}%\n'
            if episode:
                text += f'<b>Episode:</b> {episode}\n'
            if nsfw:
                text += '<b>Hentai/NSFW:</b> Yes'
            async def _send_preview():
                url = f'https://media.trace.moe/video/{anilist_id}/{urlencode(filename)}?t={at_time}&token={tokenthumb}'
                with tempfile.NamedTemporaryFile() as file:
                    async with session.get(url) as resp:
                        while True:
                            chunk = await resp.content.read(10)
                            if not chunk:
                                break
                            file.write(chunk)
                    file.seek(0)
                    try:
                        await reply.reply_video(file.name, caption=f'{from_time} - {to_time}')
                    except Exception:
                        await reply.reply_text('Cannot send preview :/')
            await asyncio.gather(reply.edit_text(text, disable_web_page_preview=True), _send_preview())

progress_callback_data = {}
async def progress_callback(current, total, reply):
    message_identifier = (reply.chat.id, reply.message_id)
    last_edit_time, prevtext, start_time = progress_callback_data.get(message_identifier, (0, None, time.time()))
    if current == total:
        try:
            progress_callback_data.pop(message_identifier)
        except KeyError:
            pass
    elif (time.time() - last_edit_time) > 1:
        if last_edit_time:
            download_speed = format_bytes((total - current) / (time.time() - start_time))
        else:
            download_speed = '0 B'
        text = f'''Downloading...
<code>{return_progress_string(current, total)}</code>

<b>Total Size:</b> {format_bytes(total)}
<b>Downladed Size:</b> {format_bytes(current)}
<b>Download Speed:</b> {download_speed}/s
<b>ETA:</b> {calculate_eta(current, total, start_time)}'''
        if prevtext != text:
            await reply.edit_text(text)
            prevtext = text
            last_edit_time = time.time()
            progress_callback_data[message_identifier] = last_edit_time, prevtext, start_time
