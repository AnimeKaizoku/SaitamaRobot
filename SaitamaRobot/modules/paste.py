from pyrogram import filters
from SaitamaRobot import app
import aiohttp


@app.on_message(filters.command('paste'))
async def paste(c, m):
    async with aiohttp.ClientSession() as sess:
        async with sess.post(
                "https://nekobin.com/api/documents",
                json={'content': m.reply_to_message.text}) as response:
            key = (await response.json())['result']['key']
    await m.reply(f"**Nekofied To :** __{'https://nekobin.com/'+key}__")
