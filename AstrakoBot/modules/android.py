# Magisk Module- Module from AstrakoBot
# Inspired from RaphaelGang's android.py
# By DAvinash97

import time
from bs4 import BeautifulSoup
from requests import get
from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, CommandHandler
from telegram.ext import CallbackContext, run_async
from ujson import loads
from AstrakoBot import dispatcher
from AstrakoBot.modules.github import getphh


def magisk(update: Update, context: CallbackContext):
    link = "https://raw.githubusercontent.com/topjohnwu/magisk_files/"
    bot = context.bot
    magisk_dict = {
        "*Stable*": "master/stable.json",
        "\n" "*Canary*": "canary/canary.json",
    }.items()
    releases = "*Latest Magisk Releases:*\n\n"
    for magisk_type, release_url in magisk_dict:
        if "Canary" in magisk_type:
            canary = "https://github.com/topjohnwu/magisk_files/raw/canary/"
        else:
            canary = ""
        data = get(link + release_url).json()
        releases += (
            f"{magisk_type}:\n"
            f'• Manager - [{data["app"]["version"]} ({data["app"]["versionCode"]})]({canary + data["app"]["link"]}) \n'
            f'• Uninstaller - [Uninstaller {data["magisk"]["version"]} ({data["magisk"]["versionCode"]})]({canary + data["uninstaller"]["link"]}) \n'
        )
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=releases,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


def checkfw(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if not len(args) == 2:
        reply = f'Give me something to fetch, like:\n`/checkfw SM-N975F DBT`'
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
            return
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                    err.message == "Message can't be deleted"):
                return
    temp, csc = args
    model = f'sm-' + temp if not temp.upper().startswith('SM-') else temp
    fota = get(
        f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml'
    )
    if fota.status_code != 200:
        reply = f"Couldn't check for {temp.upper()} and {csc.upper()}, please refine your search or try again later!"
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                    err.message == "Message can't be deleted"):
                return
    page = BeautifulSoup(fota.content, 'lxml')
    os = page.find("latest").get("o")
    if page.find("latest").text.strip():
        reply = f'*Latest released firmware for {model.upper()} and {csc.upper()} is:*\n'
        pda, csc, phone = page.find("latest").text.strip().split('/')
        reply += f'• PDA: `{pda}`\n• CSC: `{csc}`\n'
        if phone:
            reply += f'• Phone: `{phone}`\n'
        if os:
            reply += f'• Android: `{os}`\n'
        reply += f''
    else:
        reply = f'*No public release found for {model.upper()} and {csc.upper()}.*\n\n'
    update.message.reply_text("{}".format(reply),
                              parse_mode=ParseMode.MARKDOWN,
                              disable_web_page_preview=True)


def getfw(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if not len(args) == 2:
        reply = f'Give me something to fetch, like:\n`/getfw SM-N975F DBT`'
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
            return
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                    err.message == "Message can't be deleted"):
                return
    temp, csc = args
    model = f'sm-' + temp if not temp.upper().startswith('SM-') else temp
    test = get(
        f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.test.xml'
    )
    if test.status_code != 200:
        reply = f"Couldn't find any firmware downloads for {temp.upper()} and {csc.upper()}, please refine your search or try again later!"
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                    err.message == "Message can't be deleted"):
                return
    url1 = f'https://samfrew.com/model/{model.upper()}/region/{csc.upper()}/'
    url2 = f'https://www.sammobile.com/samsung/firmware/{model.upper()}/{csc.upper()}/'
    url3 = f'https://sfirmware.com/samsung-{model.lower()}/#tab=firmwares'
    url4 = f'https://samfw.com/firmware/{model.upper()}/{csc.upper()}/'
    fota = get(
        f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml'
    )
    page = BeautifulSoup(fota.content, 'lxml')
    os = page.find("latest").get("o")
    reply = ""
    if page.find("latest").text.strip():
        pda, csc2, phone = page.find("latest").text.strip().split('/')
        reply += f'*Latest firmware for {model.upper()} and {csc.upper()} is:*\n'
        reply += f'• PDA: `{pda}`\n• CSC: `{csc2}`\n'
        if phone:
            reply += f'• Phone: `{phone}`\n'
        if os:
            reply += f'• Android: `{os}`\n'
    reply += f'\n'
    reply += f'*Downloads for {model.upper()} and {csc.upper()}*\n'
    reply += f'• [samfrew.com]({url1})\n'
    reply += f'• [sammobile.com]({url2})\n'
    reply += f'• [sfirmware.com]({url3})\n'
    reply += f'• [samfw.com]({url4})\n'
    update.message.reply_text("{}".format(reply),
                              parse_mode=ParseMode.MARKDOWN,
                              disable_web_page_preview=True)


def phh(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    index = int(args[0]) if len(args) > 0 and args[0].isdigit() else 0
    text = getphh(index)
    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    return


def orangefox(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    device = message.text[len("/orangefox ") :]

    if device:
        link = get(f"https://api.orangefox.download/v3/releases/?codename={device}&sort=date_desc&limit=1")

        if link.status_code == 404:
            message = f"OrangeFox currently is not avaliable for {device}"
        else:
            page = loads(link.content)
            file_id = page["data"][0]["_id"]
            link = get(f"https://api.orangefox.download/v3/devices/get?codename={device}")
            page = loads(link.content)
            oem = page["oem_name"]
            model = page["model_name"]
            full_name = page["full_name"]
            link = get(f"https://api.orangefox.download/v3/releases/get?_id={file_id}")
            page = loads(link.content)
            dl_file = page["filename"]
            build_type = page["type"]
            version = page["version"]
            changelog = page["changelog"][0]
            size = page["size"]
            dl_link = page["mirrors"]["DL"]
            date = page["date"]
            md5 = page["md5"]
            message = f"<b>Latest OrangeFox Recovery for the {full_name}</b>\n\n"
            message += f"• Manufacturer: {oem}\n"
            message += f"• Model: {model}\n"
            message += f"• Codename: {device}\n"
            message += f"• Release type: official\n"
            message += f"• Build type: {build_type}\n"
            message += f"• Version: {version}\n"
            message += f"• Changelog: {changelog}\n"
            message += f"• Size: {size}\n"
            message += f"• Date: {date}\n"
            message += f"• File: {dl_file}\n"
            message += f"• MD5: {md5}\n\n"
            message += f"• <b>Download:</b> {dl_link}\n"        

    else:
        message = "Please specify a device codename"


    bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


def twrp(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    device = message.text[len("/twrp ") :]

    if device:
        link = get(f"https://eu.dl.twrp.me/{device}")

        if link.status_code == 404:
            message = f"TWRP currently is not avaliable for {device}"
        else:
            page = BeautifulSoup(link.content, "lxml")
            download = page.find("table").find("tr").find("a")
            dl_link = f"https://eu.dl.twrp.me{download['href']}"
            dl_file = download.text
            size = page.find("span", {"class": "filesize"}).text
            date = page.find("em").text.strip()
            message = f"<b>Latest TWRP for the {device}</b>\n\n"
            message += f"• Release type: official\n"
            message += f"• Size: {size}\n"
            message += f"• Date: {date}\n"
            message += f"• File: {dl_file}\n\n"
            message += f"• <b>Download:</b> {dl_link}\n"
    else:
        message = "Please specify a device codename"


    bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


__help__ = """
*Available commands:*\n
*Magisk:* 
• `/magisk`, `/su`, `/root`: fetches latest magisk\n
*OrangeFox Recovery Project:* 
• `/orangefox` `<devicecodename>`: fetches lastest OrangeFox Recovery available for a given device codename\n
*TWRP:* 
• `/twrp <devicecodename>`: fetches lastest TWRP available for a given device codename\n
*Phh:* 
• `/phh`: get lastest phh builds from github\n
*Samsung:*
• `/checkfw <model> <csc>` - Samsung only - shows the latest firmware info for the given device, taken from samsung servers
• `/getfw <model> <csc>` - Samsung only - gets firmware download links from samfrew, sammobile and sfirmwares for the given device
"""
magisk_handler = CommandHandler(["magisk", "root", "su"], magisk, run_async=True)
orangefox_handler = CommandHandler("orangefox", orangefox, run_async=True)
twrp_handler = CommandHandler("twrp", twrp, run_async=True)
GETFW_HANDLER = CommandHandler("getfw", getfw, run_async=True)
CHECKFW_HANDLER = CommandHandler("checkfw", checkfw, run_async=True)
PHH_HANDLER = CommandHandler("phh", phh, run_async=True)

dispatcher.add_handler(magisk_handler)
dispatcher.add_handler(orangefox_handler)
dispatcher.add_handler(twrp_handler)
dispatcher.add_handler(GETFW_HANDLER)
dispatcher.add_handler(CHECKFW_HANDLER)
dispatcher.add_handler(PHH_HANDLER)

__mod_name__ = "Android"
__command_list__ = ["magisk", "root", "su", "orangefox", "twrp", "phh"]
__handlers__ = [magisk_handler, orangefox_handler, twrp_handler, GETFW_HANDLER, CHECKFW_HANDLER, PHH_HANDLER]
