import yt_dlp
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, InlineQueryHandler, CallbackQueryHandler
import uuid
import os

BOT_TOKEN = os.environ['BOT_TOKEN']

def inline_query(update, context):
    query = update.inline_query.query
    if not query:
        return

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'simulate': True,
        'extract_flat': 'in_playlist',
        'cookiefile': 'cookies.txt'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch5:{query}", download=False)

    articles = []
    for entry in search_results.get("entries", []):
        title = entry.get("title")
        video_id = entry.get("id")
        url = f"https://www.youtube.com/watch?v={video_id}"
        keyboard = [
            [InlineKeyboardButton("144p", callback_data=f"download:144:{url}"),
             InlineKeyboardButton("360p", callback_data=f"download:360:{url}"),
             InlineKeyboardButton("480p", callback_data=f"download:480:{url}")],
            [InlineKeyboardButton("MP3", callback_data=f"download:audio:{url}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        articles.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=title,
                input_message_content=InputTextMessageContent(f"Video: {title}\n{url}"),
                description=entry.get("description"),
                thumb_url=entry.get("thumbnail"),
                reply_markup=reply_markup
            )
        )

    update.inline_query.answer(articles)

def button_handler(update, context):
    query = update.callback_query
    query.answer()

    try:
        data = query.data.split(":")
        if data[0] == "download":
            quality = data[1]
            video_url = ':'.join(data[2:])

            query.edit_message_text(f"Starting download in {quality}...")

            if quality == "audio":
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': '%(title)s.%(ext)s',
                    'quiet': True,
                    'cookiefile': 'cookies.txt',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                }
            else:
                ydl_opts = {
                    'format': f'best[height<={quality}]/best',
                    'outtmpl': '%(title)s - %(height)sp.%(ext)s',
                    'quiet': True,
                    'cookiefile': 'cookies.txt'
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)

            if quality == "audio":
                audio_file = filename.rsplit(".", 1)[0] + ".mp3"
                context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=open(audio_file, 'rb'),
                    title=info['title']
                )
                os.remove(audio_file)
            else:
                context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=open(filename, 'rb'),
                    caption=f"{info['title']} - {quality}p"
                )
                os.remove(filename)

            query.edit_message_text("Download completed!")
    except Exception as e:
        query.edit_message_text(f"Error during download: {str(e)}")

def main():
    from keep_alive import keep_alive
    keep_alive()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(InlineQueryHandler(inline_query))
    dp.add_handler(CallbackQueryHandler(button_handler, pattern="^download"))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
