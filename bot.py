import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import ReactionTypeEmoji, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import sheets
from extractor import extract_movie_links, fetch_og_title

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.text:
        return

    links = extract_movie_links(message.text)
    if not links:
        return

    added_any = False
    for link in links:
        title = await fetch_og_title(link)
        added_by = message.from_user.full_name if message.from_user else "Unknown"
        if sheets.add_film(link, title, added_by):
            added_any = True

    if added_any:
        try:
            await message.set_reaction([ReactionTypeEmoji(emoji="👀")])
        except Exception:
            pass


async def handle_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.dice:
        return

    current = sheets.get_current_film()
    if current:
        await message.reply_text(
            f"Сначала посмотрите текущий фильм:\n\n"
            f"🎬 <b>{current['title']}</b>\n{current['link']}\n\n"
            f"После просмотра напишите /watched",
            parse_mode="HTML",
        )
        return

    unwatched = sheets.get_unwatched_films()
    if not unwatched:
        await message.reply_text("Список пуст! Скидывайте ссылки на фильмы.")
        return

    dice_value = message.dice.value  # 1–6
    film = unwatched[(dice_value - 1) % len(unwatched)]
    sheets.set_current_film(film["row"])

    await asyncio.sleep(3)  # ждём анимацию кубика
    await message.reply_text(
        f"🎬 Смотрим:\n\n"
        f"<b>{film['title']}</b>\n{film['link']}\n\n"
        f"Добавил: {film['added_by']}",
        parse_mode="HTML",
    )


async def handle_watched(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    film = sheets.mark_watched()
    if film:
        await update.message.reply_text(
            f"✅ Посмотрели!\n\n<b>{film['title']}</b>\n\nМожно бросать кубик 🎲",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("Нет текущего фильма.")


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("watched", handle_watched))
    app.add_handler(MessageHandler(filters.Dice.DICE, handle_dice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
