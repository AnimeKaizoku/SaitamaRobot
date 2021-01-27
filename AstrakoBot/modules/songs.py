# Thanks to @p_rinc_e
from pathlib import Path
import asyncio, time, io, math, os, glob, logging, asyncio, shutil, re, subprocess, json
from re import findall
from asyncio import sleep
from telethon.events import NewMessage
from telethon.tl.custom import Dialog
from datetime import datetime as dt
from pytz import country_names as c_n, country_timezones as c_tz, timezone as tz
from hachoir.parser import createParser
import pybase64
from base64 import b64decode
from pySmartDL import SmartDL
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio
from telethon import events

from AstrakoBot import dispatcher
from AstrakoBot import telethn
from AstrakoBot.modules.disable import DisableAbleCommandHandler
from AstrakoBot.utils import progress
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.messages import ImportChatInviteRequest as Get
from validators.url import url
from html import unescape
from urllib.error import HTTPError
import bs4
from bs4 import BeautifulSoup
from youtube_dl import YoutubeDL
from youtubesearchpython import SearchVideos
from youtube_dl.utils import (DownloadError, ContentTooShortError,
                              ExtractorError, GeoRestrictedError,
                              MaxDownloadsReached, PostProcessingError,
                              UnavailableVideoError, XAttrMetadataError)


async def process(v_url, dtype, opts):
    lazy = v_url ; sender = await lazy.get_sender() ; me = await lazy.client.get_me()
    if not sender.id == me.id:
        rkp = await lazy.reply("`processing...`")
    else:
    	rkp = await lazy.edit("`processing...`")   
    url = v_url.pattern_match.group(1)
    if not url:
         return await rkp.edit("`Error \nusage song <song name>`")
    search = SearchVideos(url, offset = 1, mode = "json", max_results = 1)
    test = search.result()
    p = json.loads(test)
    q = p.get('search_result')
    try:
       url = q[0]['link']
    except:
    	return await rkp.edit("`failed to find`")
    type = "audio"
    await rkp.edit("`Preparing to download...`")
  
    try:
        await rkp.edit("`Fetching data, please wait..`")
        with YoutubeDL(opts) as rip:
            rip_data = rip.extract_info(url)
    except DownloadError as DE:
        await rkp.edit(f"`{str(DE)}`")
        return
    except ContentTooShortError:
        await rkp.edit("`The download content was too short.`")
        return
    except GeoRestrictedError:
        await rkp.edit(
            "`Video is not available from your geographic location due to geographic restrictions imposed by a website.`"
        )
        return
    except MaxDownloadsReached:
        await rkp.edit("`Max-downloads limit has been reached.`")
        return
    except PostProcessingError:
        await rkp.edit("`There was an error during post processing.`")
        return
    except UnavailableVideoError:
        await rkp.edit("`Media is not available in the requested format.`")
        return
    except XAttrMetadataError as XAME:
        await rkp.edit(f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
        return
    except ExtractorError:
        await rkp.edit("`There was an error during info extraction.`")
        return
    except Exception as e:
        await rkp.edit(f"{str(type(e)): {str(e)}}")
        return
    c_time = time.time()

    if dtype == "song":

        if int(rip_data["duration"] / 60) > 30:
            await rkp.edit("`Song is too long for processing.`")
            return

        await rkp.edit(f"`Preparing to upload song:`\
        \n**{rip_data['title']}**\
        \nby *{rip_data['uploader']}*")
        await v_url.client.send_file(
            v_url.chat_id,
            f"{rip_data['id']}.mp3",
            supports_streaming=True,
            attributes=[
                DocumentAttributeAudio(duration=int(rip_data['duration']),
                                       title=str(rip_data['title']),
                                       performer=str(rip_data['uploader']))
            ],
            progress_callback=lambda d, t: asyncio.get_event_loop(
            ).create_task(
                progress(d, t, v_url, c_time, "Uploading..",
                         f"{rip_data['title']}.mp3")))

    else:

        if int(rip_data["duration"] / 60) > 10:
            await rkp.edit("`Video is too long for processing.`")
            return

        await rkp.edit(f"`Preparing to upload video:`\
        \n**{rip_data['title']}**\
        \nby *{rip_data['uploader']}*")
        await v_url.client.send_file(
            v_url.chat_id,
            f"{rip_data['id']}.mp4",
            supports_streaming=True,
            caption=url,
            progress_callback=lambda d, t: asyncio.get_event_loop(
            ).create_task(
                progress(d, t, v_url, c_time, "Uploading..",
                         f"{rip_data['title']}.mp4")))


@telethn.on(events.NewMessage(pattern="^[!/]song(.*)"))
async def song(v_url):
    opts = {
    'format':
    'bestaudio',
    'addmetadata':
    True,
    'key':
    'FFmpegMetadata',
    'writethumbnail':
    True,
    'prefer_ffmpeg':
    True,
    'geo_bypass':
    True,
    'nocheckcertificate':
    True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
    'outtmpl':
    '%(id)s.mp3',
    'quiet':
    True,
    'logtostderr':
    False
    }
    await process(v_url, "song", opts)

    try:
        for f in glob.glob("*.mp*"):
            os.remove(f)
    except Exception:
        pass

@telethn.on(events.NewMessage(pattern="^[!/]video(.*)"))
async def video(v_url):
    opts = {
    'format':
    'best',
    'addmetadata':
    True,
    'key':
    'FFmpegMetadata',
    'prefer_ffmpeg':
    True,
    'geo_bypass':
    True,
    'nocheckcertificate':
    True,
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4'
    }],
    'outtmpl':
    '%(id)s.mp4',
    'logtostderr':
    False,
    'quiet':
    True
    }
    await process(v_url, "video", opts)

    try:
        for f in glob.glob("*.mp*"):
            os.remove(f)
    except Exception:
        pass


SONG_HANDLER = DisableAbleCommandHandler('song', song)
VIDEO_HANDLER = DisableAbleCommandHandler('video', video)

dispatcher.add_handler(SONG_HANDLER)
dispatcher.add_handler(VIDEO_HANDLER)

__handlers__ = [
    SONG_HANDLER,
    VIDEO_HANDLER
]

