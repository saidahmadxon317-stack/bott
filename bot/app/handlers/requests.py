"""
Item Requests, Daily Limit, Notifications & Edit Handler for Be'minnat Bot
- Daily limit: 1 item per user per day
- Owner notification when item is taken
- Listing edit flow
"""
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.client import DBService
from app.keyboards.main_menu import get_main_menu_keyboard, get_cancel_keyboard
from app.keyboards.inline import get_request_moderation_keyboard

router = Router()


class RequestStates(StatesGroup):
    waiting_for_message = State()


class ReportStates(StatesGroup):
    waiting_for_reason = State()


class EditListingStates(StatesGroup):
    choose_field = State()
    new_title = State()
    new_description = State()


@router.callback_query(F.data.startswith("req_item:"))
async def start_item_request(call: types.CallbackQuery, state: FSMContext):
    listing_id = call.data.split(":")[1]
    user = call.from_user

    # Fetch listing
    listing = await DBService.get_listing_by_id(listing_id)
    if not listing:
        await call.answer("E'lon topilmadi yoki o'chirilgan.", show_alert=True)
        return

    # Fetch requester profile
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    if listing.get("owner_id") == profile["id"]:
        await call.answer("O'zingizning e'loningizga so'rov yubora olmaysiz!", show_alert=True)
        return

    if listing.get("status") != "approved":
        await call.answer("Bu buyum allaqachon olib ketilgan yoki faol emas.", show_alert=True)
        return

    # ✅ DAILY LIMIT CHECK: 1 item per day
    daily_taken = await DBService.count_user_daily_requests(profile["id"])
    if daily_taken >= 1:
        await call.answer(
            "⚠️ Siz bugun allaqachon 1 ta buyum so'rovini yubordingiz!\n"
            "Kunlik limit: 1 ta buyum. Ertaga qaytadan urinib ko'ring.",
            show_alert=True
        )
        return

    await state.update_data(listing_id=listing_id, listing_title=listing.get("title", ""))
    await state.set_state(RequestStates.waiting_for_message)

    await call.message.answer(
        f"🎁 <b>\"{listing.get('title')}\"</b> buyumini olishni so'rash:\n\n"
        "Egasiga nima uchun bu buyum sizga kerakligi haqida qisqacha xabar yozing:\n"
        "<i>(Siz bilan bog'lanish uchun profilingizdagi tel. raqam va manzil ishlatiladi)</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(RequestStates.waiting_for_message, F.text)
async def input_request_message(message: types.Message, state: FSMContext):
    msg_text = message.text.strip()
    if len(msg_text) < 3:
        await message.answer("Iltimos, qisqacha xabar kiriting:")
        return

    data = await state.get_data()
    listing_id = data["listing_id"]
    user = message.from_user

    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    result = await DBService.create_item_request(
        listing_id=listing_id,
        requester_id=profile["id"],
        message=msg_text,
        phone=profile.get("phone", "")
    )

    await state.clear()

    if not result.get("success"):
        error_msg = result.get("error", "Xatolik yuz berdi")
        await message.answer(f"❌ {error_msg}", reply_markup=get_main_menu_keyboard())
        return

    req_data = result["data"]

    # Contact info for notification
    requester_username = f"@{user.username}" if user.username else "username yo'q"
    requester_phone = profile.get("phone", "ko'rsatilmagan")
    requester_address = profile.get("address", "ko'rsatilmagan")

    await message.answer(
        "✅ <b>So'rovingiz buyum egasiga yetkazildi!</b>\n\n"
        "Ega so'rovingizni qabul qilsa, sizga xabar beramiz.\n\n"
        "⏰ <i>Kunlik limitingiz ishlatildi. Ertaga yana 1 ta buyum so'rovisiz mumkin.</i>",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

    # 📬 NOTIFY LISTING OWNER
    listing = await DBService.get_listing_by_id(listing_id)
    if listing and listing.get("profiles"):
        owner_tg_id = listing["profiles"].get("telegram_id")
        if owner_tg_id:
            try:
                owner_text = (
                    f"📬 <b>Sizning \"{listing.get('title')}\" e'loningizga so'rov keldi!</b>\n\n"
                    f"👤 <b>So'rovchi:</b> {user.full_name}\n"
                    f"📱 <b>Telegram:</b> {requester_username}\n"
                    f"📞 <b>Telefon:</b> {requester_phone}\n"
                    f"📍 <b>Manzil:</b> {requester_address}\n\n"
                    f"💬 <b>Xabari:</b> \"{msg_text}\"\n\n"
                    "So'rovni qabul qilasizmi?\n"
                    "<i>Qabul qilsangiz, buyumingiz olib ketildi deb belgilanadi va e'lon yopiladi.</i>"
                )
                await message.bot.send_message(
                    chat_id=owner_tg_id,
                    text=owner_text,
                    reply_markup=get_request_moderation_keyboard(req_data["id"]),
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Could not notify owner {owner_tg_id}: {e}")


@router.callback_query(F.data.startswith("accept_req:"))
async def handle_accept_request(call: types.CallbackQuery):
    req_id = call.data.split(":")[1]
    user = call.from_user
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    result = await DBService.accept_request_and_close_listing(
        request_id=req_id,
        owner_id=profile["id"]
    )

    if result.get("success"):
        await call.message.edit_text(
            "✅ <b>So'rov qabul qilindi!</b>\n\n"
            "E'loningiz yopildi (olib ketildi deb belgilandi).\n"
            "So'rov yuborgan inson bilan to'g'ridan-to'g'ri bog'laning.",
            parse_mode="HTML"
        )

        # 🔔 Notify requester that their request was accepted
        requester_tg_id = result.get("requester_telegram_id")
        listing_title = result.get("listing_title", "buyum")
        owner_username = f"@{user.username}" if user.username else user.full_name

        if requester_tg_id:
            try:
                await call.bot.send_message(
                    chat_id=requester_tg_id,
                    text=(
                        f"🎉 <b>Tabriklaymiz! So'rovingiz qabul qilindi!</b>\n\n"
                        f"📦 <b>Buyum:</b> {listing_title}\n"
                        f"👤 <b>Egasi:</b> {owner_username}\n\n"
                        "Buyum egasi bilan to'g'ridan-to'g'ri bog'laning va kelishib oling. "
                        "Bu e'lon endi yopildi."
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Could not notify requester: {e}")
    else:
        await call.answer("So'rovni yangilab bo'lmadi.", show_alert=True)
    await call.answer()


@router.callback_query(F.data.startswith("reject_req:"))
async def handle_reject_request(call: types.CallbackQuery):
    req_id = call.data.split(":")[1]
    user = call.from_user
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    result = await DBService.reject_request(
        request_id=req_id,
        owner_id=profile["id"]
    )

    if result.get("success"):
        await call.message.edit_text("❌ So'rov rad etildi.")

        # Notify requester
        requester_tg_id = result.get("requester_telegram_id")
        listing_title = result.get("listing_title", "buyum")
        if requester_tg_id:
            try:
                await call.bot.send_message(
                    chat_id=requester_tg_id,
                    text=(
                        f"😔 Afsuski, <b>\"{listing_title}\"</b> buyumi uchun so'rovingiz rad etildi.\n\n"
                        "Boshqa e'lonlarni ko'rib chiqishingiz mumkin."
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Could not notify requester of rejection: {e}")
    else:
        await call.answer("So'rovni yangilab bo'lmadi.", show_alert=True)
    await call.answer()


# ─── EDIT LISTING ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("edit_listing:"))
async def start_edit_listing(call: types.CallbackQuery, state: FSMContext):
    listing_id = call.data.split(":")[1]
    await state.update_data(edit_listing_id=listing_id)
    await state.set_state(EditListingStates.choose_field)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Nomini o'zgartirish", callback_data=f"edit_field:title")],
        [InlineKeyboardButton(text="📄 Tavsifini o'zgartirish", callback_data=f"edit_field:desc")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ])
    await call.message.answer(
        "✏️ <b>E'lonni tahrirlash</b>\n\nQaysi maydonni o'zgartirmoqchisiz?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(EditListingStates.choose_field, F.data.startswith("edit_field:"))
async def choose_edit_field(call: types.CallbackQuery, state: FSMContext):
    field = call.data.split(":")[1]
    await state.update_data(edit_field=field)

    if field == "title":
        await state.set_state(EditListingStates.new_title)
        await call.message.answer(
            "📝 Yangi nomni yozing (3-120 belgi):",
            reply_markup=get_cancel_keyboard()
        )
    else:
        await state.set_state(EditListingStates.new_description)
        await call.message.answer(
            "📄 Yangi tavsifni yozing:",
            reply_markup=get_cancel_keyboard()
        )
    await call.answer()


@router.message(EditListingStates.new_title, F.text)
async def save_edit_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 3 or len(title) > 120:
        await message.answer("❌ Nom 3-120 belgi bo'lishi kerak:")
        return

    data = await state.get_data()
    user = message.from_user
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    ok = await DBService.update_listing_field(
        listing_id=data["edit_listing_id"],
        owner_id=profile["id"],
        field="title",
        value=title
    )
    await state.clear()

    if ok:
        await message.answer("✅ E'lon nomi yangilandi!", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer("❌ O'zgartirib bo'lmadi. Faqat o'z e'lonlaringizni tahrirlashingiz mumkin.", reply_markup=get_main_menu_keyboard())


@router.message(EditListingStates.new_description, F.text)
async def save_edit_description(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    if len(desc) < 5:
        await message.answer("❌ Tavsif juda qisqa:")
        return

    data = await state.get_data()
    user = message.from_user
    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    ok = await DBService.update_listing_field(
        listing_id=data["edit_listing_id"],
        owner_id=profile["id"],
        field="description",
        value=desc
    )
    await state.clear()

    if ok:
        await message.answer("✅ E'lon tavsifi yangilandi!", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer("❌ O'zgartirib bo'lmadi.", reply_markup=get_main_menu_keyboard())


# ─── REPORT ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("rep_item:"))
async def start_report_flow(call: types.CallbackQuery, state: FSMContext):
    listing_id = call.data.split(":")[1]
    await state.update_data(report_listing_id=listing_id)
    await state.set_state(ReportStates.waiting_for_reason)
    await call.message.answer(
        "⚠️ <b>E'lon ustidan shikoyat qilish:</b>\n\n"
        "Iltimos, qanday qoidabuzarlik sezganingizni yozib qoldiring\n"
        "<i>(masalan: pul talab qilinmoqda, taqiqlangan mahsulot va h.k.):</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(ReportStates.waiting_for_reason, F.text)
async def submit_report_reason(message: types.Message, state: FSMContext):
    reason = message.text.strip()
    data = await state.get_data()
    listing_id = data.get("report_listing_id")
    user = message.from_user

    profile = await DBService.get_or_create_user_profile(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    await DBService.submit_report(
        reporter_id=profile["id"],
        listing_id=listing_id,
        reason=reason
    )

    await state.clear()
    await message.answer(
        "✅ Shikoyatingiz qabul qilindi va moderatorlar tomonidan ko'rib chiqiladi. Rahmat!",
        reply_markup=get_main_menu_keyboard()
    )
