import subprocess
import time
import os
import requests
import speedtest
import json
import sys
import traceback
import psutil
import platform
import AstrakoBot.modules.helper_funcs.git_api as git

from datetime import datetime
from platform import python_version, uname
from telethon import version
from telegram import Update, Bot, Message, Chat, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.error import BadRequest, Unauthorized

from AstrakoBot import DEV_USERS, LOGGER, StartTime, dispatcher
from AstrakoBot.modules.disable import DisableAbleCommandHandler, DisableAbleRegexHandler
from AstrakoBot.modules.helper_funcs.misc import delete
from AstrakoBot.modules.helper_funcs.chat_status import owner_plus, dev_plus, sudo_plus


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


def convert(speed):
    return round(int(speed) / 1048576, 2)


@owner_plus
def shell(update: Update, context: CallbackContext):
    message = update.effective_message
    cmd = message.text.split(" ", 1)
    if len(cmd) == 1:
        message.reply_text("No command to execute was given.")
        return
    cmd = cmd[1]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    stdout, stderr = process.communicate()
    msg = ""
    stderr = stderr.decode()
    stdout = stdout.decode()
    if stdout:
        msg += f"*Stdout*\n`{stdout}`\n"
        LOGGER.info(f"Shell - {cmd} - {stdout}")
    if stderr:
        msg += f"*Stderr*\n`{stderr}`\n"
        LOGGER.error(f"Shell - {cmd} - {stderr}")
    if len(msg) > 3000:
        with open("shell_output.txt", "w") as file:
            file.write(msg)
        with open("shell_output.txt", "rb") as doc:
            delmsg = message.reply_document(
                document = doc,
                filename = doc.name,
                reply_to_message_id = message.message_id,
            )
    else:

        delmsg = message.reply_text(
            text = msg,
            parse_mode = ParseMode.MARKDOWN,
            disable_web_page_preview = True,
        )

    context.dispatcher.run_async(delete, delmsg, 120)


@dev_plus
def status(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    query = update.callback_query

    msg = "*Bot information*\n"
    msg += f"Python version: `{python_version()}`\n"
    msg += f"Telethon version: `{version.__version__}`\n"
    msg += f"GitHub API version: `{str(git.vercheck())}`\n"
    uptime = get_readable_time((time.time() - StartTime))
    msg += f"Uptime: `{uptime}`\n\n"
    uname = platform.uname()
    msg += "*System information*\n"
    msg += f"OS: `{uname.system}`\n"
    msg += f"Version: `{uname.version}`\n"
    msg += f"Release: `{uname.release}`\n"
    msg += f"Processor: `{uname.processor}`\n"
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    msg += f"Boot time: `{bt.day}/{bt.month}/{bt.year} - {bt.hour}:{bt.minute}:{bt.second}`\n"
    msg += f"CPU cores: `{psutil.cpu_count(logical=False)} physical, {psutil.cpu_count()} logical`\n"
    msg += f"CPU freq: `{psutil.cpu_freq().current:.2f}Mhz`\n"
    msg += f"CPU usage: `{psutil.cpu_percent()}%`\n"
    ram = psutil.virtual_memory()
    msg += f"RAM: `{get_size(ram.total)} - {get_size(ram.used)} used ({ram.percent}%)`\n"
    disk = psutil.disk_usage('/')
    msg += f"Disk usage: `{get_size(disk.total)} total - {get_size(disk.used)} used ({disk.percent}%)`\n"
    swap = psutil.swap_memory()
    msg += f"SWAP: `{get_size(swap.total)} - {get_size(swap.used)} used ({swap.percent}%)`\n"

    delmsg = message.reply_text(
        text = msg,
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    context.dispatcher.run_async(delete, delmsg, 120)


@owner_plus
def get_bot_ip(update: Update, context: CallbackContext):
    message = update.effective_message
    ip = requests.get("http://ipinfo.io/ip")

    delmsg = message.reply_text(
        text = f"*IP:* `{ip.text}`",
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    context.dispatcher.run_async(delete, delmsg, 60)


@sudo_plus
def ping(update: Update, context: CallbackContext):
    message = update.effective_message

    start_time = time.time()
    msg = message.reply_text("Pinging...")
    end_time = time.time()
    telegram_ping = str(round((end_time - start_time) * 1000, 3)) + " ms"
    uptime = get_readable_time((time.time() - StartTime))


    delmsg = msg.edit_text(
        "*PONG!!*\n"
        f"Time Taken: `{telegram_ping}`\n"
        f"Service uptime: `{uptime}`",
        parse_mode=ParseMode.MARKDOWN,
    )

    context.dispatcher.run_async(delete, delmsg, 30)


@dev_plus
def speedtestxyz(update: Update, context: CallbackContext):
    buttons = [
        [
            InlineKeyboardButton("Image", callback_data="speedtest_image"),
            InlineKeyboardButton("Text", callback_data="speedtest_text"),
        ]
    ]
    update.effective_message.reply_text(
        "Select SpeedTest Mode", reply_markup=InlineKeyboardMarkup(buttons)
    )


def speedtestxyz_callback(update: Update, context: CallbackContext):
    message = update.effective_message
    query = update.callback_query

    if query.from_user.id in DEV_USERS:
        delmsg = message.edit_text("Running a speedtest....")
        speed = speedtest.Speedtest()
        speed.get_best_server()
        speed.download()
        speed.upload()
        context.dispatcher.run_async(delete, delmsg, 30)
        msg = "*SpeedTest Results:*"

        if query.data == "speedtest_image":
            speedtest_image = speed.results.share()
            delmsg = message.reply_photo(
                photo=speedtest_image, 
                caption=msg,
                parse_mode = ParseMode.MARKDOWN,
            )

        elif query.data == "speedtest_text":
            result = speed.results.dict()
            msg += f"\nDownload: `{convert(result['download'])}Mb/s`\nUpload: `{convert(result['upload'])}Mb/s`\nPing: `{result['ping']}`"
            delmsg = message.reply_text(
                text = msg,
                parse_mode = ParseMode.MARKDOWN,
                disable_web_page_preview = True,
            )

        context.dispatcher.run_async(delete, delmsg, 60)

    else:
        query.answer("You are required to be a developer user to use this command.")

IP_HANDLER = DisableAbleCommandHandler("ip", get_bot_ip, run_async=True)
PING_HANDLER = DisableAbleCommandHandler("ping", ping, run_async=True)
SHELL_HANDLER = DisableAbleCommandHandler(["sh"], shell, run_async=True)
SPEED_TEST_CALLBACKHANDLER = CallbackQueryHandler(speedtestxyz_callback, pattern="speedtest_.*", run_async=True)
SPEED_TEST_HANDLER = DisableAbleCommandHandler("speedtest", speedtestxyz, run_async=True)
STATUS_HANDLER = DisableAbleCommandHandler("status", status, run_async=True)
  
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(SHELL_HANDLER)
dispatcher.add_handler(SPEED_TEST_CALLBACKHANDLER)
dispatcher.add_handler(SPEED_TEST_HANDLER)
dispatcher.add_handler(STATUS_HANDLER)

