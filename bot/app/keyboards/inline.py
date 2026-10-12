"""
Inline Keyboards for Ulashamiz Telegram Bot
"""
from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_categories_inline_keyboard(categories: List[Dict[str, Any]], prefix: str = "cat") -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        name = cat.get("name_uz", "Kategoriya")
        cat_id = cat.get("id")
        buttons.append([InlineKeyboardButton(text=f"📦 {name}", callback_data=f"{prefix}:{cat_id}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_condition_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="✨ Yangi (ishlatilmagan)", callback_data="cond:new")],
        [InlineKeyboardButton(text="🌟 Deyarli yangi", callback_data="cond:like_new")],
        [InlineKeyboardButton(text="👍 Yaxshi holatda", callback_data="cond:good")],
        [InlineKeyboardButton(text="👌 O'rtacha (ishlaydi)", callback_data="cond:fair")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_regions_inline_keyboard(regions: List[Dict[str, Any]], prefix: str = "reg") -> InlineKeyboardMarkup:
    buttons = []
    # Display in 2 columns
    row = []
    for reg in regions:
        name = reg.get("name_uz", "Viloyat")
        reg_id = reg.get("id")
        row.append(InlineKeyboardButton(text=name, callback_data=f"{prefix}:{reg_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_districts_inline_keyboard(districts: List[Dict[str, Any]], prefix: str = "dist") -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for d in districts:
        name = d.get("name_uz", "Tuman")
        d_id = d.get("id")
        row.append(InlineKeyboardButton(text=name, callback_data=f"{prefix}:{d_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_regions")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_publish_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlayman va chop etaman", callback_data="confirm_publish"),
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skip_photo_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="⏩ Rasmsiz davom etish", callback_data="skip_photo")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_listing_card_keyboard(listing_id: str, web_url: str, is_favorite: bool = False, owner_username: Optional[str] = None) -> InlineKeyboardMarkup:
    fav_icon = "💔 O'chirish" if is_favorite else "❤️ Saqlash"
    keyboard = []
    if owner_username:
        keyboard.append([
            InlineKeyboardButton(text=f"💬 Egasiga yozish (@{owner_username})", url=f"https://t.me/{owner_username}")
        ])
    item_web_url = f"{web_url}/items/{listing_id}" if "localhost" not in web_url else f"https://beminnat.uz/items/{listing_id}"
    keyboard.extend([
        [
            InlineKeyboardButton(text="🎁 Buyumni olishni so'rash", callback_data=f"req_item:{listing_id}"),
            InlineKeyboardButton(text=fav_icon, callback_data=f"fav_toggle:{listing_id}")
        ],
        [
            InlineKeyboardButton(text="🌐 Saytda ko'rish", url=item_web_url),
            InlineKeyboardButton(text="⚠️ Shikoyat qilish", callback_data=f"rep_item:{listing_id}")
        ]
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_owner_listing_keyboard(listing_id: str, is_given_away: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if not is_given_away:
        buttons.append([InlineKeyboardButton(text="✅ Olib ketildi deb belgilash", callback_data=f"mark_given:{listing_id}")])
        buttons.append([InlineKeyboardButton(text="✏️ E'lonni tahrirlash", callback_data=f"edit_listing:{listing_id}")])
    buttons.append([InlineKeyboardButton(text="🗑 E'lonni o'chirish", callback_data=f"delete_listing:{listing_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_request_moderation_keyboard(request_id: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Qabul qilish (Kontaktni ulashish)", callback_data=f"accept_req:{request_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_req:{request_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_search_pagination_keyboard(offset: int, limit: int, total_count: int, query_type: str = "search") -> InlineKeyboardMarkup:
    buttons = []
    nav_row = []
    if offset > 0:
        prev_offset = max(0, offset - limit)
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"page:{query_type}:{prev_offset}"))
    if offset + limit < total_count:
        next_offset = offset + limit
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"page:{query_type}:{next_offset}"))
    if nav_row:
        buttons.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
