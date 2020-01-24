
import requests
import asyncio
from telegram.ext import CommandHandler, run_async
from telegram import Message, Chat, Update, Bot, MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton
from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from telegram import ParseMode
# fell free to remove useless imports
#Made by t.me/DragSama
#Uses https://jikan.moe/
#Try a one liner if you want( I tried but there were alignment issues )
base_url = "https://api.jikan.moe/v3"

bt1 = "More Information" #1st button, 1st row on anime and manga
bt2 = "Watch Trailer" #2nd button, 1st row on anime
bt3 = "Download from Kayo" #3rd button, 2nd row on anime
bt4 = "Download From Kaizoku" #4th button, 2nd row on anime

@run_async
def myanime(bot: Bot, update: Update):
    message = update.effective_message
    text = message.text[len('/myanime '):]
    if text == '':
        update.effective_message.reply_text("Format : /myanime <animename>")
        exit()
    search = text.replace(" ", "%20")
    r = requests.get('{}/search/anime?q={}&page=1'.format(base_url, search))
    c = r.json()
    mal_id = (c.get("results")[0].get("mal_id"))
    anime = requests.get('{}/anime/{}'.format(base_url, mal_id))
    animedata = anime.json()
    genrec = len(animedata.get("genres"))
    msg = ""
    v = 0
    trailer = (animedata.get("trailer_url"))
    information = (animedata.get("url"))
    airedfromto = (animedata.get("aired").get("string"))
    msg += f"[{animedata['title']}]({animedata['image_url']})(`{animedata['title_japanese']}`)\n"
    msg += f"*Type* : `{animedata['type']}` \n"
    msg += f"*Source* : `{animedata['source']}` \n"
    msg += f"*Status* : `{animedata['status']}` \n"
    msg += "*Aired* : `{}` \n".format(airedfromto)
    msg += f"*Episodes* : `{animedata['episodes']}` \n"
    msg += f"*Duration* : `{animedata['duration']}` \n"
    msg += f"*Score* : `{animedata['score']}` \n"
    msg += f"*Rank* : `{animedata['rank']}` \n"
    msg += f"*Genres* : "
    for x in range(genrec):
        a = (animedata.get("genres")[v].get("name"))
        msg += "`{}`, ".format(a)
        a = None
        v += 1
    msg = msg[:-2]
    kaizoku = "https://animekaizoku.com//?s={}".format(search)
    kayo = "https://animekayo.com//?s={}".format(search)
    if trailer:
        buttons = [
            [InlineKeyboardButton(bt1, url=information),
             InlineKeyboardButton(bt2, url=trailer)],
            
            [InlineKeyboardButton(bt3, url=kayo),
             InlineKeyboardButton(bt4, url=kaizoku)]
        ]
    else:
        buttons = [
             [InlineKeyboardButton(bt1, url=information)]
            
            [InlineKeyboardButton(bt3, url=kayo),
             InlineKeyboardButton(bt4, url=kaizoku)]
         ]
    msg += f"\n*Synopsis* : _ {animedata['synopsis']} _"
    update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))

@run_async
def mymanga(bot: Bot, update: Update):
    message = update.effective_message
    text = message.text[len('/mymanga '):]
    if text == '':
        update.effective_message.reply_text("Format : /mymanga <manganame>")
        exit()
    search = text.replace(" ", "%20")
    r = requests.get('{}/search/manga?q={}&page=1'.format(base_url, search))
    c = r.json()
    mal_id = (c.get("results")[0].get("mal_id"))
    manga = requests.get('{}/manga/{}'.format(base_url, mal_id))
    mangadata = manga.json()
    genrec = len(mangadata.get("genres"))
    msg = ""
    v = 0
    information = (mangadata.get("url"))
    msg += f"*Title* : [{mangadata['title']}]({mangadata['image_url']}) \n"
    msg += f"*Type* : `{mangadata['type']}` \n"
    msg += f"*Status* : `{mangadata['status']}` \n"
    msg += f"*Volumes* : `{mangadata['volumes']}` \n"
    msg += f"*Chapters* : `{mangadata['chapters']}` \n"
    msg += f"*Score* : `{mangadata['score']}` \n"
    msg += f"*Rank* : `{mangadata['rank']}` \n"
    msg += f"*Genres* : "
    for x in range(genrec):
        a = (mangadata.get("genres")[v].get("name"))
        msg += "`{}`, ".format(a)
        a = None
        v += 1
    msg = msg[:-2]
    if search:
        buttons = [
            [InlineKeyboardButton(bt1, url=information)]
        ]
    else: #too lazy to remove this, do if You can. 
        buttons = [
             [InlineKeyboardButton(bt1, url=information)]
         ]
    msg += f"\n*Synopsis* : _ {mangadata['synopsis']} _"
    update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
    
@run_async
def upcoming(bot: Bot, update: Update):
    v = 0
    rank = 1
    msg = "Top Upcoming Anime: \n"
    r = requests.get("https://api.jikan.moe/v3/top/anime/1/upcoming")
    c = r.json()
    for x in range(10): #number of results to get
        a = (c.get("top")[v].get("title"))
        msg += "{}.`{}` \n".format(rank, a)
        a = None
        v += 1
        rank += 1
    update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

@run_async
def mycharacter(bot: Bot, update: Update):
    v = 0
    rank = 1
    msg = ""
    message = update.effective_message
    text = message.text[len('/mycharacter '):]
    if text == '':
        update.effective_message.reply_text("Format : /mycharacter <charactername>")
        exit()
    search = text.replace(" ", "%20")
    r = requests.get('{}/search/character?q={}&limit=1'.format(base_url, search))
    c = r.json()
    mal_id = (c.get("results")[0].get("mal_id"))
    character = requests.get('{}/character/{}'.format(base_url, mal_id))
    characterdata = character.json()
    nicknames = (characterdata.get('nicknames'))
    msg += f"*Name* : [{characterdata['name']}]({characterdata['image_url']}) \n"
    msg += f"Name-Kanji : {characterdata['name_kanji']}\n"
    msg += "*Nickname(s)* : "
    for nick in nicknames:
        msg += f"{nicknames[v]},"
        v += 1
    msg = msg[:-2]
    msg += f"\n{characterdata['about']}"
    update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

__help__ = """
Get information about anime, manga or characters from [MyAnimeList](https://myanimelist.net).

*Available commands:*

 - /myanime <anime>: returns information about the anime.

 - /mycharacter <character>: returns information about the character.

 - /mymanga <manga>: returns information about the manga.

 - /upcoming: returns a list of new anime in the upcoming seasons.

 """

__mod_name__ = "MyAnimeList"

ANIME_HANDLER = CommandHandler("myanime", myanime)

CHARACTER_HANDLER = CommandHandler("mycharacter", mycharacter)

UPCOMING_HANDLER = CommandHandler("upcoming", upcoming)

MANGA_HANDLER = CommandHandler("mymanga", mymanga)


dispatcher.add_handler(ANIME_HANDLER)

dispatcher.add_handler(CHARACTER_HANDLER)

dispatcher.add_handler(UPCOMING_HANDLER)

dispatcher.add_handler(MANGA_HANDLER)
