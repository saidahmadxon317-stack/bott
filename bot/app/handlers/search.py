"""
Search, Categories, and Region Filters Handler for Be'minnat Bot
Real-time DB integration with combined filters
"""
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database.client import DBService
from app.config import settings
from app.keyboards.main_menu import get_main_menu_keyboard, get_cancel_keyboard
from app.keyboards.inline import (
    get_categories_inline_keyboard,
    get_regions_inline_keyboard,
    get_listing_card_keyboard
)

router = Router()


class SearchStates(StatesGroup):
    waiting_for_keyword = State()


# ─── KEYBOARD HELPER ──────────────────────────────────────────────────────────

def get_filter_keyboard(current_cat=None, current_reg=None):
    """Active filters + navigation buttons."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    cat_label = f"✅ Kategoriya tanlangan" if current_cat else "📂 Kategoriya tanlash"
    reg_label = f"✅ Hudud tanlangan" if current_reg else "📍 Hudud tanlash"
    builder.button(text=cat_label, callback_data="filter_choose_cat")
    builder.button(text=reg_label, callback_data="filter_choose_reg")
    if current_cat or current_reg:
        builder.button(text="🔄 Filtrlarni tozalash", callback_data="filter_reset")
    builder.button(text="🏠 Asosiy menyu", callback_data="go_main")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


# ─── MAIN SEARCH ──────────────────────────────────────────────────────────────

@router.message(F.text == "🔎 Buyum topish")
async def prompt_search(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(SearchStates.waiting_for_keyword)
    await message.answer(
        "🔎 <b>Qidirayotgan buyumingiz nomini yozing:</b>\n"
        "<i>(Masalan: kitob, velosiped, ko'ylak, divan...)</i>\n\n"
        "Yoki <b>Bekor qilish</b> tugmasini bosib menyuga qayting.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(SearchStates.waiting_for_keyword, F.text)
async def execute_search(message: types.Message, state: FSMContext):
    query = message.text.strip()
    await state.clear()

    listings = await DBService.search_listings(query=query, limit=8)
    if not listings:
        await message.answer(
            f"😔 <b>\"{query}\"</b> bo'yicha hech qanday bepul buyum topilmadi.\n\n"
            "🔹 Boshqa so'z bilan qidirib ko'ring\n"
            "🔹 Kategoriyalar bo'yicha ko'rib chiqing",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"✅ <b>\"{query}\"</b> bo'yicha <b>{len(listings)}</b> ta bepul buyum topildi:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    for item in listings:
        await send_listing_card(message, item)


# ─── CATEGORIES ───────────────────────────────────────────────────────────────

@router.message(F.text == "📂 Kategoriyalar")
async def show_categories(message: types.Message, state: FSMContext):
    await state.clear()
    categories = await DBService.get_categories()
    if not categories:
        await message.answer(
            "😔 Kategoriyalar hali mavjud emas.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    await message.answer(
        "📂 <b>Qaysi kategoriyadan qidirasiz?</b>",
        reply_markup=get_categories_inline_keyboard(categories, prefix="browse_cat"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("browse_cat:"))
async def browse_by_category(call: types.CallbackQuery, state: FSMContext):
    cat_id = call.data.split(":")[1]
    # Save to session for combined filter
    await state.update_data(filter_cat=cat_id)
    data = await state.get_data()
    reg_id = data.get("filter_reg")

    listings = await DBService.search_listings(category_id=cat_id, region_id=reg_id, limit=8)
    cat_name = cat_id  # will be overridden by first listing's category name

    if listings:
        cat_name = (listings[0].get("categories") or {}).get("name_uz", cat_id)

    if not listings:
        await call.message.edit_text(
            "😔 Ushbu kategoriyada hozircha bepul e'lonlar yo'q.\n"
            "Boshqa kategoriyani tanlang yoki keyinroq qaytib keling.",
            reply_markup=get_filter_keyboard(current_cat=cat_id, current_reg=reg_id)
        )
        await call.answer()
        return

    await call.message.edit_text(
        f"✅ <b>{cat_name}</b> kategoriyasida <b>{len(listings)}</b> ta e'lon:",
        parse_mode="HTML"
    )
    for item in listings:
        await send_listing_card(call.message, item)

    # Show filter panel after results
    await call.message.answer(
        "🔽 Qo'shimcha filtr yoki menyuga qaytish:",
        reply_markup=get_filter_keyboard(current_cat=cat_id, current_reg=reg_id)
    )
    await call.answer()


# ─── REGIONS ──────────────────────────────────────────────────────────────────

@router.message(F.text == "📍 Hududni tanlash")
async def show_regions(message: types.Message, state: FSMContext):
    await state.clear()
    regions = await DBService.get_regions()
    if not regions:
        await message.answer(
            "😔 Hududlar hali mavjud emas.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    await message.answer(
        "📍 <b>Qaysi hududdan qidirasiz?</b>",
        reply_markup=get_regions_inline_keyboard(regions, prefix="browse_reg"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("browse_reg:"))
async def browse_by_region(call: types.CallbackQuery, state: FSMContext):
    reg_id = call.data.split(":")[1]
    await state.update_data(filter_reg=reg_id)
    data = await state.get_data()
    cat_id = data.get("filter_cat")

    listings = await DBService.search_listings(region_id=reg_id, category_id=cat_id, limit=8)
    reg_name = reg_id
    if listings:
        reg_name = (listings[0].get("regions") or {}).get("name_uz", reg_id)

    if not listings:
        await call.message.edit_text(
            "😔 Tanlangan hududda hozircha faol e'lonlar yo'q.",
            reply_markup=get_filter_keyboard(current_cat=cat_id, current_reg=reg_id)
        )
        await call.answer()
        return

    await call.message.edit_text(
        f"✅ <b>{reg_name}</b> hududida <b>{len(listings)}</b> ta e'lon:",
        parse_mode="HTML"
    )
    for item in listings:
        await send_listing_card(call.message, item)

    await call.message.answer(
        "🔽 Qo'shimcha filtr yoki menyuga qaytish:",
        reply_markup=get_filter_keyboard(current_cat=cat_id, current_reg=reg_id)
    )
    await call.answer()


# ─── FILTER CALLBACKS ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "filter_choose_cat")
async def filter_choose_cat(call: types.CallbackQuery, state: FSMContext):
    categories = await DBService.get_categories()
    if not categories:
        await call.answer("Kategoriyalar topilmadi", show_alert=True)
        return
    await call.message.edit_text(
        "📂 <b>Kategoriyani tanlang:</b>",
        reply_markup=get_categories_inline_keyboard(categories, prefix="browse_cat"),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "filter_choose_reg")
async def filter_choose_reg(call: types.CallbackQuery, state: FSMContext):
    regions = await DBService.get_regions()
    if not regions:
        await call.answer("Hududlar topilmadi", show_alert=True)
        return
    await call.message.edit_text(
        "📍 <b>Hududni tanlang:</b>",
        reply_markup=get_regions_inline_keyboard(regions, prefix="browse_reg"),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "filter_reset")
async def filter_reset(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(filter_cat=None, filter_reg=None)
    listings = await DBService.search_listings(limit=8)
    await call.message.edit_text(
        f"🔄 Filtrlar tozalandi. Barcha e'lonlar ({len(listings)} ta):",
        parse_mode="HTML"
    )
    for item in listings:
        await send_listing_card(call.message, item)
    await call.answer("Filtrlar tozalandi")


@router.callback_query(F.data == "go_main")
async def go_main_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=get_main_menu_keyboard()
    )
    await call.answer()


# ─── LISTING CARD RENDERER ────────────────────────────────────────────────────

async def send_listing_card(message: types.Message, item: dict):
    title = item.get("title", "Nomsiz buyum")
    desc = item.get("description", "")
    if len(desc) > 200:
        desc = desc[:197] + "..."
    category = item.get("categories", {}).get("name_uz", "Boshqa") if item.get("categories") else "Boshqa"
    district = item.get("districts", {}).get("name_uz", "") if item.get("districts") else ""
    region = item.get("regions", {}).get("name_uz", "") if item.get("regions") else ""
    location = f"{region}, {district}".strip(", ")
    cond_labels = {"new": "🆕 Yangi", "like_new": "✨ Deyarli yangi", "good": "👍 Yaxshi", "fair": "🔸 O'rtacha"}
    condition = cond_labels.get(item.get("condition", "good"), "👍 Yaxshi")

    owner_profile = item.get("profiles") or {}
    owner_username = owner_profile.get("telegram_username")
    owner_name = owner_profile.get("full_name") or "Saxiy inson"
    owner_display = f"@{owner_username}" if owner_username else owner_name

    text = (
        f"🎁 <b>{title}</b>\n\n"
        f"📝 {desc}\n\n"
        f"📦 <b>Kategoriya:</b> {category}\n"
        f"✨ <b>Holati:</b> {condition}\n"
        f"📍 <b>Hudud:</b> {location or 'Oʻzbekiston'}\n"
        f"👤 <b>Egasi:</b> {owner_display}\n"
        f"💚 <b>Narxi: BEPUL</b>"
    )

    item_id = item.get("id")
    kb = get_listing_card_keyboard(item_id, settings.WEB_URL, owner_username=owner_username)

    images = item.get("listing_images", [])
    img_url = images[0].get("url") if images else None

    if img_url:
        try:
            await message.answer_photo(photo=img_url, caption=text, reply_markup=kb, parse_mode="HTML")
            return
        except Exception:
            pass

    await message.answer(text, reply_markup=kb, parse_mode="HTML")
