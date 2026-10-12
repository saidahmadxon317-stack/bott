"""
Profile and Account Linking Handler for Ulashamiz Telegram Bot
"""
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.client import DBService
from app.config import settings

router = Router()

@router.message(F.text == "👤 Profil")
async def show_profile(message: types.Message):
    user = message.from_user
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    listings = await DBService.get_user_listings(profile["id"])
    active_count = sum(1 for item in listings if item.get("status") == "approved")
    given_count = sum(1 for item in listings if item.get("status") == "given_away")

    text = (
        "👤 <b>Sizning profilingiz:</b>\n\n"
        f"📝 <b>Ism:</b> {profile.get('full_name') or user.full_name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"🔗 <b>Username:</b> @{user.username or 'mavjud emas'}\n\n"
        "📊 <b>Statistika:</b>\n"
        f"• Faol e'lonlar: {active_count} ta\n"
        f"• Bepul berilgan buyumlar: {given_count} ta\n\n"
        "🌐 <b>Sayt bilan bog'lash:</b>\n"
        "Veb-saytdagi profilingizga Telegram hisobingizni ulash uchun quyidagi tugmani bosing."
    )

    web_profile_url = f"{settings.WEB_URL}/profile" if "localhost" not in settings.WEB_URL else "https://beminnat.uz/profile"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 Saytga ulash kodini olish", callback_data="generate_link_token")],
        [InlineKeyboardButton(text="🌐 Veb-saytga o'tish", url=web_profile_url)]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "generate_link_token")
async def handle_generate_link_token(call: types.CallbackQuery):
    user = call.from_user
    token_code = await DBService.create_account_link_token(
        telegram_id=user.id,
        telegram_username=user.username
    )

    msg = (
        "🔐 <b>Hisobni ulash kodi:</b>\n\n"
        f"👉 <code>{token_code}</code> 👈\n\n"
        "⏳ Ushbu kod <b>10 daqiqa</b> davomida amal qiladi va faqat 1 marta ishlatiladi.\n\n"
        "<b>Qanday ulash mumkin?</b>\n"
        f"1. <a href=\"{settings.WEB_URL}/profile\">Be'minnat veb-saytiga</a> kiring\n"
        "2. Profil sozlamalari sahifasida 'Telegram hisobini ulash' maydoniga ushbu kodni kiriting\n"
        "3. 'Ulash' tugmasini bosing\n\n"
        "⚠️ <i>Ushbu kodni boshqa hech kimga bermang!</i>"
    )

    await call.message.answer(msg, parse_mode="HTML", disable_web_page_preview=True)
    await call.answer()
