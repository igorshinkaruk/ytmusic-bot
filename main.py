import yt_dlp
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("images/background.jpg", "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="🎵 Привіт! Напиши назву треку або посилання з YouTube Music, щоб отримати аудіо."
            )
    except FileNotFoundError:
        await update.message.reply_text("🎵 Привіт! Напиши назву треку або посилання з YouTube Music, щоб отримати аудіо.")

async def search_youtube_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        await update.message.reply_text("❌ Вкажи запит або посилання.")
        return

    await update.message.reply_text("⏳ Шукаю і завантажую аудіо з YouTube Music...")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "keepvideo": False,
        "quiet": True,
        "max_filesize": 1000 * 1024 * 1024,
        "user_agent": "Mozilla/5.0",
    }

    try:
        if not query.startswith("http"):
            query = f"ytsearch1:{query}"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(query, download=True)

            entries = info_dict["entries"] if "entries" in info_dict and info_dict["entries"] else [info_dict]

            for entry in entries:
                file_path = None
                if "requested_downloads" in entry:
                    file_path = entry["requested_downloads"][0]["filepath"]
                elif "filepath" in entry:
                    file_path = entry["filepath"]
                elif "_filename" in entry:
                    file_path = str(Path(entry["_filename"]).with_suffix(".mp3"))

                if file_path and Path(file_path).exists():
                    if Path(file_path).stat().st_size > 50 * 1024 * 1024:
                        yt_url = entry.get("webpage_url", "")
                        await update.message.reply_text(
                            f"❌ Файл занадто великий для Telegram (>50 МБ).\n🔗 {yt_url}",
                            disable_web_page_preview=True
                        )
                        Path(file_path).unlink(missing_ok=True)
                        continue

                    with open(file_path, "rb") as audio_file:
                        await update.message.reply_audio(
                            audio=audio_file,
                            title=entry.get("title", "Audio"),
                            performer=entry.get("uploader", None)
                        )
                    Path(file_path).unlink(missing_ok=True)
                else:
                    await update.message.reply_text("❌ Не вдалося знайти аудіофайл.")

    except Exception as e:
        await update.message.reply_text("❌ Сталася помилка при завантаженні.")
        print(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_youtube_music))
    app.run_polling()

if __name__ == "__main__":
    main()
