import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- ASOSIY SOZLAMALAR ---
TOKEN = "8318944066:AAFzbWusxwkL9eSbCuoWfoTihyB-Ivh1V2w"
ADMIN_ID = 8135296587 # ID raqamingiz

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- BAZA BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect("manecafe.db")
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    
    defaults = [
        ('group_url', 'https://t.me/manecafe_group'),
        ('sayt_url', 'https://manecafe.uz/uz'),
        ('b1', 'Taomlar 🍲'), ('b2', 'Ichimliklar ☕️'),
        ('b3', 'Shirinliklar 🍰'), ('b4', 'Yetkazib berish 🚚'),
        ('b5', 'Biz haqimizda ℹ️'), ('b6', 'Mane Cafe Menu 🍴')
    ]
    for k, v in defaults:
        cursor.execute("INSERT OR IGNORE INTO settings VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

def get_conf(key):
    try:
        conn = sqlite3.connect("manecafe.db")
        res = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
        return res[0] if res else ""
    except:
        return "Tugma"

def set_conf(key, value):
    conn = sqlite3.connect("manecafe.db")
    conn.execute("UPDATE settings SET value=? WHERE key=?", (value, key))
    conn.commit()
    conn.close()

# --- HOLATLAR ---
class AdminStates(StatesGroup):
    waiting_reklama = State()
    waiting_config_val = State()

# --- KLAVIATURALAR ---
def get_main_menu():
    kb = [
        [KeyboardButton(text=get_conf('b1')), KeyboardButton(text=get_conf('b2'))],
        [KeyboardButton(text=get_conf('b3')), KeyboardButton(text=get_conf('b4'))],
        [KeyboardButton(text=get_conf('b5'))],
        [KeyboardButton(text=get_conf('b6'))]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- HANDLERLAR ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    conn = sqlite3.connect("manecafe.db")
    conn.execute("INSERT OR IGNORE INTO users VALUES (?)", (message.from_user.id,))
    conn.commit()
    conn.close()
    
    sub_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Guruhga qo'shilish", url=get_conf('group_url'))],
        [InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_sub")]
    ])
    await message.answer("Mane Cafe botiga xush kelibsiz!", reply_markup=sub_kb)

@dp.callback_query(F.data == "check_sub")
async def checked(call: types.CallbackQuery):
    await call.message.answer("Xush kelibsiz!", reply_markup=get_main_menu())
    await call.answer()

# 6-tugma (Sayt) - Xatolik bermasligi uchun tekshirish usuli o'zgardi
@dp.message(lambda message: message.text == get_conf('b6'))
async def open_site(message: types.Message):
    url_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Saytga o'tish", url=get_conf('sayt_url'))]
    ])
    await message.answer("Menyu sayti:", reply_markup=url_kb)

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def admin_main(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Reklama", callback_data="adm_reklama")],
            [InlineKeyboardButton(text="🔗 Guruh linki", callback_data="conf_group_url")],
            [InlineKeyboardButton(text="🌐 Sayt linki", callback_data="conf_sayt_url")],
            [InlineKeyboardButton(text="✏️ Tugmalar", callback_data="adm_edit_btns")]
        ])
        await message.answer("Admin paneli:", reply_markup=kb)

@dp.callback_query(F.data.startswith("conf_"))
async def edit_config(call: types.CallbackQuery, state: FSMContext):
    key = call.data.replace("conf_", "")
    await state.update_data(key=key)
    await call.message.answer(f"Yangi qiymatni yuboring:")
    await state.set_state(AdminStates.waiting_config_val)

@dp.callback_query(F.data == "adm_edit_btns")
async def list_btns(call: types.CallbackQuery):
    btns = [[InlineKeyboardButton(text=get_conf(f"b{i}"), callback_data=f"conf_b{i}")] for i in range(1, 7)]
    await call.message.edit_text("O'zgartirmoqchi bo'lgan tugmani tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.message(AdminStates.waiting_config_val)
async def update_config(message: types.Message, state: FSMContext):
    data = await state.get_data()
    set_conf(data['key'], message.text)
    await message.answer("✅ Saqlandi!")
    await state.clear()

@dp.callback_query(F.data == "adm_reklama")
async def start_ads(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Reklama xabarini yuboring:")
    await state.set_state(AdminStates.waiting_reklama)

@dp.message(AdminStates.waiting_reklama)
async def send_ads(message: types.Message, state: FSMContext):
    conn = sqlite3.connect("manecafe.db")
    users = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    for u in users:
        try: await message.copy_to(u[0])
        except: pass
    await message.answer("Reklama tarqatildi.")
    await state.clear()

# --- ISHGA TUSHIRISH ---
async def main():
    init_db() # Jadvallarni yaratish
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())