# Magisk Module- Module from AstrakoBot
# Inspired from RaphaelGang's android.py
# By DAvinash97

from bs4 import BeautifulSoup
from requests import get
from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, CommandHandler
from telegram.ext import CallbackContext, run_async
from ujson import loads
from AstrakoBot import dispatcher

link = "https://raw.githubusercontent.com/topjohnwu/magisk_files/"


@run_async
def magisk(update: Update, context: CallbackContext):
    link = "https://raw.githubusercontent.com/topjohnwu/magisk_files/"
    bot = context.bot
    magisk_dict = {
            "*Stable*": "master/stable.json", "\n"
            "*Beta*": "master/beta.json", "\n"
            "*Canary*": "canary/canary.json",
        }.items()
    releases = '*Latest Magisk Releases:*\n\n'
    for magisk_type, release_url in magisk_dict:
        if "Canary" in magisk_type:
            canary = "https://github.com/topjohnwu/magisk_files/raw/canary/"
        else:
            canary = ""
        data = get(link + release_url).json()
        releases += f'{magisk_type}:\n' \
                    f'• Installer - [{data["magisk"]["version"]} ({data["magisk"]["versionCode"]})]({canary + data["magisk"]["link"]}) \n' \
                    f'• Manager - [{data["app"]["version"]} ({data["app"]["versionCode"]})]({canary + data["app"]["link"]}) \n' \
                    f'• Uninstaller - [Uninstaller {data["magisk"]["version"]} ({data["magisk"]["versionCode"]})]({canary + data["uninstaller"]["link"]}) \n'
    bot.send_message(chat_id = update.effective_chat.id,
                             text=releases,
                             parse_mode=ParseMode.MARKDOWN,
                             disable_web_page_preview=True)


@run_async
def orangefox(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    device = (args[0])
    link = get(f'https://api.orangefox.download/v2/device/{device}/releases/last')

    if link.status_code == 404:
        message = f"OrangeFox currently is not avaliable for {device}"

    else:
        page = loads(link.content)
        dl_file = page['file_name']
        build_type = page['build_type']
        version = page['version']
        changelog = page['changelog']
        size = page['size_human']
        dl_link = page['url']
        date = page['date']
        md5 = page['md5']
        message = f'<b>Latest OrangeFox Recovery for the {device}</b>\n\n'
        message += f'• Release type: official\n'
        message += f'• Build type: {build_type}\n'        
        message += f'• Version: {version}\n'
        message += f'• Changelog: {changelog}\n'
        message += f'• Size: {size}\n'
        message += f'• Date: {date}\n'
        message += f'• File: {dl_file}\n'
        message += f'• MD5: {md5}\n\n'
        message += f'• <b>Download:</b> {dl_link}\n'

    bot.send_message(chat_id = update.effective_chat.id,
                        text = message,
                        parse_mode = ParseMode.HTML,
                        disable_web_page_preview = True)


@run_async
def twrp(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    device = (args[0])
    link = get(f'https://eu.dl.twrp.me/{device}')

    if link.status_code == 404:
        message = f"TWRP currently is not avaliable for {device}"

    else:

        page = BeautifulSoup(link.content, 'lxml')
        download = page.find('table').find('tr').find('a')
        dl_link = f"https://eu.dl.twrp.me{download['href']}"
        dl_file = download.text
        size = page.find("span", {"class": "filesize"}).text
        date = page.find("em").text.strip()
        message = f'<b>Latest TWRP for the {device}</b>\n\n'
        message += f'• Release type: official\n'
        message += f'• Size: {size}\n'
        message += f'• Date: {date}\n'
        message += f'• File: {dl_file}\n\n'
        message += f'• <b>Download:</b> {dl_link}\n'
    
    bot.send_message(chat_id = update.effective_chat.id,

                        text = message,
                        parse_mode = ParseMode.HTML,
                        disable_web_page_preview = True)
                             
__help__ = """
*Available commands:*\n
*Magisk:* 
• `/magisk`, `/su`, `/root`: fetches latest magisk\n
*OrangeFox Recovery Project:* 
• `/ofox`, `/orangefox` `<devicecodename>`: fetches lastest OrangeFox Recovery available for a given device codename\n
*TWRP:* 
• `/twrp <devicecodename>`: fetches lastest TWRP available for a given device codename
"""
magisk_handler = CommandHandler(['magisk', 'root', 'su'], magisk)
orangefox_handler = CommandHandler(['ofox', 'orangefox'], orangefox)
twrp_handler = CommandHandler('twrp', twrp)

dispatcher.add_handler(magisk_handler)
dispatcher.add_handler(orangefox_handler)
dispatcher.add_handler(twrp_handler)

__mod_name__ = "Android"
__command_list__ = ["magisk", "root", "su", "ofox", "orangefox", "twrp"]
__handlers__ = [
    magisk_handler,
    orangefox_handler,
    twrp_handler
]
