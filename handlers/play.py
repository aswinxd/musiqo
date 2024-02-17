from os import path
from typing import Callable, Coroutine, Dict, List, Tuple, Union

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.errors import UserAlreadyParticipant
from youtube_search import YoutubeSearch

from callsmusic import callsmusic, queues
from config import BOT_NAME as bn, DURATION_LIMIT
from converter import convert
from helpers.admins import get_administrators
from helpers.decorators import errors, authorized_users_only
from helpers.filters import command, other_filters
from helpers.gets import get_file_name, get_url
from downloader.youtube import download

chat_id = None


def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        else:
            await cb.answer("You ain't allowed!", show_alert=True)
            return

    return decorator


# transcoder


def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw", format='s16le', acodec='pcm_s16le', ac=2, ar='48k').overwrite_output().run()
    os.remove(filename)


# Convert seconds to mm:ss

def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds

def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(':'))))


# Change image size

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    image1 = Image.open("./background.png")
    image2 = Image.open("image/Musiqo.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("image/font.otf", 32)
    draw.text((205, 550), f"Song title:- {title}", (51, 215, 255), font=font)
    draw.text(
        (205, 590), f"Song duration:- {duration}", (255, 255, 255), font=font
    )
    draw.text((205, 630), f"Song views:- {views}", (255, 255, 255), font=font)
    draw.text((205, 670),
              f"Playing for:- {requested_by}",
              (255, 255, 255),
              font=font,
              )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(
    filters.command("playlist")
    & filters.group
    & ~filters.edited
)
async def playlist(client, message):
    global que
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text('Player is idle')
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style='md')
    msg = "**Now playing** in {}".format(message.chat.title)
    msg += "\n- " + now_playing
    msg += "\n- Requested by " + by
    temp.pop(0)
    if temp:
        msg += '\n\n'
        msg += 'playlist'
        for song in temp:
            name = song[0]
            usr = song[1].mention(style='md')
            msg += f'\n- {name}'
            msg += f'\n- Requested by {usr}\n'
    await message.reply_text(msg)


# SETTINGS---------------- read before editing

def updated_stats(chat, queue, vol=100):
    if chat.id in callsmusic.pytgcalls.active_calls:
        # if chat.id in active_chats:
        stats = 'Settings of **{}**'.format(chat.title)
        if len(que) > 0:
            stats += '\n\n'
            stats += 'Volume : {}%\n'.format(vol)
            stats += 'Songs in playlist : `{}`\n'.format(len(que))
            stats += 'now playing : **{}**\n'.format(queue[0][0])
            stats += 'requested by : {}'.format(queue[0][1].mention)
    else:
        stats = None
    return stats


def r_ply(type_):
    if type_ == 'play':
        ico = 'play'
    else:
        ico = 'play'
    mar = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('⏺️', 'Leave'),
                InlineKeyboardButton('⏸️', 'Pause'),
                InlineKeyboardButton('▶️', 'Resume'),
                InlineKeyboardButton('⏩', 'Skip')
            ],
            [
                InlineKeyboardButton('Playlist', 'playlist')
            ],
            [
                InlineKeyboardButton("Close Menu", 'cls')
            ]
        ]
    )
    return mar


@Client.on_message(
    filters.command("current")
    & filters.group
    & ~filters.edited
)
async def ee(client, message):
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        await message.reply(stats)
    else:
        await message.reply('No VC instances running in this chat')


@Client.on_message(
    filters.command("player")
    & filters.group
    & ~filters.edited
)
@authorized_users_only
async def settings(client, message):
    playing = None
    if message.chat.id in callsmusic.pytgcalls.active_calls:
        playing = True
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        if playing:
            await message.reply(stats, reply_markup=r_ply('pause'))
        else:
            await message.reply(stats, reply_markup=r_ply('play'))
    else:
        await message.reply('No VC instances running in this chat')


@Client.on_callback_query(filters.regex(pattern=r'^(playlist)$'))
async def p_cb(b, cb):
    global que
    qeue = que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    chat_id = cb.message.chat.id
    m_chat = cb.message.chat
    the_data = cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == 'playlist':
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit('Player is idle')
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style='md')
        msg = "Now playing in {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- requested " + by
        temp.pop(0)
        if temp:
            msg += '\n\n'
            msg += 'queue'
            for song in temp:
                name = song[0]
                usr = song[1].mention(style='md')
                msg += f'\n- {name}'
                msg += f'\n- requested by {usr}\n'
        await cb.message.edit(msg)


@Client.on_callback_query(filters.regex(pattern=r'^(play|pause|skip|leave|puse|resume|menu|cls)$'))
@cb_admin_check
async def m_cb(b, cb):
    global que
    qeue = que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    chat_id = cb.message.chat.id
    m_chat = cb.message.chat
    the_data = cb.message.reply_markup.inline_keyboard[1][0].callback_data

    if type_ == 'pause':
        if (chat_id not in callsmusic.pytgcalls.active_calls) or (callsmusic.pytgcalls.active_calls[chat_id] == 'paused'):
            await cb.answer('Chat is not connected!', show_alert=True)
        else:
            callsmusic.pytgcalls.pause_stream(chat_id)
            await cb.answer('Music Paused!')
            await cb.message.edit(updated_stats(m_chat, qeue), reply_markup=r_ply('play'))

    elif type_ == 'play':
        if (chat_id not in callsmusic.pytgcalls.active_calls) or (callsmusic.pytgcalls.active_calls[chat_id] == 'playing'):
            await cb.answer('Chat is not connected!', show_alert=True)
        else:
            callsmusic.pytgcalls.resume_stream(chat_id)
            await cb.answer('Music Resumed!')
            await cb.message.edit(updated_stats(m_chat, qeue), reply_markup=r_ply('pause'))

    elif type_ == 'playlist':
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit('Player is idle')
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style='md')
        msg = "Now playing in {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- requested " + by
        temp.pop(0)
        if temp:
            msg += '\n\n'
            msg += 'queue'
            for song in temp:
                name = song[0]
                usr = song[1].mention(style='md')
                msg += f'\n- {name}'
                msg += f'\n- requested by {usr}\n'
        await cb.message.edit(msg)

    elif type_ == 'skip':
        if (chat_id not in callsmusic.pytgcalls.active_calls) or (callsmusic.pytgcalls.active_calls[chat_id] == 'paused'):
            await cb.answer('Chat is not connected!', show_alert=True)
        else:
            callsmusic.pytgcalls.skip_current_playing(chat_id)
            await cb.answer('Skipped the song!')
            await cb.message.edit(updated_stats(m_chat, qeue))

    elif type_ == 'leave':
        if chat_id in callsmusic.pytgcalls.active_calls:
            try:
                queues.clear(chat_id)
                callsmusic.pytgcalls.leave_group_call(chat_id)
                await cb.message.delete()
            except:
                pass
        else:
            await cb.answer('Chat is not connected!', show_alert=True)

    elif type_ == 'menu':
        await cb.answer('Closing Menu...', show_alert=True)
        await cb.message.delete()

    elif type_ == 'cls':
        await cb.answer('Closing Menu...', show_alert=True)
        await cb.message.delete()


@Client.on_message(
    filters.command("help")
    & filters.group
    & ~filters.edited
)
async def help(client, message):
    buttons = [
        [
            InlineKeyboardButton('Commands 🛠', callback_data='cmds'),
            InlineKeyboardButton('Settings ⚙️', callback_data='set')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text(
        "Hey, I'm Music Player. "
        "I can play music in your group's voice chat. "
        "Click the buttons below to get more info.",
        reply_markup=reply_markup
    )


@Client.on_callback_query(filters.regex(pattern=r'^(cmds|set)$'))
async def help_cb(b, cb):
    data = cb.matches[0].group(1)
    if data == 'cmds':
        buttons = [
            [
                InlineKeyboardButton('Close 🔒', callback_data='cls')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await cb.message.edit(
            "Here are the available commands:\n"
            "/play - reply to an audio file or youtube url to play it or use /play <query>.\n"
            "/pause - pause the playback.\n"
            "/resume - resume the playback.\n"
            "/skip - skip the current playback.\n"
            "/stop - stop the playback and leave the voice chat.\n"
            "/joinvc - join the voice chat.\n"
            "/leavevc - leave the voice chat.\n"
            "/player - show the current playback status.\n"
            "/playlist - show the current playlist.\n"
            "/volume - set the volume level (0-200%).\n"
            "/restart - restart the bot (admins only).\n"
            "/ping - check the bot's ping.\n"
            "/uptime - check the bot's uptime.\n"
            "/help - show this message.\n"
            "You can also control the playback using the buttons below.",
            reply_markup=reply_markup
        )
    elif data == 'set':
        buttons = [
            [
                InlineKeyboardButton('Close 🔒', callback_data='cls')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await cb.message.edit(
            "Here are the available settings:\n"
            "You can change these settings using the buttons below.",
            reply_markup=reply_markup
        )
    elif data == 'cls':
        await cb.message.delete()


@Client.on_message(
    command("play")
    & other_filters
)
async def play(_, message: Message):
    global que
    lel = await message.reply("Processing...")

    sender_id = message.from_user.id
    sender_name = message.from_user.first_name

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("channel", url="https://t.me/musiqo/62")
            ]
        ]
    )

    if message.chat.id not in que:
        que[message.chat.id] = []

    if message.reply_to_message:
        if message.reply_to_message.audio or message.reply_to_message.video:
            file = message.reply_to_message.audio or message.reply_to_message.video
            file_name = get_file_name(file)
            await message.reply_to_message.download(
                f"downloads/{message.chat.id}/{file_name}"
            )
            await lel.edit("Download complete, Processing...")
            await convert(
                f"downloads/{message.chat.id}/{file_name}",
                f"downloads/{message.chat.id}/{file_name}.raw",
            )
            file_name = f"downloads/{message.chat.id}/{file_name}.raw"
            await callsmusic.pytgcalls.join_group_call(
                message.chat.id, file_name
            )
            await lel.edit(f"Started Playing: {file_name}")
            return

    try:
        query = message.text.split(None, 1)[1]
    except IndexError:
        await lel.edit("Please give a youtube url or query to search.")
        return

    if not query:
        await lel.edit("Please give a youtube url or query to search.")
        return

    await lel.edit("Downloading...")

    try:
        url = get_url(query)
    except Exception as e:
        await lel.edit(
            f"Error: {e}\n\nPlease provide the correct YouTube URL or Query."
        )
        return

    await lel.edit("Processing...")

    file_name = await download(url)
    if not file_name:
        await lel.edit("No audio found.")
        return

    await lel.edit("Transcoding...")

    file_path = path.join("downloads", f"{message.chat.id}", file_name)
    thumb = await get_youtube_thumbnail(url)

    await lel.edit("Starting Streaming...")

    try:
        transcode(file_path)
    except Exception as e:
        await lel.edit(f"Error: {e}")
        return

    if message.chat.id in callsmusic.pytgcalls.active_calls:
        queue = que.get(message.chat.id)
        queue.append((file_name, message.from_user))
        que[message.chat.id] = queue
        await lel.edit("Queued! Now in Queue.\nUse /playlist to see the queue.")
    else:
        await callsmusic.pytgcalls.join_group_call(
            message.chat.id, f"downloads/{message.chat.id}/{file_name}.raw"
        )
        queue = que.get(message.chat.id)
        queue.append((file_name, message.from_user))
        que[message.chat.id] = queue
        await lel.edit(
            f"Playing...",
            reply_markup=keyboard,
        )

        await generate_cover(
            sender_name,
            title,
            views,
            duration,
            thumbnail,
        )


@Client.on_message(
    filters.command("volume")
    & filters.group
    & ~filters.edited
)
async def volume(_, message: Message):
    try:
        vol = int(message.text.split(None, 1)[1])
        if (vol < 0) or (vol > 200):
            await message.reply("Volume range must be 0-200!")
            return
    except IndexError:
        await message.reply("You forgot to specify the volume!")
        return
    except ValueError:
        await message.reply("Volume must be an integer!")
        return

    chat_id = message.chat.id
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply("Not connected to voice chat!")
        return

    try:
        callsmusic.pytgcalls.change_volume(chat_id, vol)
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
        return

    await message.reply_text(f"Volume set to {vol}%")


@Client.on_message(
    filters.command("pause")
    & filters.group
    & ~filters.edited
)
async def pause(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply("Not connected to voice chat!")
        return

    if callsmusic.pytgcalls.active_calls[chat_id] == "paused":
        await message.reply("Already paused!")
        return

    try:
        callsmusic.pytgcalls.pause_stream(chat_id)
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
        return

    await message.reply_text("Playback paused!")


@Client.on_message(
    filters.command("resume")
    & filters.group
    & ~filters.edited
)
async def resume(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply("Not connected to voice chat!")
        return

    if callsmusic.pytgcalls.active_calls[chat_id] == "playing":
        await message.reply("Already playing!")
        return

    try:
        callsmusic.pytgcalls.resume_stream(chat_id)
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
        return

    await message.reply_text("Playback resumed!")


@Client.on_message(
    filters.command("skip")
    & filters.group
    & ~filters.edited
)
async def skip(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply("Not connected to voice chat!")
        return

    try:
        callsmusic.pytgcalls.skip_current_playing(chat_id)
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
        return

    await message.reply_text("Skipped the current song!")


@Client.on_message(
    filters.command("stop")
    & filters.group
    & ~filters.edited
)
async def stop(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply("Not connected to voice chat!")
        return

    try:
        queues.clear(chat_id)
        callsmusic.pytgcalls.leave_group_call(chat_id)
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
        return

    await message.reply_text("Playback stopped and left the voice chat!")


@Client.on_message(
    filters.command("joinvc")
    & filters.group
    & ~filters.edited
)
async def join_vc(_, message: Message):
    chat_id = message.chat.id
    try:
        await callsmusic.pytgcalls.join_group_call(chat_id)
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
        return

    await message.reply_text("Joined the voice chat!")


@Client.on_message(
    filters.command("leavevc")
    & filters.group
    & ~filters.edited
)
async def leave_vc(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in callsmusic.pytgcalls.active_calls:
        await message.reply("Not connected to voice chat!")
        return

    try:
        queues.clear(chat_id)
        callsmusic.pytgcalls.leave_group_call(chat_id)
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
        return

    await message.reply_text("Left the voice chat!")


@Client.on_message(
    filters.command("restart")
    & filters.user(OWNER_ID)
    & ~filters.edited
)
async def restart(_, message: Message):
    await message.reply_text("Restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)


@Client.on_message(
    filters.command("ping")
    & filters.group
    & ~filters.edited
)
async def ping(_, message: Message):
    start = time.time()
    m_reply = await message.reply_text("Pinging...")
    delta_ping = time.time() - start
    await m_reply.edit_text(
        "Pong!\n" f"⏳ `{delta_ping * 1000:.3f} ms`"
    )


@Client.on_message(
    filters.command("uptime")
    & filters.group
    & ~filters.edited
)
async def uptime(_, message: Message):
    uptime_seconds = time.time() - START_TIME
    uptime = convert_seconds(uptime_seconds)
    await message.reply_text(
        f"Uptime: {uptime}"
    )


@Client.on_message(
    filters.command("leave")
    & filters.private
    & ~filters.edited
)
async def leave_private(_, message: Message):
    await message.reply_text("You can't make me leave from here.\nUse /help to know more.")


@Client.on_message(
    filters.command("join")
    & filters.private
    & ~filters.edited
)
async def join_group(_, message: Message):
    invite_link = await app.export_chat_invite_link(int(message.text.split()[1]))
    await app.send_message(message.chat.id, f"Join the group {invite_link} to use the bot")


@Client.on_message(
    filters.command("chatid")
    & filters.private
    & ~filters.edited
)
async def chat_id(_, message: Message):
    await message.reply_text(
        f"Chat ID: <code>{message.chat.id}</code>",
        parse_mode="html",
    )


@Client.on_message(
    filters.command("id")
    & filters.private
    & ~filters.edited
)
async def user_id(_, message: Message):
    await message.reply_text(
        f"Your ID: <code>{message.from_user.id}</code>",
        parse_mode="html",
    )
