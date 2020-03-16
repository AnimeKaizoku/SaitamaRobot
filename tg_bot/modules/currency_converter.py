import requests
from telegram import Bot, Update
from telegram.ext import CommandHandler, run_async

from tg_bot import dispatcher, CASH_API_KEY


@run_async
def convert(bot: Bot, update: Update):
    args = update.effective_message.text.split(" ", 3)
    if len(args) > 1:

        orig_cur_amount = float(args[1])

        try:
            orig_cur = args[2].upper()
        except IndexError:
            update.effective_message.reply_text("You forgot to mention the currency code.")
            return

        try:
            new_cur = args[3].upper()
        except IndexError:
            update.effective_message.reply_text("You forgot to mention the currency code to convert into.")
            return

        request_url = (f"https://www.alphavantage.co/query"
                       f"?function=CURRENCY_EXCHANGE_RATE"
                       f"&from_currency={orig_cur}"
                       f"&to_currency={new_cur}"
                       f"&apikey={CASH_API_KEY}")
        response = requests.get(request_url).json()
        try:
            current_rate = float(response['Realtime Currency Exchange Rate']['5. Exchange Rate'])
        except KeyError:
            update.effective_message.reply_text(f"Currency Not Supported.")
            return
        new_cur_amount = round(orig_cur_amount * current_rate, 5)
        update.effective_message.reply_text(f"{orig_cur_amount} {orig_cur} = {new_cur_amount} {new_cur}")
    else:
        update.effective_message.reply_text(__help__)


__help__ = """
 - /cash : currency converter
 example syntax: /cash 1 USD INR
"""

CONVERTER_HANDLER = CommandHandler('cash', convert)

dispatcher.add_handler(CONVERTER_HANDLER)

__mod_name__ = "Currency Converter"
__command_list__ = ["cash"]
__handlers__ = [CONVERTER_HANDLER]
