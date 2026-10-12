"""
Start & Registration Handler for Be'minnat Telegram Bot
Simple registration: full_name + phone (address optional)
"""
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from app.database.client import DBService
from app.keyboards.main_menu import get_main_menu_keyboard
from app.config import settings

router = Router()


class RegisterStates(StatesGroup):
    full_name = State()
    phone = State()


def get_phone_keyboard():
    """Share contact button keyboard."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Raqamni ulashish", request_contact=True)
    builder.button(text="❌ Bekor qilish")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    if not user:
        return

    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    # Already registered — show main menu
    if profile.get("phone"):
        name = profile.get("full_name") or user.full_name or "Foydalanuvchi"
        await message.answer(
            f"👋 Assalomu alaykum, <b>{name}</b>!\n\n"
            "🤲 <b>Be'minnat</b> — bepul buyumlar ulashish platformasi!\n\n"
            "✨ Barcha buyumlar <b>100% BEPUL</b> beriladi.\n\n"
            f"📢 Kanalimiz: <a href=\"{settings.TELEGRAM_CHANNEL}\">@beminnatuzz</a>",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return

    # New user — start registration
    # Try to pre-fill name from Telegram
    tg_name = user.full_name or ""
    await state.set_state(RegisterStates.full_name)
    await state.update_data(tg_name=tg_name)

    await message.answer(
        "🤲 <b>Be'minnat</b> botiga xush kelibsiz!\n\n"
        "Bu yerda bepul buyumlar berib va olib bo'ladi.\n\n"
        "📝 <b>Bir marta ro'yxatdan o'tish kerak:</b>\n\n"
        f"1️⃣ <b>Ism va familyangizni</b> yozing:\n"
        + (f"<i>(Yoki shunchaki ✅ yuboring — Telegram ismingiz: {tg_name})</i>" if tg_name else "<i>Masalan: Alisher Karimov</i>"),
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(RegisterStates.full_name, F.text)
async def reg_full_name(message: types.Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard())
        return

    data = await state.get_data()
    tg_name = data.get("tg_name", "")

    # Accept "✅" or any short confirm as "use Telegram name"
    if text in ("✅", "+", "ha", "ok", "Ok") and tg_name:
        name = tg_name
    else:
        name = text

    if len(name) < 2 or len(name) > 80:
        await message.answer("❌ Ism kamida 2, ko'pi bilan 80 ta belgi bo'lishi kerak. Qaytadan kiriting:")
        return

    await state.update_data(full_name=name)
    await state.set_state(RegisterStates.phone)
    await message.answer(
        f"✅ <b>{name}</b> — qabul qilindi!\n\n"
        "2️⃣ <b>Telefon raqamingizni yuboring:</b>\n"
        "<i>Pastdagi tugmani bosib avtomatik yuboring yoki qo'lda kiriting (+998XXXXXXXXX)</i>",
        parse_mode="HTML",
        reply_markup=get_phone_keyboard()
    )


@router.message(RegisterStates.phone, F.contact)
async def reg_phone_contact(message: types.Message, state: FSMContext):
    """Handle shared contact (button click)."""
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await _finish_registration(message, state, phone)


@router.message(RegisterStates.phone, F.text)
async def reg_phone_text(message: types.Message, state: FSMContext):
    """Handle manually typed phone."""
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard())
        return

    cleaned = text.replace(" ", "").replace("-", "")
    if not (cleaned.startswith("+998") or cleaned.startswith("998") or cleaned.startswith("8")):
        await message.answer(
            "❌ O'zbekiston telefon raqami kiriting.\n"
            "<i>Masalan: +998901234567</i>",
            parse_mode="HTML"
        )
        return
    if len(cleaned.lstrip("+")) < 9:
        await message.answer("❌ Raqam juda qisqa. To'liq kiriting:")
        return

    if not cleaned.startswith("+"):
        cleaned = "+998" + cleaned[-9:]

    await _finish_registration(message, state, cleaned)


async def _finish_registration(message: types.Message, state: FSMContext, phone: str):
    data = await state.get_data()
    full_name = data.get("full_name", "Foydalanuvchi")
    user = message.from_user

    await DBService.update_user_profile(
        telegram_id=user.id,
        full_name=full_name,
        phone=phone,
        address="Noma'lum",
        username=user.username
    )

    await state.clear()

    await message.answer(
        "🎉 <b>Tabriklaymiz! Ro'yxatdan o'tdingiz!</b>\n\n"
        f"👤 Ism: <b>{full_name}</b>\n"
        f"📱 Tel: <b>{phone}</b>\n\n"
        "✅ Endi Be'minnat xizmatlaridan to'liq foydalana olasiz!\n\n"
        f"📢 Kanalimiz: <a href=\"{settings.TELEGRAM_CHANNEL}\">@beminnatuzz</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=get_main_menu_keyboard()
    )
