"""
Listing Publication Flow with FSM for Ulashamiz Telegram Bot
"""
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.client import DBService
from app.config import settings
from app.keyboards.main_menu import get_main_menu_keyboard, get_cancel_keyboard
from app.keyboards.inline import (
    get_categories_inline_keyboard,
    get_condition_inline_keyboard,
    get_regions_inline_keyboard,
    get_districts_inline_keyboard,
    get_skip_photo_keyboard,
    get_confirm_publish_keyboard
)

router = Router()

class PublishStates(StatesGroup):
    category = State()
    condition = State()
    title = State()
    description = State()
    region = State()
    district = State()
    neighborhood = State()
    photo = State()
    confirm = State()

@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Amal bekor qilindi. Bosh menyudasiz.",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "cancel_action")
async def cancel_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Amal bekor qilindi.")
    await call.message.answer("Bosh menyudasiz.", reply_markup=get_main_menu_keyboard())
    await call.answer()

@router.message(F.text == "🎁 Bepul buyum berish")
async def start_publish(message: types.Message, state: FSMContext):
    await state.clear()
    categories = await DBService.get_categories()
    if not categories:
        await message.answer("Kategoriyalar ro'yxati yuklanmadi. Keyinroq urinib ko'ring.")
        return

    await state.set_state(PublishStates.category)
    await message.answer(
        "📦 <b>1/8. Buyum kategoriyasini tanlang:</b>",
        reply_markup=get_categories_inline_keyboard(categories),
        parse_mode="HTML"
    )

@router.callback_query(PublishStates.category, F.data.startswith("cat:"))
async def select_category(call: types.CallbackQuery, state: FSMContext):
    cat_id = call.data.split(":")[1]
    await state.update_data(category_id=cat_id)
    await state.set_state(PublishStates.condition)
    await call.message.edit_text(
        "✨ <b>2/8. Buyum holatini tanlang:</b>",
        reply_markup=get_condition_inline_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(PublishStates.condition, F.data.startswith("cond:"))
async def select_condition(call: types.CallbackQuery, state: FSMContext):
    cond = call.data.split(":")[1]
    await state.update_data(condition=cond)
    await state.set_state(PublishStates.title)
    await call.message.edit_text(
        "📝 <b>3/8. Buyum nomini yozing:</b>\n<i>(Masalan: Bolalar qishki kurtkasi, 5-6 yosh)</i>",
        parse_mode="HTML"
    )
    await call.message.answer(
        "Nomini yuboring:",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(PublishStates.title, F.text)
async def input_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 3 or len(title) > 120:
        await message.answer("Buyum nomi 3 tadan 120 tagacha belgidan iborat bo'lishi kerak. Qaytadan kiriting:")
        return

    await state.update_data(title=title)
    await state.set_state(PublishStates.description)
    await message.answer(
        "📄 <b>4/8. Buyum haqida batafsil tavsif bering:</b>\n"
        "<i>(O'lchami, kamchiliklari, kimga to'g'ri kelishi yoki qayerdan olib ketilishi)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(PublishStates.description, F.text)
async def input_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if len(desc) < 5:
        await message.answer("Iltimos, kamida 5 ta belgidan iborat tavsif kiriting:")
        return

    await state.update_data(description=desc)
    regions = await DBService.get_regions()
    if not regions:
        await message.answer("Viloyatlar ro'yxatini yuklab bo'lmadi.")
        return

    await state.set_state(PublishStates.region)
    await message.answer(
        "📍 <b>5/8. Viloyatingizni tanlang:</b>",
        reply_markup=get_regions_inline_keyboard(regions),
        parse_mode="HTML"
    )

@router.callback_query(PublishStates.region, F.data.startswith("reg:"))
async def select_region(call: types.CallbackQuery, state: FSMContext):
    reg_id = call.data.split(":")[1]
    await state.update_data(region_id=reg_id)
    districts = await DBService.get_districts(reg_id)
    if not districts:
        await state.update_data(district_id=None)
        await state.set_state(PublishStates.neighborhood)
        await call.message.edit_text("Mahalla yoki mo'ljalni kiriting (ixtiyoriy, o'tkazib yuborish uchun '-' yuboring):")
        await call.answer()
        return

    await state.set_state(PublishStates.district)
    await call.message.edit_text(
        "🏘 <b>6/8. Tumaningizni tanlang:</b>",
        reply_markup=get_districts_inline_keyboard(districts),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(PublishStates.district, F.data.startswith("dist:"))
async def select_district(call: types.CallbackQuery, state: FSMContext):
    dist_id = call.data.split(":")[1]
    await state.update_data(district_id=dist_id)
    await state.set_state(PublishStates.neighborhood)
    await call.message.edit_text(
        "🏡 <b>7/8. Mahalla yoki ko'cha nomini yozing (ixtiyoriy):</b>\n<i>O'tkazib yuborish uchun '-' yuboring</i>",
        parse_mode="HTML"
    )
    await call.answer()

@router.message(PublishStates.neighborhood, F.text)
async def input_neighborhood(message: types.Message, state: FSMContext):
    neighborhood = message.text.strip()
    if neighborhood == "-":
        neighborhood = ""

    await state.update_data(neighborhood=neighborhood)
    await state.set_state(PublishStates.photo)
    await message.answer(
        "📷 <b>8/8. Buyumning rasmini yuboring:</b>\n<i>(Bir dona rasm yuboring yoki rasmsiz davom eting)</i>",
        reply_markup=get_skip_photo_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(PublishStates.photo, F.data == "skip_photo")
async def skip_photo_handler(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(image_url=None)
    await show_confirmation_preview(call.message, state)
    await call.answer()

@router.message(PublishStates.photo, F.photo)
async def input_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    wait_msg = await message.answer("⏳ <i>Rasm yuklanmoqda, iltimos kuting...</i>", parse_mode="HTML")
    try:
        file = await message.bot.get_file(photo.file_id)
        import io
        import uuid
        file_io = io.BytesIO()
        await message.bot.download_file(file.file_path, destination=file_io)
        file_bytes = file_io.getvalue()
        
        filename = f"bot_uploads/{uuid.uuid4()}.jpg"
        public_url = await DBService.upload_image_to_storage(file_bytes, filename)
        await state.update_data(image_url=public_url)
    except Exception as e:
        print(f"Error handling photo upload: {e}")
        await state.update_data(image_url=None)
    finally:
        try:
            await wait_msg.delete()
        except Exception:
            pass

    await show_confirmation_preview(message, state)

async def show_confirmation_preview(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(PublishStates.confirm)

    cond_labels = {
        "new": "Yangi",
        "like_new": "Deyarli yangi",
        "good": "Yaxshi holatda",
        "fair": "O'rtacha"
    }

    preview_text = (
        "🔍 <b>E'lonni tasdiqlash</b>\n\n"
        f"📌 <b>Nomi:</b> {data.get('title')}\n"
        f"📄 <b>Tavsifi:</b> {data.get('description')}\n"
        f"✨ <b>Holati:</b> {cond_labels.get(data.get('condition', 'good'), 'Yaxshi')}\n"
        f"🏡 <b>Mo'ljal:</b> {data.get('neighborhood') or 'Ko''rsatilmagan'}\n"
        f"💰 <b>Narxi:</b> BEPUL (0 so'm)\n\n"
        "<i>E'lon saytda va botda darhol ko'rinadi. Chop etilsinmi?</i>"
    )

    image_url = data.get("image_url")
    if image_url:
        try:
            await message.answer_photo(
                photo=image_url,
                caption=preview_text,
                reply_markup=get_confirm_publish_keyboard(),
                parse_mode="HTML"
            )
            return
        except Exception:
            pass

    await message.answer(
        preview_text,
        reply_markup=get_confirm_publish_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(PublishStates.confirm, F.data == "confirm_publish")
async def finalize_publication(call: types.CallbackQuery, state: FSMContext):
    await call.answer("⏳ Chop etilmoqda...")
    data = await state.get_data()
    user = call.from_user

    # Fetch user profile id
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    listing = await DBService.create_listing(
        owner_id=profile["id"],
        title=data.get("title", ""),
        description=data.get("description", ""),
        category_id=data.get("category_id", ""),
        condition=data.get("condition", "good"),
        region_id=data.get("region_id", ""),
        district_id=data.get("district_id", ""),
        neighborhood=data.get("neighborhood"),
        image_url=data.get("image_url")
    )

    await state.clear()

    # Remove buttons from the confirmation message safely
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if listing:
        listing_id = listing["id"]
        web_link = f"{settings.WEB_URL}/items/{listing_id}"
        success_text = (
            "🎉 <b>Tabriklaymiz! E'loningiz muvaffaqiyatli chop etildi!</b>\n\n"
            f"🆔 <b>E'lon ID:</b> <code>{listing_id}</code>\n"
            f"🌐 <b>Saytdagi havola:</b> <a href=\"{web_link}\">{web_link}</a>\n\n"
            "Buyumingiz saytda va botda darhol paydo bo'ldi. Ehtiyojmand insonlar siz bilan bog'lana olishadi."
        )

        inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🌐 Saytda ko'rish", url=web_link)]
        ])

        await call.message.answer(
            success_text,
            reply_markup=inline_kb,
            parse_mode="HTML",
            disable_web_page_preview=False
        )
        await call.message.answer("Bosh menyudasiz:", reply_markup=get_main_menu_keyboard())
    else:
        await call.message.answer(
            "❌ E'lonni saqlashda xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.",
            reply_markup=get_main_menu_keyboard()
        )
