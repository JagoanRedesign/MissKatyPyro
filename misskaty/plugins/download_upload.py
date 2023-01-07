import time
import asyncio
import math
import os
from misskaty.helper.http import http
from logging import getLogger
from misskaty import app
from pySmartDL import SmartDL
from datetime import datetime
from misskaty.core.decorator.errors import capture_err
from misskaty.vars import COMMAND_HANDLER, SUDO
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from misskaty.helper.pyro_progress import (
    progress_for_pyrogram,
    humanbytes,
)

LOGGER = getLogger(__name__)

__MODULE__ = "Download/Upload"
__HELP__ = """
/download [url] - Download file from URL (Sudo Only)
/download [reply_to_TG_File] - Download TG File
/tiktokdl [link] - Download TikTok Video
/fbdl [link] - Download Facebook Video
/anon [link] - Upload files to Anonfiles
/ytdown [link] - Download YouTube dengan link
"""


@app.on_message(filters.command(["anon"], COMMAND_HANDLER))
async def upload(bot, message):
    if not message.reply_to_message:
        return await message.reply("Please reply to media file.")
    if message.reply_to_message is not None:
        vid = [message.reply_to_message.video, message.reply_to_message.document]
        for v in vid:
            if v is not None:
                break
    m = await message.reply("Download your file to my Server...")
    now = time.time()
    fileku = await message.reply_to_message.download(
        progress=progress_for_pyrogram,
        progress_args=("Trying to download, please wait..", m, now),
    )
    try:
        files = {"file": open(fileku, "rb")}
        await m.edit("Uploading to Anonfile, Please Wait||")
        callapi = await http.post("https://api.anonfiles.com/upload", files=files)
        text = callapi.json()
        output = f'<u>File Uploaded to Anonfile</u>\n\n📂 File Name: {text["data"]["file"]["metadata"]["name"]}\n\n📦 File Size: {text["data"]["file"]["metadata"]["size"]["readable"]}\n\n📥 Download Link: {text["data"]["file"]["url"]["full"]}'

        btn = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download 📥", url=f"{text['data']['file']['url']['full']}")]])
        await m.edit(output, reply_markup=btn)
    except Exception as e:
        await bot.send_message(message.chat.id, text=f"Something Went Wrong!\n\n{e}")
    os.remove(sed)


@app.on_message(filters.command(["download"], COMMAND_HANDLER) & filters.user(SUDO))
@capture_err
async def download(client, message):
    pesan = await message.reply_text("Processing...", quote=True)
    if message.reply_to_message is not None:
        start_t = datetime.now()
        c_time = time.time()
        the_real_download_location = await client.download_media(
            message=message.reply_to_message,
            progress=progress_for_pyrogram,
            progress_args=("trying to download, sabar yakk..", pesan, c_time),
        )
        end_t = datetime.now()
        ms = (end_t - start_t).seconds
        await pesan.edit(f"Downloaded to <code>{the_real_download_location}</code> in <u>{ms}</u> seconds.")
    elif len(message.command) > 1:
        start_t = datetime.now()
        the_url_parts = " ".join(message.command[1:])
        url = the_url_parts.strip()
        custom_file_name = os.path.basename(url)
        if "|" in the_url_parts:
            url, custom_file_name = the_url_parts.split("|")
            url = url.strip()
            custom_file_name = custom_file_name.strip()
        download_file_path = os.path.join("downloads/", custom_file_name)
        downloader = SmartDL(url, download_file_path, progress_bar=False)
        downloader.start(blocking=False)
        c_time = time.time()
        while not downloader.isFinished():
            total_length = downloader.filesize or None
            downloaded = downloader.get_dl_size()
            display_message = ""
            now = time.time()
            diff = now - c_time
            percentage = downloader.get_progress() * 100
            speed = downloader.get_speed()
            round(diff) * 1000
            progress_str = "[{0}{1}]\nProgress: {2}%".format(
                "".join(["█" for _ in range(math.floor(percentage / 5))]),
                "".join(["░" for _ in range(20 - math.floor(percentage / 5))]),
                round(percentage, 2),
            )

            estimated_total_time = downloader.get_eta(human=True)
            try:
                current_message = "trying to download...\n"
                current_message += f"URL: <code>{url}</code>\n"
                current_message += f"File Name: <code>{custom_file_name}</code>\n"
                current_message += f"Speed: {speed}\n"
                current_message += f"{progress_str}\n"
                current_message += f"{humanbytes(downloaded)} of {humanbytes(total_length)}\n"
                current_message += f"ETA: {estimated_total_time}"
                if round(diff % 10.00) == 0 and current_message != display_message:
                    await pesan.edit(disable_web_page_preview=True, text=current_message)
                    display_message = current_message
                    await asyncio.sleep(10)
            except Exception as e:
                LOGGER.info(str(e))
        if os.path.exists(download_file_path):
            end_t = datetime.now()
            ms = (end_t - start_t).seconds
            await pesan.edit(f"Downloaded to <code>{download_file_path}</code> in {ms} seconds")
    else:
        await pesan.edit("Reply to a Telegram Media, to download it to my local server.")


@app.on_message(filters.command(["tiktokdl"], COMMAND_HANDLER))
@capture_err
async def tiktokdl(client, message):
    if len(message.command) == 1:
        return await message.reply(f"Use command /{message.command[0]} [link] to download tiktok video.")
    link = message.command[1]
    msg = await message.reply("Trying download...")
    try:
        r = (await http.get(f"https://api.hayo.my.id/api/tiktok/4?url={link}")).json()
        await message.reply_video(
            r["linkori"],
            caption=f"<b>Title:</b> <code>{r['name']}</code>\n\nUploaded for {message.from_user.mention} [<code>{message.from_user.id}</code>]",
        )
        await msg.delete()
    except Exception as e:
        await message.reply(f"Failed to download tiktok video..\n\n<b>Reason:</b> {e}")
        await msg.delete()


@app.on_message(filters.command(["fbdl"], COMMAND_HANDLER))
@capture_err
async def fbdl(client, message):
    if len(message.command) == 1:
        return await message.reply(f"Use command /{message.command[0]} [link] to download Facebook video.")
    link = message.command[1]
    msg = await message.reply("Trying download...")
    try:
        resjson = (await http.get(f"https://yasirapi.eu.org/fbdl?link={link}")).json()
        try:
            url = resjson["result"]["links"]["hd"].replace("&amp;", "&")
        except:
            url = resjson["result"]["links"]["sd"].replace("&amp;", "&")
        obj = SmartDL(url, progress_bar=False)
        obj.start()
        path = obj.get_dest()
        await message.reply_video(
            path,
            caption=f"<code>{os.path.basename(path)}</code>\n\nUploaded for {message.from_user.mention} [<code>{message.from_user.id}</code>]",
        )
        await msg.delete()
        try:
            os.remove(path)
        except:
            pass
    except Exception as e:
        await message.reply(f"Failed to download Facebook video..\n\n<b>Reason:</b> {e}")
        await msg.delete()
