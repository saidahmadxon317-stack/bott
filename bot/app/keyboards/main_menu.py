"""
Persistent Main Menu Keyboard for Ulashamiz Telegram Bot
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Main menu keyboard with 8 primary actions specified in project requirements:
    - 🔎 Buyum topish
    - 🎁 Bepul buyum berish
    - 📂 Kategoriyalar
    - 📍 Hududni tanlash
    - ❤️ Saqlanganlar
    - 📦 Mening e'lonlarim
    - 👤 Profil
    - ℹ️ Yordam
    """
    keyboard = [
        [
            KeyboardButton(text="🔎 Buyum topish"),
            KeyboardButton(text="🎁 Bepul buyum berish")
        ],
        [
            KeyboardButton(text="📂 Kategoriyalar"),
            KeyboardButton(text="📍 Hududni tanlash")
        ],
        [
            KeyboardButton(text="❤️ Saqlanganlar"),
            KeyboardButton(text="📦 Mening e'lonlarim")
        ],
        [
            KeyboardButton(text="👤 Profil"),
            KeyboardButton(text="ℹ️ Yordam")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Quyidagi bo'limlardan birini tanlang..."
    )

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
