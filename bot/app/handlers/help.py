"""
Help and Community Guidelines Handler for Ulashamiz Bot
"""
from aiogram import Router, F, types
from app.config import settings

router = Router()

@router.message(F.text == "ℹ️ Yordam")
async def show_help(message: types.Message):
    help_text = (
        "ℹ️ <b>Be'minnat loyihasi haqida ma'lumot</b>\n\n"
        "🌱 <b>Maqsadimiz:</b>\n"
        "O'zbekistonda ortiqcha va foydali buyumlarni bepul ulashish madaniyatini rivojlantirish, isrofgarchilikning oldini olish va muhtojlarga beminnat ko'maklashish.\n\n"
        "📜 <b>Asosiy qoidalar:</b>\n"
        "1. <b>Barcha buyumlar 100% BEPUL:</b> Pul, komissiya yoki evaziga xizmat so'rash qat'iyan taqiqlanadi.\n"
        "2. <b>Yaroqlilik:</b> Oziq-ovqatlar yaroqli, kiyimlar toza va butun, texnikalar ishlaydigan holatda bo'lishi shart.\n"
        "3. <b>Kunlik limit:</b> Har bir foydalanuvchi bir kunda faqat 1 ta buyum olishi mumkin.\n"
        "4. <b>Taqiqlangan buyumlar:</b> Dori-darmonlar, qurol-yarog', xavfli moddalar va qonun bilan taqiqlangan har qanday buyumlar.\n\n"
        "🌐 <b>Veb-saytimiz:</b> " + settings.WEB_URL + "\n"
        "📢 <b>Rasmiy kanal:</b> " + settings.TELEGRAM_CHANNEL + "\n"
        "Aloqa va takliflar: @beminnatuz_bot"
    )
    await message.answer(help_text, parse_mode="HTML", disable_web_page_preview=True)
