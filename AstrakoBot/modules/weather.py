import json
from datetime import datetime

from pytz import country_timezones as c_tz, timezone as tz, country_names as c_n
from requests import get
from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, CommandHandler
from telegram.ext import CallbackContext, run_async
from AstrakoBot import WEATHER_API, dispatcher


@run_async
def get_tz(con):
    for c_code in c_n:
        if con == c_n[c_code]:
            return tz(c_tz[c_code][0])
    try:
        if c_n[con]:
            return tz(c_tz[con][0])
    except KeyError:
        return


@run_async
def weather(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    city = message.text[len("/weather ") :]
    if city:
        APPID = WEATHER_API
        result = None
        timezone_countries = {
            timezone: country
            for country, timezones in c_tz.items()
            for timezone in timezones
        }
        if "," in city:
            newcity = city.split(",")
            if len(newcity[1]) == 2:
                city = newcity[0].strip() + "," + newcity[1].strip()
            else:
                country = get_tz((newcity[1].strip()).title())
                try:
                    countrycode = timezone_countries[f"{country}"]
                except KeyError:
                    weather.edit("`Invalid country.`")
                    return
                city = newcity[0].strip() + "," + countrycode.strip()
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={APPID}"
        request = get(url)
        result = json.loads(request.text)
        if request.status_code != 200:
            info = f"No weather information for this location!"
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=info,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
            return

        cityname = result["name"]
        curtemp = result["main"]["temp"]
        humidity = result["main"]["humidity"]
        min_temp = result["main"]["temp_min"]
        max_temp = result["main"]["temp_max"]
        country = result["sys"]["country"]
        sunrise = result["sys"]["sunrise"]
        sunset = result["sys"]["sunset"]
        wind = result["wind"]["speed"]
        weath = result["weather"][0]
        desc = weath["main"]
        icon = weath["id"]
        condmain = weath["main"]
        conddet = weath["description"]

        if icon <= 232:  # Rain storm
            icon = "⛈"
        elif icon <= 321:  # Drizzle
            icon = "🌧"
        elif icon <= 504:  # Light rain
            icon = "🌦"
        elif icon <= 531:  # Cloudy rain
            icon = "⛈"
        elif icon <= 622:  # Snow
            icon = "❄️"
        elif icon <= 781:  # Atmosphere
            icon = "🌪"
        elif icon <= 800:  # Bright
            icon = "☀️"
        elif icon <= 801:  # A little cloudy
            icon = "⛅️"
        elif icon <= 804:  # Cloudy
            icon = "☁️"

        ctimezone = tz(c_tz[country][0])
        time = (
            datetime.now(ctimezone)
            .strftime("%A %d %b, %H:%M")
            .lstrip("0")
            .replace(" 0", " ")
        )
        fullc_n = c_n[f"{country}"]
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

        kmph = str(wind * 3.6).split(".")
        mph = str(wind * 2.237).split(".")

        def fahrenheit(f):
            temp = str(((f - 273.15) * 9 / 5 + 32)).split(".")
            return temp[0]

        def celsius(c):
            temp = str((c - 273.15)).split(".")
            return temp[0]

        def sun(unix):
            xx = (
                datetime.fromtimestamp(unix, tz=ctimezone)
                .strftime("%H:%M")
                .lstrip("0")
                .replace(" 0", " ")
            )
            return xx

        if city:
            info = f"*{cityname}, {fullc_n}*\n"
            info += f"`{time}`\n\n"
            info += f"• **Temperature:** `{celsius(curtemp)}°C\n`"
            info += f"• **Condition:** `{condmain}, {conddet}` " + f"{icon}\n"
            info += f"• **Humidity:** `{humidity}%`\n"
            info += f"• **Wind:** `{kmph[0]} km/h`\n"
            info += f"• **Sunrise**: `{sun(sunrise)}`\n"
            info += f"• **Sunset**: `{sun(sunset)}`"
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=info,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )


WEATHER_HANDLER = CommandHandler(["weather"], weather)
dispatcher.add_handler(WEATHER_HANDLER)


__command_list__ = ["weather"]
__handlers__ = [WEATHER_HANDLER]
