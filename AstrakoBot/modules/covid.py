from datetime import datetime
from covid import Covid
from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, CommandHandler
from telegram.ext import CallbackContext, run_async
from AstrakoBot import dispatcher


@run_async
def covid(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    country = message.text[len("/covid ") :]
    covid = Covid()
    country_data = covid.get_status_by_country_name(country)
    if country_data:
        info = f"*Corona Virus Info*\n\n"
        info += f"• Country: `{country}`\n"
        info += f"• Confirmed: `{country_data['confirmed']}`\n"
        info += f"• Active: `{country_data['active']}`\n"
        info += f"• Deaths: `{country_data['deaths']}`\n"
        info += f"• Recovered: `{country_data['recovered']}`\n"
        info += (
            "Last update: "
            f"`{datetime.utcfromtimestamp(country_data['last_update'] // 1000).strftime('%Y-%m-%d %H:%M:%S')}`\n"
        )
        info += f"__Data provided by__ [Johns Hopkins University](https://j.mp/2xf6oxF)"
    else:
        info = f"No information yet about this country!"

    bot.send_message(
        chat_id=update.effective_chat.id,
        text=info,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


covid_handler = CommandHandler(["covid"], covid)
dispatcher.add_handler(covid_handler)


__command_list__ = ["covid"]
__handlers__ = [covid_handler]
