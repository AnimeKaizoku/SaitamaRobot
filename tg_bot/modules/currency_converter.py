from currency_converter import CurrencyConverter

from telegram import Update, Bot
from telegram.ext import CommandHandler

from tg_bot import dispatcher

def convert(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 3)
    if len(args) > 1:
        orig_cur = args[1]
        
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

    c = CurrencyConverter('http://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip')
    new_cur = c.convert(orig_cur, orig_rate, new_rate)
    new_cur = float("{0:.2f}".format(new_cur))
    update.effective_message.reply_text("{} {} = {} {}".format(orig_cur, orig_rate, new_cur, new_rate))


__help__ = """
 - /cash : currency converter
 example syntax: /cash 1 USD INR
"""

__mod_name__ = "Currency Converter"


CONVERTER_HANDLER = CommandHandler('cash', convert)

dispatcher.add_handler(CONVERTER_HANDLER)
