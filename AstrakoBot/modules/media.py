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
 • `/song <songname artist(optional)>`: uploads the song as mp3
 • `/video <songname artist(optional)>`: uploads the video song in sd quality (480p) as mp4 \n
"""

__mod_name__ = "Media"
__command_list__ = ["reverse", "tts", "song", "video"]
