import aiohttp
from pyrogram import filters
from bs4 import BeautifulSoup as bs
from SaitamaRobot import app


@app.on_message(filters.command('cash'))
async def curr_converter(c, m):
    try:
        amount = m.command[1]
        from_, to = m.command[2], m.command[3]
    except IndexError:
        await m.reply("Invalid Format")
        return
    query = f"https://www.x-rates.com/calculator/?from={from_}&to={to}&amount={amount}"
    async with aiohttp.ClientSession() as sess:
        async with sess.get(query) as resp:
            data = await resp.text()
    soup = bs(data, 'lxml')
    result = soup.find('span', class_="ccOutputRslt").get_text()
    if '-' in result:
        await m.reply("Invalid Currency Format")
        return
    await m.reply(f"__{amount} {from_.upper()}__ = **{result}**")
