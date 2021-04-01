import os, glob, json

from telegram import Bot, Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext, run_async
from AstrakoBot import dispatcher
from AstrakoBot.modules.disable import DisableAbleCommandHandler
from youtubesearchpython import SearchVideos

from youtube_dl import YoutubeDL


def youtube(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    yt = message.text[len("/youtube ") :]
    if yt:
        search = SearchVideos(yt, offset=1, mode="json", max_results=1)
        test = search.result()
        
        try:
            p = json.loads(test)
        except:
            return message.reply_text(
                "Failed to find song or video", 
                parse_mode = ParseMode.MARKDOWN
            )
        
        q = p.get("search_result")
        url = q[0]["link"]
        title = q[0]["title"]

        buttons = [
            [
                InlineKeyboardButton("Song", callback_data=f"youtube;audio;{url}"),
                InlineKeyboardButton("Video", callback_data=f"youtube;video;{url}"),
            ]
        ]

        msg = "*Preparing to upload file:*\n"
        msg += f"`{title}`\n"
        message.reply_text(
            msg, 
            parse_mode=ParseMode.MARKDOWN,            
            reply_markup = InlineKeyboardMarkup(buttons)
        )
    else:
        message.reply_text("Specify a song or video"
        )


def youtube_callback(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    query = update.callback_query

    media = query.data.split(";")
    media_type = media[1]
    media_url = media[2]
    
    if media_type == "audio":    
        opts = {
        "format": "bestaudio/best",
        "addmetadata": True,
        "key": "FFmpegMetadata",
        "writethumbnail": True,
        "prefer_ffmpeg": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": "%(id)s.mp3",
        "quiet": True,
        "logtostderr": False,
        }
        
        codec = "mp3"

        with YoutubeDL(opts) as rip:
            rip_data = rip.extract_info(media_url)
            
            try:
                message.reply_audio(
                audio = open(f"{rip_data['id']}.{codec}", "rb"),
                duration = int(rip_data['duration']),
                title = str(rip_data['title']),
                parse_mode = ParseMode.HTML)
            except:
                message.reply_text(
                    "Song is too large for processing, or any other error happened. Try again later"
                )

    else:
        opts = {
        "format": "best",
        "addmetadata": True,
        "key": "FFmpegMetadata",
        "prefer_ffmpeg": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        "outtmpl": "%(id)s.mp4",
        "logtostderr": False,
        "quiet": True,
        }

        codec = "mp4"

        with YoutubeDL(opts) as rip:
            rip_data = rip.extract_info(media_url)
            
            try:
                message.reply_video(
                video = open(f"{rip_data['id']}.{codec}", "rb"),
                duration = int(rip_data['duration']),
                caption = rip_data['title'],
                supports_streaming = True,
                parse_mode = ParseMode.HTML)
            except:
                message.reply_text(
                    "Video is too large for processing, or any other error happened. Try again later"
                )

    try:
        for f in glob.glob("*.mp*"):
            os.remove(f)
    except Exception:
        pass



YOUTUBE_HANDLER = DisableAbleCommandHandler(["youtube", "yt"], youtube, run_async = True)
YOUTUBE_CALLBACKHANDLER = CallbackQueryHandler(
    youtube_callback, pattern="youtube*", run_async=True
)
dispatcher.add_handler(YOUTUBE_HANDLER)
dispatcher.add_handler(YOUTUBE_CALLBACKHANDLER)

__handlers__ = [YOUTUBE_HANDLER, YOUTUBE_CALLBACKHANDLER]
