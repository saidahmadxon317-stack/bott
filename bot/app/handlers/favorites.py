"""
Favorites Handler for Ulashamiz Telegram Bot
"""
from aiogram import Router, F, types
from app.database.client import DBService
from app.config import settings
from app.keyboards.inline import get_listing_card_keyboard

router = Router()

@router.message(F.text == "❤️ Saqlanganlar")
async def show_favorites(message: types.Message):
    user = message.from_user
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    items = await DBService.get_user_favorites(profile["id"])
    if not items:
        await message.answer(
            "❤️ Saqlangan buyumlar ro'yxati bo'sh.\n\n"
            "Buyum kartasidagi \"❤️ Saqlash\" tugmasini bosib, yoqqan buyumlarni saqlab qo'yishingiz mumkin."
        )
        return

    await message.answer(f"❤️ <b>Saqlangan buyumlaringiz ({len(items)} ta):</b>", parse_mode="HTML")

    for item in items:
        title = item.get("title", "")
        desc = item.get("description", "")
        if len(desc) > 150:
            desc = desc[:147] + "..."
        text = f"❤️ <b>{title}</b>\n\n{desc}\n💰 BEPUL"
        kb = get_listing_card_keyboard(item.get("id"), settings.WEB_URL, is_favorite=True)
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("fav_toggle:"))
async def toggle_favorite(call: types.CallbackQuery):
    listing_id = call.data.split(":")[1]
    user = call.from_user
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    is_added = await DBService.toggle_favorite(profile["id"], listing_id)
    if is_added:
        await call.answer("❤️ Saqlanganlarga qo'shildi!", show_alert=False)
    else:
        await call.answer("💔 Saqlanganlardan o'chirildi!", show_alert=False)
