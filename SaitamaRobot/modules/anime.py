import datetime
import html
import textwrap
import json

import bs4
import jikanpy
import requests
from telegram.utils.helpers import mention_html
from telegram.error import BadRequest
from SaitamaRobot import DEV_USERS, OWNER_ID, DRAGONS, REDIS, dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update ,replymarkup)
from telegram.ext import CallbackContext, CallbackQueryHandler, run_async

info_btn = "More Information"
prequel_btn = "⬅️"
sequel_btn = "➡️"
close_btn = "❌"


def shorten(description, info='anilist.co'):
    msg = ""
    if len(description) > 700:
        description = description[0:500] + '....'
        msg += f"\n*Description*: _{description}_[Read More]({info})"
    else:
        msg += f"\n*Description*:_{description}_"
    return msg


#time formatter from uniborg
def t(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time,
    as string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + " Days, ") if days else "") + \
        ((str(hours) + " Hours, ") if hours else "") + \
        ((str(minutes) + " Minutes, ") if minutes else "") + \
        ((str(seconds) + " Seconds, ") if seconds else "") + \
        ((str(milliseconds) + " ms, ") if milliseconds else "")
    return tmp[:-2]


airing_query = '''
    query ($id: Int,$search: String) { 
      Media (id: $id, type: ANIME,search: $search) { 
        id
        episodes
        title {
          romaji
          english
          native
        }
        nextAiringEpisode {
           airingAt
           timeUntilAiring
           episode
        } 
      }
    }
    '''

fav_query = """
query ($id: Int) { 
      Media (id: $id, type: ANIME) { 
        id
        title {
          romaji
          english
          native
        }
     }
}
"""

anime_query = '''
   query ($id: Int,$search: String) { 
      Media (id: $id, type: ANIME,search: $search) { 
        id
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          episodes
          season
          type
          format
          status
          duration
          siteUrl
          studios{
              nodes{
                   name
              }
          }
          trailer{
               id
               site 
               thumbnail
          }
          averageScore
          genres
          bannerImage
      }
    }
'''
character_query = """
    query ($query: String) {
        Character (search: $query) {
               id
               name {
                     first
                     last
                     full
               }
               siteUrl
               image {
                        large
               }
               description
        }
    }
"""

manga_query = """
query ($id: Int,$search: String) { 
      Media (id: $id, type: MANGA,search: $search) { 
        id
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          type
          format
          status
          siteUrl
          averageScore
          genres
          bannerImage
      }
    }
"""

url = 'https://graphql.anilist.co'


@run_async
def airing(update, context):
    message = update.effective_message
    search_str = message.text.split(' ', 1)
    if len(search_str) == 1:
        update.effective_message.reply_text(
            'Tell Anime Name :) ( /airing <anime name>)')
        return
    variables = {'search': search_str[1]}
    response = requests.post(
        url, json={
            'query': airing_query,
            'variables': variables
        }).json()['data']['Media']
    msg = f"*Name*: *{response['title']['romaji']}*(`{response['title']['native']}`)\n*ID*: `{response['id']}`"
    if response['nextAiringEpisode']:
        time = response['nextAiringEpisode']['timeUntilAiring'] * 1000
        time = t(time)
        msg += f"\n*Episode*: `{response['nextAiringEpisode']['episode']}`\n*Airing In*: `{time}`"
    else:
        msg += f"\n*Episode*:{response['episodes']}\n*Status*: `N/A`"
    update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@run_async
def anime(update, context):
    message = update.effective_message
    user = update.effective_user
    search = message.text.split(' ', 1)
    if len(search) == 1:
        update.effective_message.reply_text('Format : /anime < anime name >')
        return
    else:
        search = search[1]
    variables = {'search': search}
    json = requests.post(
        url, json={
            'query': anime_query,
            'variables': variables
        }).json()
    if 'errors' in json.keys():
        update.effective_message.reply_text('Anime not found')
        return
    if json:
        json = json['data']['Media']
        msg = f"*{json['title']['romaji']}*(`{json['title']['native']}`)\n*Type*: {json['format']}\n*Status*: {json['status']}\n*Episodes*: {json.get('episodes', 'N/A')}\n*Duration*: {json.get('duration', 'N/A')} Per Ep.\n*Score*: {json['averageScore']}\n*Genres*: `"
        for x in json['genres']:
            msg += f"{x}, "
        msg = msg[:-2] + '`\n'
        msg += "*Studios*: `"
        for x in json['studios']['nodes']:
            msg += f"{x['name']}, "
        msg = msg[:-2] + '`\n'
        anime_name_w = f"{json['title']['romaji']}"
        info = json.get('siteUrl')
        trailer = json.get('trailer', None)
        anime_id = json['id']
        if trailer:
            trailer_id = trailer.get('id', None)
            site = trailer.get('site', None)
            if site == "youtube":
                trailer = 'https://youtu.be/' + trailer_id
        description = json.get('description', 'N/A').replace('<i>', '').replace(
            '</i>', '').replace('<br>', '')
        msg += shorten(description, info)
        image = json.get('bannerImage', None)
        if trailer:
            buttons = [[
                InlineKeyboardButton("More Info", url=info),
                InlineKeyboardButton("Trailer 🎬", url=trailer)
            ]]
        else:
            buttons = [[InlineKeyboardButton("More Info", url=info)]]
        buttons += [[InlineKeyboardButton("💬Add To Watchlist🔴", callback_data=f"xanime_watchlist={anime_name_w}")]]
        if image:
            try:
                update.effective_message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons))
            except:
                msg += f" [〽️]({image})"
                update.effective_message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons))
        else:
            update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons))


@run_async
def character(update, context):
    message = update.effective_message
    search = message.text.split(' ', 1)
    if len(search) == 1:
        update.effective_message.reply_text(
            'Format : /character < character name >')
        return
    search = search[1]
    variables = {'query': search}
    json = requests.post(
        url, json={
            'query': character_query,
            'variables': variables
        }).json()
    if 'errors' in json.keys():
        update.effective_message.reply_text('Character not found')
        return
    if json:
        json = json['data']['Character']
        msg = f"*{json.get('name').get('full')}*(`{json.get('name').get('native')}`)\n"
        description = f"{json['description']}"
        site_url = json.get('siteUrl')
        char_name = f"{json.get('name').get('full')}"
        msg += shorten(description, site_url)
        image = json.get('image', None)
        if image:
            image = image.get('large')
            buttons = [[InlineKeyboardButton("Add To Favorite Character😎", callback_data=f"xanime_fvrtchar={char_name}")]]
            update.effective_message.reply_photo(
                photo=image,
                caption=msg.replace('<b>', '</b>'),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text(
                msg.replace('<b>', '</b>'),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN)


@run_async
def manga(update, context):
    message = update.effective_message
    search = message.text.split(' ', 1)
    if len(search) == 1:
        update.effective_message.reply_text('Format : /manga < manga name >')
        return
    search = search[1]
    variables = {'search': search}
    json = requests.post(
        url, json={
            'query': manga_query,
            'variables': variables
        }).json()
    msg = ''
    if 'errors' in json.keys():
        update.effective_message.reply_text('Manga not found')
        return
    if json:
        json = json['data']['Media']
        title, title_native = json['title'].get('romaji',
                                                False), json['title'].get(
                                                    'native', False)
        start_date, status, score = json['startDate'].get(
            'year', False), json.get('status',
                                     False), json.get('averageScore', False)
        if title:
            msg += f"*{title}*"
            if title_native:
                msg += f"(`{title_native}`)"
        if start_date:
            msg += f"\n*Start Date* - `{start_date}`"
        if status:
            msg += f"\n*Status* - `{status}`"
        if score:
            msg += f"\n*Score* - `{score}`"
        msg += '\n*Genres* - '
        for x in json.get('genres', []):
            msg += f"{x}, "
        msg = msg[:-2]
        info = json['siteUrl']
        buttons = [[InlineKeyboardButton("More Info", url=info)]]
        buttons += [[InlineKeyboardButton("Add To Read List📖", callback_data=f"xanime_manga={title}")]]
        image = json.get("bannerImage", False)
        msg += f"_{json.get('description', None)}_"
        if image:
            try:
                update.effective_message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons))
            except:
                msg += f" [〽️]({image})"
                update.effective_message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons))
        else:
            update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons))


@run_async
def user(update, context):
    message = update.effective_message
    args = message.text.strip().split(" ", 1)

    try:
        search_query = args[1]
    except:
        if message.reply_to_message:
            search_query = message.reply_to_message.text
        else:
            update.effective_message.reply_text("Format : /user <username>")
            return

    jikan = jikanpy.jikan.Jikan()

    try:
        user = jikan.user(search_query)
    except jikanpy.APIException:
        update.effective_message.reply_text("Username not found.")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")

    date_format = "%Y-%m-%d"
    if user['image_url'] is None:
        img = "https://cdn.myanimelist.net/images/questionmark_50.gif"
    else:
        img = user['image_url']

    try:
        user_birthday = datetime.datetime.fromisoformat(user['birthday'])
        user_birthday_formatted = user_birthday.strftime(date_format)
    except:
        user_birthday_formatted = "Unknown"

    user_joined_date = datetime.datetime.fromisoformat(user['joined'])
    user_joined_date_formatted = user_joined_date.strftime(date_format)

    for entity in user:
        if user[entity] is None:
            user[entity] = "Unknown"

    about = user['about'].split(" ", 60)

    try:
        about.pop(60)
    except IndexError:
        pass

    about_string = ' '.join(about)
    about_string = about_string.replace("<br>",
                                        "").strip().replace("\r\n", "\n")

    caption = ""

    caption += textwrap.dedent(f"""
    *Username*: [{user['username']}]({user['url']})
    *Gender*: `{user['gender']}`
    *Birthday*: `{user_birthday_formatted}`
    *Joined*: `{user_joined_date_formatted}`
    *Days wasted watching anime*: `{user['anime_stats']['days_watched']}`
    *Days wasted reading manga*: `{user['manga_stats']['days_read']}`
    """)

    caption += f"*About*: {about_string}"

    buttons = [[InlineKeyboardButton(info_btn, url=user['url'])],
               [
                   InlineKeyboardButton(
                       close_btn,
                       callback_data=f"anime_close, {message.from_user.id}")
               ]]

    update.effective_message.reply_photo(
        photo=img,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=False)
    progress_message.delete()


@run_async
def upcoming(update, context):
    jikan = jikanpy.jikan.Jikan()
    upcoming = jikan.top('anime', page=1, subtype="upcoming")

    upcoming_list = [entry['title'] for entry in upcoming['top']]
    upcoming_message = ""

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"{entry_num + 1}. {upcoming_list[entry_num]}\n"

    update.effective_message.reply_text(upcoming_message)
    
def anime_quote():
    url = "https://animechanapi.xyz/api/quotes/random"
    response = requests.get(url)
    # since text attribute returns dictionary like string
    dic = json.loads(response.text)
    quote = dic["data"][0]["quote"]
    character = dic["data"][0]["character"]
    anime = dic["data"][0]["anime"]
    return quote, character, anime


@run_async
def quotes(update: Update, context: CallbackContext):
    message = update.effective_message
    quote, character, anime = anime_quote()
    msg = f"<i>❝{quote}❞</i>\n\n<b>{character} from {anime}</b>"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text="Change🔁", callback_data="change_quote")]]
    )
    message.reply_text(
        msg,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


@run_async
def change_quote(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    quote, character, anime = anime_quote()
    msg = f"<i>❝{quote}❞</i>\n\n<b>{character} from {anime}</b>"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text="Change🔁", callback_data="quote_change")]]
    )
    message.edit_text(msg, reply_markup=keyboard, parse_mode=ParseMode.HTML)



@run_async
def watchlist(update, context):
    chat = update.effective_chat  
    user = update.effective_user 
    message = update.effective_message  
    watchlist = list(REDIS.sunion(f'anime_watch_list{user.id}'))
    watchlist.sort()
    watchlist = "\n• ".join(watchlist)
    if watchlist:
        message.reply_text(
            "{}<b>'s Watchlist:</b>"
            "\n• {}".format(mention_html(user.id, user.first_name),
                        watchlist),
            parse_mode=ParseMode.HTML
        )
    else:
        message.reply_text(
            "You havn't added anything in your watchlist!"
        )
@run_async
def removewatchlist(update, context):
    user = update.effective_user 
    message = update.effective_message 
    removewlist = message.text.split(' ', 1) 
    args = context.args
    query = " ".join(args)
    if not query:
        message.reply_text("Please enter a anime name to remove from your watchlist.")
        return
    watchlist = list(REDIS.sunion(f'anime_watch_list{user.id}'))
    removewlist = removewlist[1]
    
    if removewlist not in watchlist:
        message.reply_text(
            f"<code>{removewlist}</code> doesn't exist in your watch list.",
            parse_mode=ParseMode.HTML
        )
    else:
        message.reply_text(
            f"<code>{removewlist}</code> has been removed from your watch list.",
            parse_mode=ParseMode.HTML
        )
        REDIS.srem(f'anime_watch_list{user.id}', removewlist)

@run_async
def fvrtchar(update, context):
    chat = update.effective_chat  
    user = update.effective_user 
    message = update.effective_message  
    fvrt_char = list(REDIS.sunion(f'anime_fvrtchar{user.id}'))
    fvrt_char.sort()
    fvrt_char = "\n• ".join(fvrt_char)
    if fvrt_char:
        message.reply_text(
            "{}<b>'s Favorite Characters List:</b>"
            "\n• {}".format(mention_html(user.id, user.first_name),
                        fvrt_char),
            parse_mode=ParseMode.HTML
        )
    else:
        message.reply_text(
            "You havn't added anything in your favorite characters list!"
        )
        
@run_async
def removefvrtchar(update, context):
    user = update.effective_user 
    message = update.effective_message 
    removewlist = message.text.split(' ', 1) 
    args = context.args
    query = " ".join(args)
    if not query:
        message.reply_text("Please enter a your favorite character name to remove from your favorite characters list.")
        return
    fvrt_char = list(REDIS.sunion(f'anime_fvrtchar{user.id}'))
    removewlist = removewlist[1]
    
    if removewlist not in fvrt_char:
        message.reply_text(
            f"<code>{removewlist}</code> doesn't exist in your favorite characters list.",
            parse_mode=ParseMode.HTML
        )
    else:
        message.reply_text(
            f"<code>{removewlist}</code> has been removed from your favorite characters list.",
            parse_mode=ParseMode.HTML
        )
        REDIS.srem(f'anime_fvrtchar{user.id}', removewlist)
    
@run_async
def readmanga(update, context):
    chat = update.effective_chat  
    user = update.effective_user 
    message = update.effective_message  
    manga_list = list(REDIS.sunion(f'anime_mangaread{user.id}'))
    manga_list.sort()
    manga_list = "\n• ".join(manga_list)
    if manga_list:
        message.reply_text(
            "{}<b>'s Manga Lists:</b>"
            "\n• {}".format(mention_html(user.id, user.first_name),
                        manga_list),
            parse_mode=ParseMode.HTML
        )
    else:
        message.reply_text(
            "You havn't added anything in your manga list!"
        )
        
@run_async
def removemangalist(update, context):
    user = update.effective_user 
    message = update.effective_message 
    removewlist = message.text.split(' ', 1) 
    args = context.args
    query = " ".join(args)
    if not query:
        message.reply_text("Please enter a manga name to remove from your manga list.")
        return
    fvrt_char = list(REDIS.sunion(f'anime_mangaread{user.id}'))
    removewlist = removewlist[1]
    
    if removewlist not in fvrt_char:
        message.reply_text(
            f"<code>{removewlist}</code> doesn't exist in your manga list.",
            parse_mode=ParseMode.HTML
        )
    else:
        message.reply_text(
            f"<code>{removewlist}</code> has been removed from your favorite characters list.",
            parse_mode=ParseMode.HTML
        )
        REDIS.srem(f'anime_mangaread{user.id}', removewlist)

def animestuffs(update, context):
    query = update.callback_query
    user = update.effective_user
    splitter = query.data.split('=')
    query_match = splitter[0]
    callback_anime_data = splitter[1] 
    if query_match == "xanime_watchlist":
        watchlist = list(REDIS.sunion(f'anime_watch_list{user.id}'))
        if not callback_anime_data in watchlist:
            REDIS.sadd(f'anime_watch_list{user.id}', callback_anime_data)
            context.bot.answer_callback_query(query.id,
                                                text=f"{callback_anime_data} is successfully added to your watch list.",
                                                show_alert=True)
        else:
            context.bot.answer_callback_query(query.id,
                                                text=f"{callback_anime_data} is already exists in your watch list!",
                                                show_alert=True)
            
    elif query_match == "xanime_fvrtchar":   
        fvrt_char = list(REDIS.sunion(f'anime_fvrtchar{user.id}'))
        if not callback_anime_data in fvrt_char:
            REDIS.sadd(f'anime_fvrtchar{user.id}', callback_anime_data)
            context.bot.answer_callback_query(query.id,
                                                text=f"{callback_anime_data} is successfully added to your favorite character.",
                                                show_alert=True)
        else:
            context.bot.answer_callback_query(query.id,
                                                text=f"{callback_anime_data} is already exists in your favorite characters list!",
                                                show_alert=True)
    elif query_match == "xanime_manga":   
        fvrt_char = list(REDIS.sunion(f'anime_mangaread{user.id}'))
        if not callback_anime_data in fvrt_char:
            REDIS.sadd(f'anime_mangaread{user.id}', callback_anime_data)
            context.bot.answer_callback_query(query.id,
                                                text=f"{callback_anime_data} is successfully added to your read list.",
                                                show_alert=True)
        else:
            context.bot.answer_callback_query(query.id,
                                                text=f"{callback_anime_data} is already exists in your read list!",
                                                show_alert=True)
            

    
def button(update, context):
    bot = context.bot
    query = update.callback_query
    message = query.message
    data = query.data.split(", ")
    print(data)
    query_type = data[0]
    original_user_id = int(data[1])

    user_and_admin_list = [original_user_id, OWNER_ID] + DRAGONS + DEV_USERS 

    bot.answer_callback_query(query.id)
    if query_type == "anime_close":
        if query.from_user.id in user_and_admin_list:
            message.delete()
        else:
            query.answer("You are not allowed to use this.")
    elif query_type in ('anime_anime', 'anime_manga'):
        mal_id = data[2]
        if query.from_user.id == original_user_id:
            message.delete()
            progress_message = bot.sendMessage(message.chat.id,
                                               "Searching.... ")
            caption, buttons, image = get_anime_manga(mal_id, query_type,
                                                      original_user_id)
            bot.sendPhoto(
                message.chat.id,
                photo=image,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=False)
            progress_message.delete()
        else:
            query.answer("You are not allowed to use this.")




__help__ = """
Get information about anime, manga or characters from [AniList](anilist.co).
*Available commands:*
 - /anime <anime>: returns information about the anime.
 - /character <character>: returns information about the character.
 - /manga <manga>: returns information about the manga.
 - /user <user>: returns information about a MyAnimeList user.
 - /upcoming: returns a list of new anime in the upcoming seasons.
 - /airing <anime>: returns anime airing info.
 - /aq: get random anime quote
 - /kaizoku <anime>: search an anime on animekaizoku.com
 - /kayo <anime>: search an anime on animekayo.com
 - /watchlist: to get your saved watchlist.
 - /mangalist: to get your saved manga read list.
 - /characterlist | fcl: to get your favorite characters list.
 - /removewatchlist | rwl <anime>: to remove a anime from your list.
 - /rfcharacter | rfcl <character>: to remove a character from your list.  
 - /rmanga | rml <manga>: to remove a manga from your list.
 """

ANIME_HANDLER = DisableAbleCommandHandler("anime", anime)
AIRING_HANDLER = DisableAbleCommandHandler("airing", airing)
CHARACTER_HANDLER = DisableAbleCommandHandler("character", character)
MANGA_HANDLER = DisableAbleCommandHandler("manga", manga)
USER_HANDLER = DisableAbleCommandHandler("user", user)
UPCOMING_HANDLER = DisableAbleCommandHandler("upcoming", upcoming)
QUOTE = DisableAbleCommandHandler("aq", quotes)
CHANGE_QUOTE = CallbackQueryHandler(change_quote, pattern=r"change_.*")
QUOTE_CHANGE = CallbackQueryHandler(change_quote, pattern=r"quote_.*")
WATCHLIST_HANDLER = DisableAbleCommandHandler("watchlist", watchlist)
MANGALIST_HANDLER = DisableAbleCommandHandler("mangalist", readmanga)
FVRT_CHAR_HANDLER = DisableAbleCommandHandler(["characterlist","fcl"], fvrtchar)
REMOVE_WATCHLIST_HANDLER = DisableAbleCommandHandler(["rmwatchlist","rwl"], removewatchlist)
REMOVE_FVRT_CHAR_HANDLER = DisableAbleCommandHandler(["rmfcharacter","rfcl"], removefvrtchar)
REMOVE_MANGA_CHAR_HANDLER = DisableAbleCommandHandler(["rmmanga","rml"], removemangalist)
BUTTON_HANDLER = CallbackQueryHandler(button, pattern='anime_.*')
ANIME_STUFFS_HANDLER = CallbackQueryHandler(animestuffs, pattern='xanime_.*')

dispatcher.add_handler(BUTTON_HANDLER)
dispatcher.add_handler(ANIME_STUFFS_HANDLER)
dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(CHARACTER_HANDLER)
dispatcher.add_handler(MANGA_HANDLER)
dispatcher.add_handler(AIRING_HANDLER)
dispatcher.add_handler(USER_HANDLER)
dispatcher.add_handler(UPCOMING_HANDLER)
dispatcher.add_handler(QUOTE)
dispatcher.add_handler(CHANGE_QUOTE)
dispatcher.add_handler(QUOTE_CHANGE)
dispatcher.add_handler(WATCHLIST_HANDLER)
dispatcher.add_handler(MANGALIST_HANDLER)
dispatcher.add_handler(FVRT_CHAR_HANDLER)
dispatcher.add_handler(REMOVE_FVRT_CHAR_HANDLER)
dispatcher.add_handler(REMOVE_MANGA_CHAR_HANDLER)
dispatcher.add_handler(REMOVE_WATCHLIST_HANDLER)

__mod_name__ = "Anime"

dispatcher.add_handler(UPCOMING_HANDLER)
dispatcher.add_handler(WATCHLIST_HANDLER)
dispatcher.add_handler(MANGALIST_HANDLER)
dispatcher.add_handler(FVRT_CHAR_HANDLER)
dispatcher.add_handler(REMOVE_FVRT_CHAR_HANDLER)
dispatcher.add_handler(REMOVE_MANGA_CHAR_HANDLER)
dispatcher.add_handler(REMOVE_WATCHLIST_HANDLER)

__mod_name__ = "Anime"
