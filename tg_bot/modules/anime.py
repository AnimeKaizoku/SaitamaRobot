import requests, jikanpy, textwrap, datetime

from telegram.ext import CallbackQueryHandler, run_async
from telegram import Message, Update, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ParseMode

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, DEV_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler

info_btn = "More Information"
kaizoku_btn = "Kaizoku ☠️"
kayo_btn = "Kayo 🏴‍☠️"
prequel_btn = "Prequel ⬅️"
sequel_btn = "Sequel ➡️"
close_btn = "Close ❌"

def getKitsu(mal):
    # get kitsu id from mal id
    link = f'https://kitsu.io/api/edge/mappings?filter[external_site]=myanimelist/anime&filter[external_id]={mal}'
    result = requests.get(link).json()['data'][0]['id']
    link = f'https://kitsu.io/api/edge/mappings/{result}/item?fields[anime]=slug'
    kitsu = requests.get(link).json()['data']['id']
    return(kitsu)

def getPosterLink(mal):
    # grab poster from kitsu
    kitsu = getKitsu(mal)
    image = requests.get(f'https://kitsu.io/api/edge/anime/{kitsu}').json()
    return(image['data']['attributes']['posterImage']['original'])

def getBannerLink(mal):
    # try getting kitsu backdrop
    kitsu = getKitsu(mal)
    image = f'http://media.kitsu.io/anime/cover_images/{kitsu}/original.jpg'
    response = requests.get(image)
    if response.status_code == 200: return(image)
    # try getting anilist banner
    query = '''
    query ($idMal: Int){
        Media(idMal: $idMal){
            bannerImage
        }
    }
    '''
    image = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'idMal': int(mal)}}).json()['data']['Media']['bannerImage']
    if image: return(image)
    # use the poster from kitsu
    return(getPosterLink(mal))

def get_anime_manga(mal_id, search_type, user_id):

    jikan = jikanpy.jikan.Jikan()
    
    if search_type == "anime_anime":
        result = jikan.anime(mal_id)
        image = getBannerLink(mal_id)

        studio_string = ', '.join([studio_info['name'] for studio_info in result['studios']])
        producer_string = ', '.join([producer_info['name'] for producer_info in result['producers']])
    
    elif search_type == "anime_manga":
        result = jikan.manga(mal_id)
        image = result['image_url']

    caption = f"<a href=\'{result['url']}\'>{result['title']}</a>"

    if result['title_japanese']:
        caption += f" ({result['title_japanese']})\n"
    else:
        caption += "\n"

    alternative_names = []

    if result['title_english'] != None:
        alternative_names.append(result['title_english'])
    alternative_names.extend(result['title_synonyms'])

    if alternative_names:
        alternative_names_string = ", ".join(alternative_names)
        caption += f"\n<b>Also known as</b>: <code>{alternative_names_string}</code>"

    genre_string = ', '.join([genre_info['name'] for genre_info in result['genres']])
    
    if result['synopsis'] != None:
        synopsis = result['synopsis'].split(" ", 60)

        try:
            synopsis.pop(60)
        except IndexError:
            pass

        synopsis_string = ' '.join(synopsis) + "..."
    else:
        synopsis_string = "Unknown"

    for entity in result:
        if result[entity] == None:
            result[entity] = "Unknown"
    
    if search_type == "anime_anime":
        caption += textwrap.dedent(f"""
        <b>Type</b>: <code>{result['type']}</code>
        <b>Status</b>: <code>{result['status']}</code>
        <b>Aired</b>: <code>{result['aired']['string']}</code>
        <b>Episodes</b>: <code>{result['episodes']}</code>
        <b>Score</b>: <code>{result['score']}</code>
        <b>Premiered</b>: <code>{result['premiered']}</code>
        <b>Duration</b>: <code>{result['duration']}</code>
        <b>Genres</b>: <code>{genre_string}</code>
        <b>Studios</b>: <code>{studio_string}</code>
        <b>Producers</b>: <code>{producer_string}</code>

        📖 <b>Synopsis</b>: {synopsis_string} <a href='{result['url']}'>read more</a>

        <i>Search an encode on..</i>
        """)
    elif search_type == "anime_manga":
        caption += textwrap.dedent(f"""
        <b>Type</b>: <code>{result['type']}</code>
        <b>Status</b>: <code>{result['status']}</code>
        <b>Volumes</b>: <code>{result['volumes']}</code>
        <b>Chapters</b>: <code>{result['chapters']}</code>
        <b>Score</b>: <code>{result['score']}</code>
        <b>Genres</b>: <code>{genre_string}</code>

        📖 <b>Synopsis</b>: {synopsis_string}
        """)

    related = result['related']
    mal_url = result['url']
    prequel_id, sequel_id = None, None
    buttons, related_list = [], []

    if "Prequel" in related:
        prequel_id = related["Prequel"][0]["mal_id"]
    
    if "Sequel" in related:
        sequel_id = related["Sequel"][0]["mal_id"]

    if search_type == "anime_anime":
        kaizoku = f"https://animekaizoku.com/?s={result['title']}"
        kayo = f"https://animekayo.com/?s={result['title']}"

        buttons.append(
            [InlineKeyboardButton(kaizoku_btn, url=kaizoku), InlineKeyboardButton(kayo_btn, url=kayo)]
        )
    elif search_type == "anime_manga":
        buttons.append(
            [InlineKeyboardButton(info_btn, url=mal_url)]
        )

    if prequel_id:
        related_list.append(InlineKeyboardButton(prequel_btn, callback_data=f"{search_type}, {user_id}, {prequel_id}"))

    if sequel_id:
        related_list.append(InlineKeyboardButton(sequel_btn, callback_data=f"{search_type}, {user_id}, {sequel_id}"))

    if related_list:
        buttons.append(related_list)

    buttons.append([InlineKeyboardButton(close_btn, callback_data=f"anime_close, {user_id}")])
    
    return caption, buttons, image

@run_async
def anime(bot: Bot, update: Update):
    
    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    try:
        search_query = args[1]
    except:
        update.effective_message.reply_text("Format : /anime <animename>")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")

    jikan = jikanpy.jikan.Jikan()

    search_result = jikan.search("anime", search_query)
    first_mal_id = search_result["results"][0]["mal_id"]

    caption, buttons, image = get_anime_manga(first_mal_id, "anime_anime", message.from_user.id)

    update.effective_message.reply_photo(photo=image, caption=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=False)
    progress_message.delete()

@run_async
def manga(bot: Bot, update: Update):

    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    try:
        search_query = args[1]
    except:
        update.effective_message.reply_text("Format : /manga <manganame>")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")

    jikan = jikanpy.jikan.Jikan()

    search_result = jikan.search("manga", search_query)
    first_mal_id = search_result["results"][0]["mal_id"]

    caption, buttons, image = get_anime_manga(first_mal_id, "anime_manga", message.from_user.id)
    
    update.effective_message.reply_photo(photo=image, caption=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=False)
    progress_message.delete()

@run_async
def character(bot: Bot, update: Update):

    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    try:
        search_query = args[1]
    except:
        update.effective_message.reply_text("Format : /character <charactername>")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")
    jikan = jikanpy.jikan.Jikan()
    
    search_result = jikan.search("character", search_query)
    first_mal_id = search_result["results"][0]["mal_id"]
    
    character = jikan.character(first_mal_id)

    caption = f"[{character['name']}]({character['url']})"

    if character['name_kanji'] != "Japanese":
        caption += f" ({character['name_kanji']})\n"
    else:
        caption += "\n"

    if character['nicknames']:
        nicknames_string = ", ".join(character['nicknames'])
        caption += f"\n*Nicknames* : `{nicknames_string}`"

    about = character['about'].split(" ", 60)

    try:
        about.pop(60)
    except IndexError:
        pass

    about_string = ' '.join(about)

    for entity in character:
        if character[entity] == None:
            character[entity] = "Unknown"

    caption += f"\n*About*: {about_string}..."

    buttons = [
        [InlineKeyboardButton(info_btn, url=character['url'])],
        [InlineKeyboardButton(close_btn, callback_data=f"anime_close, {message.from_user.id}")]
    ]

    update.effective_message.reply_photo(photo=character['image_url'], caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=False)
    progress_message.delete()

@run_async
def user(bot: Bot, update: Update):

    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    try:
        search_query = args[1]
    except:
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

    try:
        user_birthday = datetime.datetime.fromisoformat(user['birthday'])
        user_birthday_formatted = user_birthday.strftime(date_format)
    except:
        user_birthday_formatted = "Unknown"

    user_joined_date = datetime.datetime.fromisoformat(user['joined'])
    user_joined_date_formatted = user_joined_date.strftime(date_format)

    for entity in user:
        if user[entity] == None:
            user[entity] = "Unknown"
    
    about = user['about'].split(" ", 60)

    try:
        about.pop(60)
    except IndexError:
        pass

    about_string = ' '.join(about)
    about_string = about_string.replace("<br>", "").strip().replace("\r\n", "\n")
    
    caption = ""

    caption += textwrap.dedent(f"""
    *Username*: [{user['username']}]({user['url']})

    *Gender*: `{user['gender']}`
    *Birthday*: `{user_birthday_formatted}`
    *Joined*: `{user_joined_date_formatted}`
    *Days wasted watching anime*: `{user['anime_stats']['days_watched']}`
    *Days wasted reading manga*: `{user['manga_stats']['days_read']}`

    """)

    caption += f"*About*: {about_string}...[ ]({user['image_url']})"

    buttons = [
        [InlineKeyboardButton(info_btn, url=user['url'])],
        [InlineKeyboardButton(close_btn, callback_data=f"anime_close, {message.from_user.id}")]
    ]

    update.effective_message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=False)
    progress_message.delete()
    
@run_async
def upcoming(bot: Bot, update: Update):

    jikan = jikanpy.jikan.Jikan()
    upcoming = jikan.top('anime', page=1, subtype="upcoming")

    upcoming_list = [entry['title'] for entry in upcoming['top']]
    upcoming_message = ""

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"{entry_num + 1}. {upcoming_list[entry_num]}\n"
        
    update.effective_message.reply_text(upcoming_message)

def button(bot, update):

    query = update.callback_query
    message = query.message
    data = query.data.split(", ")
    query_type = data[0]
    original_user_id = int(data[1])

    user_and_admin_list = [original_user_id, OWNER_ID] + SUDO_USERS + DEV_USERS
    
    if query_type == "anime_close":
        if query.from_user.id in user_and_admin_list:
            message.delete()
        else:
            query.answer("You are not allowed to use this.")
    elif query_type == "anime_anime" or query_type == "anime_manga":
        mal_id = data[2]
        if query.from_user.id == original_user_id:
            message.delete()
            progress_message = bot.sendMessage(message.chat.id, "Searching.... ")
            caption, buttons, image = get_anime_manga(mal_id, query_type, original_user_id)
            bot.sendPhoto(message.chat.id, photo=image, caption=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=False)
            progress_message.delete()
        else:
            query.answer("You are not allowed to use this.")

__help__ = """
Get information about anime, manga or characters from [MyAnimeList](https://myanimelist.net).

*Available commands:*

 - /anime <anime>: returns information about the anime.

 - /character <character>: returns information about the character.

 - /manga <manga>: returns information about the manga.

 - /user <user>: returns information about a MyAnimeList user.

 - /upcoming: returns a list of new anime in the upcoming seasons.

 """

__mod_name__ = "MyAnimeList"
__command_list__ = ["anime", "manga", "character", "user", "upcoming"]

ANIME_HANDLER = DisableAbleCommandHandler("anime", anime)
CHARACTER_HANDLER = DisableAbleCommandHandler("character", character)
MANGA_HANDLER = DisableAbleCommandHandler("manga", manga)
USER_HANDLER = DisableAbleCommandHandler("user", user)
UPCOMING_HANDLER = DisableAbleCommandHandler("upcoming", upcoming)

dispatcher.add_handler(CallbackQueryHandler(button, pattern='anime_.*'))
dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(CHARACTER_HANDLER)
dispatcher.add_handler(MANGA_HANDLER)
dispatcher.add_handler(USER_HANDLER)
dispatcher.add_handler(UPCOMING_HANDLER)
