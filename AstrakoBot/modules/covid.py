from datetime import datetime
from covid import Covid
from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, CommandHandler
from telegram.ext import CallbackContext, run_async
from AstrakoBot import dispatcher
from AstrakoBot.modules.helper_funcs.misc import delete


def covid(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    country = message.text[len("/covid ") :]
    covid = Covid()
    
    if country:
        try:
            country_data = covid.get_status_by_country_name(country)
        except:
            return message.reply_text("Wrong country name!")
        
        msg = f"*Corona Virus Info*\n\n"
        msg += f"• Country: `{country}`\n"
        msg += f"• Confirmed: `{country_data['confirmed']}`\n"
        msg += f"• Active: `{country_data['active']}`\n"
        msg += f"• Deaths: `{country_data['deaths']}`\n"
        msg += f"• Recovered: `{country_data['recovered']}`\n"
        msg += (
            "Last update: "
            f"`{datetime.utcfromtimestamp(country_data['last_update'] // 1000).strftime('%Y-%m-%d %H:%M:%S')}`\n"
        )
        msg += f"__Data provided by__ [Johns Hopkins University](https://j.mp/2xf6oxF)"
            
    else:
        msg = "Please specify a country"

    delmsg = message.reply_text(
        text=msg,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

    context.dispatcher.run_async(delete, delmsg, 60)


covid_handler = CommandHandler(["covid"], covid, run_async=True)
dispatcher.add_handler(covid_handler)


__command_list__ = ["covid"]
__handlers__ = [covid_handler]
