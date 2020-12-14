from AstrakoBot.modules.disable import DisableAbleCommandHandler
from AstrakoBot import dispatcher

from telegram.ext import CallbackContext, Filters, CommandHandler

__help__ = """
*Available commands:*\n
*Image reverse:*
 • `/reverse`: does a *reverse image search* of the media which it was replied to\n
*Text to speech:*
 • `/tts <text>`: convert text to speech\n
*Songs:*
 • `/song <songname artist(optional)>`: uploads the song in it's best quality available
 • `/video <songname artist(optional)>`: uploads the video song in it's best quality available\n
"""

__mod_name__ = "Media"
__command_list__ = ["reverse", "tts", "song", "video"]
