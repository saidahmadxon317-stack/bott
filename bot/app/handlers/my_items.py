"""
My Listings Handler for Ulashamiz Telegram Bot
"""
from aiogram import Router, F, types
from app.database.client import DBService
from app.keyboards.inline import get_owner_listing_keyboard

router = Router()

@router.message(F.text == "📦 Mening e'lonlarim")
async def show_my_listings(message: types.Message):
    user = message.from_user
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    items = await DBService.get_user_listings(profile["id"])
    if not items:
        await message.answer(
            "📦 Sizda hozircha hech qanday e'lon yo'q.\n\n"
            "Yangi bepul buyum ulashish uchun <b>\"🎁 Bepul buyum berish\"</b> tugmasini bosing!",
            parse_mode="HTML"
        )
        return

    await message.answer(f"📦 <b>Sizning e'lonlaringiz ({len(items)} ta):</b>", parse_mode="HTML")

    status_labels = {
        "approved": "🟢 Faol",
        "pending": "🟡 Tekshiruvda",
        "given_away": "🎁 Olib ketildi",
        "rejected": "🔴 Rad etilgan"
    }

    for item in items:
        item_id = item.get("id")
        title = item.get("title")
        status = item.get("status", "approved")
        status_text = status_labels.get(status, "Noma'lum")
        is_given = status == "given_away"

        text = (
            f"📌 <b>{title}</b>\n"
            f"Holati: {status_text}\n"
            f"Ko'rishlar soni: {item.get('view_count', 0)}"
        )
        kb = get_owner_listing_keyboard(item_id, is_given_away=is_given)
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("mark_given:"))
async def mark_given_away(call: types.CallbackQuery):
    listing_id = call.data.split(":")[1]
    user = call.from_user
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    success = await DBService.mark_listing_given_away(listing_id, profile["id"])
    if success:
        await call.message.edit_text("🎉 E'lon \"Olib ketildi\" deb belgilandi! Ezgu amalingiz uchun tashakkur!")
    else:
        await call.answer("O'zgartirib bo'lmadi.", show_alert=True)
    await call.answer()

@router.callback_query(F.data.startswith("delete_listing:"))
async def delete_user_listing(call: types.CallbackQuery):
    listing_id = call.data.split(":")[1]
    user = call.from_user
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    success = await DBService.delete_listing(listing_id, profile["id"])
    if success:
        await call.message.edit_text("🗑 E'lon muvaffaqiyatli o'chirildi.")
    else:
        await call.answer("O'chirib bo'lmadi.", show_alert=True)
    await call.answer()

@router.callback_query(F.data.startswith("edit_listing:"))
async def edit_user_listing(call: types.CallbackQuery):
    listing_id = call.data.split(":")[1]
    from app.config import settings
    web_edit_url = f"{settings.WEB_URL}/items/{listing_id}/edit"
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Saytda tahrirlash", url=web_edit_url)],
        [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="delete_edit_msg")]
    ])
    await call.message.answer(
        f"✏️ <b>E'lonni tahrirlash:</b>\n\n"
        f"E'lon ma'lumotlarini (nomi, tavsifi, holati, hududi yoki aloqa uchun Telegram username'ini) o'zgartirish uchun quyidagi tugmani bosing:\n\n"
        f"🔗 <a href=\"{web_edit_url}\">Tahrirlash sahifasiga o'tish</a>",
        reply_markup=kb,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await call.answer()

@router.callback_query(F.data == "delete_edit_msg")
async def delete_edit_msg(call: types.CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer()
