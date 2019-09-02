from currency_converter import CurrencyConverter
import requests

from datetime import datetime

from telegram import Update, Bot
from telegram.ext import CommandHandler

from tg_bot import dispatcher

def convert(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 3)
    if len(args) > 1:
        orig_cur = float(args[1])

        try:
            orig_rate = args[2].upper()
        except IndexError:
            update.effective_message.reply_text("You forgot to mention the currency code")
            return 

        try:
            new_rate = args[3].upper()
        except IndexError:
            update.effective_message.reply_text("You forgot to mention the currency code to convert into")
            return

    request_url = "https://api.exchangeratesapi.io/latest?base={}".format(orig_rate)
    current_response = requests.get(request_url).json()
    if new_rate in current_response["rates"]:
                current_rate = float(current_response["rates"][new_rate])
                new_cur = round(orig_cur * current_rate, 5)
    update.effective_message.reply_text("{} {} = {} {}".format(orig_cur, orig_rate, new_cur, new_rate))


__help__ = """
 - /cash : currency converter
 example syntax: /cash 1 USD INR
"""

__mod_name__ = "Currency Converter"


CONVERTER_HANDLER = CommandHandler('cash', convert)

dispatcher.add_handler(CONVERTER_HANDLER)
