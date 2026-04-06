import logging
import json
import os
import re
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
BOT_TOKEN       = "8378061773:AAGCYY3fKQXpj7AdAIm7174i4sgwbusM8_0"
ADMIN_ID        = 7091424551
ADMIN_SECRET    = "darkking2024"          # type this once to become admin forever
UPI_ID          = "kpal2224-1@okhdfcbank"
WHATSAPP_NUMBER = "8955839183"
GROUP_LINK      = "https://t.me/+EtcBGgRnC7NlOTM1"
CHANNEL_LINK    = "https://t.me/+IL_C-z51NVU3MzI1"
NOTIFY_CHAT_ID  = 7091424551             # orders → your personal Telegram (change to channel -100 id when ready)

DATA_FILE    = "data.json"
PRODUCT_FILE = "products.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  DATA HELPERS
# ─────────────────────────────────────────────
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_data():
    return load_json(DATA_FILE, {"admins": [ADMIN_ID], "orders": {}, "customers": {}, "order_counter": 1})

def save_data(d):
    save_json(DATA_FILE, d)

def get_products():
    return load_json(PRODUCT_FILE, {"L": {}, "K": {}})

def save_products(p):
    save_json(PRODUCT_FILE, p)

def is_admin(uid):
    d = get_data()
    return uid in d.get("admins", [ADMIN_ID])

def next_order_id():
    d = get_data()
    oid = f"ORD{d['order_counter']:04d}"
    d["order_counter"] += 1
    save_data(d)
    return oid

# ─────────────────────────────────────────────
#  DARK KNIGHT WELCOME MESSAGE
# ─────────────────────────────────────────────
DARK_WELCOME = """\
☠️💀☠️💀☠️💀☠️💀☠️💀☠️

╔═══════════════════════╗
║   🩸 𝘿𝘼𝙍𝙆  𝙆𝙉𝙄𝙂𝙃𝙏 🩸   ║
╚═══════════════════════╝

🕸️🕷️🕸️🕷️🕸️🕷️🕸️🕷️🕸️🕷️🕸️

❝ ... ʏᴏᴜ ᴅᴀʀᴇᴅ ᴛᴏ ᴇɴᴛᴇʀ ᴍʏ ᴅᴏᴍᴀɪɴ? ❞

💀 The Dark Knight emerges...
    cloak black as death...
    eyes red as blood...

❝ ɪ ᴀᴍ ᴛʜᴇ sʜᴀᴅᴏᴡ ɢᴜᴀʀᴅɪᴀɴ
  ᴏꜰ ꜰᴀsʜɪᴏɴsᴛᴏʀᴇ.000
  ɴᴏɴᴇ sʜᴀʟʟ ᴘᴀss... ❞

🩸🩸🩸🩸🩸🩸🩸🩸🩸🩸🩸

❝ ʙᴜᴛ ᴍʏ ᴋɪɴɢ sᴇɴᴛ ᴍᴇ ᴛᴏ ɢᴜɪᴅᴇ ʏᴏᴜ.
  ᴄᴏᴍᴇ... ɪ ᴡɪʟʟ ʟᴇᴀᴅ ʏᴏᴜ
  ᴛᴏ ᴛʜᴇ ꜰᴀsʜɪᴏɴ ᴡᴏʀʟᴅ ❞ 🐺⚔️

☠️ ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ᴘᴀᴛʜ ʙᴇʟᴏᴡ... ɪꜰ ʏᴏᴜ ᴅᴀʀᴇ ☠️"""

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Browse Products",    callback_data="browse")],
        [InlineKeyboardButton("🛒 Place Order",         callback_data="start_order")],
        [InlineKeyboardButton("📦 Track My Order",      callback_data="track")],
        [InlineKeyboardButton("📞 Contact Us",          callback_data="contact")],
    ])

# ─────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    d = get_data()
    uid = str(user.id)
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    if uid not in d["customers"]:
        d["customers"][uid] = {"name": user.full_name, "username": user.username or "", "visits": 1, "first": now, "orders": []}
        tag = "🆕 NEW VISITOR"
    else:
        d["customers"][uid]["visits"] += 1
        tag = "🔄 RETURNING CUSTOMER"
    save_data(d)

    try:
        visits = d["customers"][uid]["visits"]
        notif = (
            f"{tag}\n"
            f"👤 Name     : {user.full_name}\n"
            f"🆔 Username : @{user.username or 'N/A'}\n"
            f"📊 Visits   : {visits}\n"
            f"🕐 Time     : {now}"
        )
        await context.bot.send_message(chat_id=NOTIFY_CHAT_ID, text=notif)
    except Exception:
        pass

    await update.message.reply_text(DARK_WELCOME, reply_markup=main_menu_keyboard())

# ─────────────────────────────────────────────
#  GROUP: welcome new members
# ─────────────────────────────────────────────
async def group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        welcome = (
            f"☠️💀☠️💀☠️💀☠️💀☠️💀☠️\n\n"
            f"🩸 A new soul has entered...\n"
            f"❝ Welcome, {member.full_name}... ❞\n\n"
            f"💀 The Dark Knight steps forward...\n\n"
            f"❝ ɪ ᴀᴍ ᴛʜᴇ sʜᴀᴅᴏᴡ ɢᴜᴀʀᴅɪᴀɴ\n"
            f"  ᴏꜰ ꜰᴀsʜɪᴏɴsᴛᴏʀᴇ.000\n"
            f"  ᴍʏ ᴋɪɴɢ ᴡᴇʟᴄᴏᴍᴇs ʏᴏᴜ... ❞ 🐺⚔️\n\n"
            f"🕸️🕷️🕸️🕷️🕸️🕷️🕸️🕷️🕸️🕷️🕸️\n\n"
            f"👗 Browse products & order below 👇"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚔️ ORDER NOW — Open Dark Knight Bot", url=f"https://t.me/{context.bot.username}?start=group")]
        ])
        await update.message.reply_text(welcome, reply_markup=kb)

# ─────────────────────────────────────────────
#  BROWSE PRODUCTS
# ─────────────────────────────────────────────
async def browse_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = get_products()

    kb = []
    if products["L"]:
        kb.append([InlineKeyboardButton("🔥 Loot Bazar Collection", callback_data="cat_L")])
    if products["K"]:
        kb.append([InlineKeyboardButton("👑 K Loot Bazar Collection", callback_data="cat_K")])
    if not kb:
        await query.edit_message_text("⚔️ No products yet... The King is preparing the collection. Stay tuned! 🐺", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]))
        return
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="back_home")])
    await query.edit_message_text("🩸 Choose your collection, brave soul:", reply_markup=InlineKeyboardMarkup(kb))

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.split("_")[1]
    products = get_products()
    items = products.get(cat, {})

    if not items:
        await query.edit_message_text("☠️ This collection is empty. Coming soon!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="browse")]]))
        return

    kb = []
    for code, info in items.items():
        kb.append([InlineKeyboardButton(f"{code} — {info['name']} — Rs.{info['price']}", callback_data=f"product_{code}")])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="browse")])
    label = "🔥 Loot Bazar" if cat == "L" else "👑 K Loot Bazar"
    await query.edit_message_text(f"{label} Collection:\n\n☠️ Choose a product to view details:", reply_markup=InlineKeyboardMarkup(kb))

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data.replace("product_", "")
    products = get_products()
    cat = "L" if code.startswith("L") else "K"
    info = products[cat].get(code)

    if not info:
        await query.answer("Product not found!", show_alert=True)
        return

    sizes = " | ".join(info.get("sizes", []))
    caption = (
        f"🩸 *{info['name']}*\n\n"
        f"🏷️ Code  : `{code}`\n"
        f"💰 Price : Rs.{info['price']}\n"
        f"📐 Sizes : {sizes}\n\n"
        f"❝ ᴀ ᴘɪᴇᴄᴇ ꜰɪᴛ ꜰᴏʀ ᴍʏ ᴋɪɴɢ's ᴄᴏᴜʀᴛ ❞ 🐺"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🛒 Order {code}", callback_data=f"order_item_{code}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"cat_{cat}")]
    ])

    if info.get("photo_id"):
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=info["photo_id"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=kb
        )
    else:
        await query.edit_message_text(caption, parse_mode="Markdown", reply_markup=kb)

# ─────────────────────────────────────────────
#  ORDER CONVERSATION
# ─────────────────────────────────────────────
ASK_NAME, ASK_PRODUCT, ASK_SIZE, ASK_ADDRESS, ASK_PHONE, ASK_PAYMENT = range(6)

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Check if coming from a specific product
    if query.data.startswith("order_item_"):
        code = query.data.replace("order_item_", "")
        context.user_data["order_product"] = code
        context.user_data["order_from_product"] = True

    await query.edit_message_text(
        "⚔️ The Dark Knight begins your order...\n\n"
        "🩸 *Step 1 of 5*\n\n"
        "👤 What is your *full name*, brave soul?",
        parse_mode="Markdown"
    )
    return ASK_NAME

async def ask_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_name"] = update.message.text.strip()

    if context.user_data.get("order_from_product"):
        code = context.user_data["order_product"]
        products = get_products()
        cat = "L" if code.startswith("L") else "K"
        info = products[cat].get(code, {})
        sizes = info.get("sizes", [])
        kb = [[InlineKeyboardButton(s, callback_data=f"size_{s}")] for s in sizes]
        await update.message.reply_text(
            f"🩸 *Step 2 of 5*\n\n"
            f"📐 Choose your size for *{info.get('name', code)}*:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return ASK_SIZE
    else:
        products = get_products()
        all_items = {}
        for cat, items in products.items():
            all_items.update(items)
        if not all_items:
            await update.message.reply_text("☠️ No products available yet! Come back soon. 🐺")
            return ConversationHandler.END

        kb = []
        for code, info in all_items.items():
            kb.append([InlineKeyboardButton(f"{code} — {info['name']} — Rs.{info['price']}", callback_data=f"pick_{code}")])
        await update.message.reply_text(
            f"🩸 *Step 2 of 5*\n\n"
            f"👗 Choose your product:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return ASK_PRODUCT

async def product_picked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data.replace("pick_", "")
    context.user_data["order_product"] = code
    products = get_products()
    cat = "L" if code.startswith("L") else "K"
    info = products[cat].get(code, {})
    sizes = info.get("sizes", [])
    kb = [[InlineKeyboardButton(s, callback_data=f"size_{s}")] for s in sizes]
    await query.edit_message_text(
        f"🩸 *Step 3 of 5*\n\n📐 Choose your size for *{info.get('name', code)}*:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ASK_SIZE

async def size_picked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["order_size"] = query.data.replace("size_", "")
    await query.edit_message_text(
        "🩸 *Step 3 of 5*\n\n"
        "🏠 Please send your *complete delivery address*:\n\n"
        "_(House No, Street, Area, City, State, Pincode)_",
        parse_mode="Markdown"
    )
    return ASK_ADDRESS

async def address_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_address"] = update.message.text.strip()
    await update.message.reply_text(
        "🩸 *Step 4 of 5*\n\n"
        "📱 Your *WhatsApp number* please:\n_(10 digit number)_",
        parse_mode="Markdown"
    )
    return ASK_PHONE

async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip().replace(" ", "").replace("+91", "")
    if not re.fullmatch(r"\d{10}", phone):
        await update.message.reply_text("❌ Please enter a valid 10-digit WhatsApp number:")
        return ASK_PHONE
    context.user_data["order_phone"] = phone

    code = context.user_data["order_product"]
    products = get_products()
    cat = "L" if code.startswith("L") else "K"
    info = products[cat].get(code, {})

    await update.message.reply_text(
        f"🩸 *Step 5 of 5 — Payment*\n\n"
        f"💰 Amount : *Rs.{info.get('price', '?')}*\n"
        f"🏦 UPI ID : `{UPI_ID}`\n\n"
        f"1️⃣ Pay on UPI\n"
        f"2️⃣ Take screenshot\n"
        f"3️⃣ Send screenshot here 👇\n\n"
        f"❝ ᴛʜᴇ ᴅᴀʀᴋ ᴋɴɪɢʜᴛ ᴀᴡᴀɪᴛs ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ... ❞",
        parse_mode="Markdown"
    )
    return ASK_PAYMENT

async def payment_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("📸 Please send the *payment screenshot* as a photo!", parse_mode="Markdown")
        return ASK_PAYMENT

    photo_id = update.message.photo[-1].file_id
    user = update.effective_user
    ud = context.user_data
    code = ud["order_product"]
    products = get_products()
    cat = "L" if code.startswith("L") else "K"
    info = products[cat].get(code, {})
    order_id = next_order_id()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Save order
    d = get_data()
    d["orders"][order_id] = {
        "id": order_id,
        "user_id": user.id,
        "name": ud["order_name"],
        "product": code,
        "product_name": info.get("name", code),
        "size": ud["order_size"],
        "address": ud["order_address"],
        "phone": ud["order_phone"],
        "price": info.get("price", "?"),
        "status": "Pending",
        "time": now
    }
    if str(user.id) in d["customers"]:
        d["customers"][str(user.id)]["orders"].append(order_id)
    save_data(d)

    # Notify admin — clean box format
    notif_text = (
        f"╔══════ 🩸 NEW ORDER 🩸 ══════╗\n"
        f"🆔 Order ID   : {order_id}\n"
        f"👤 Name       : {ud['order_name']}\n"
        f"📦 Product    : {code} — {info.get('name', code)}\n"
        f"📐 Size       : {ud['order_size']}\n"
        f"💰 Price      : Rs.{info.get('price', '?')}\n"
        f"🏠 Address    : {ud['order_address']}\n"
        f"📱 WhatsApp   : wa.me/{ud['order_phone']}\n"
        f"🕐 Time       : {now}\n"
        f"╚═══════════════════════════╝"
    )

    try:
        await context.bot.send_photo(chat_id=NOTIFY_CHAT_ID, photo=photo_id, caption=notif_text)
    except Exception:
        try:
            await context.bot.send_message(chat_id=NOTIFY_CHAT_ID, text=notif_text)
        except Exception:
            pass

    # Confirm to customer
    await update.message.reply_text(
        f"✅ *Order Placed Successfully!*\n\n"
        f"╔══════ ⚔️ ORDER DETAILS ══════╗\n"
        f"🆔 Order ID : `{order_id}`\n"
        f"📦 Product  : {info.get('name', code)}\n"
        f"📐 Size     : {ud['order_size']}\n"
        f"💰 Price    : Rs.{info.get('price', '?')}\n"
        f"╚══════════════════════════╝\n\n"
        f"❝ ᴛʜᴇ ᴅᴀʀᴋ ᴋɴɪɢʜᴛ ʜᴀs ʀᴇᴄᴇɪᴠᴇᴅ ʏᴏᴜʀ ᴏʀᴅᴇʀ.\n"
        f"  ʏᴏᴜ ᴡɪʟʟ ʙᴇ ɴᴏᴛɪꜰɪᴇᴅ ᴡʜᴇɴ ɪᴛ sʜɪᴘs... ❞ 🐺⚔️\n\n"
        f"📱 Questions? WhatsApp: {WHATSAPP_NUMBER}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Order cancelled. Type /start to begin again. 🐺")
    return ConversationHandler.END

# ─────────────────────────────────────────────
#  TRACK ORDER
# ─────────────────────────────────────────────
async def track_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    d = get_data()
    customer = d["customers"].get(user_id)
    if not customer or not customer.get("orders"):
        await query.edit_message_text("☠️ No orders found for your account.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]))
        return

    text = "📦 *Your Orders:*\n\n"
    for oid in customer["orders"][-5:]:
        o = d["orders"].get(oid, {})
        text += (
            f"🆔 {oid}\n"
            f"📦 {o.get('product_name','?')} ({o.get('size','?')})\n"
            f"💰 Rs.{o.get('price','?')}\n"
            f"🚦 Status: *{o.get('status','Pending')}*\n\n"
        )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]))

# ─────────────────────────────────────────────
#  CONTACT
# ─────────────────────────────────────────────
async def contact_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        f"📞 *Contact fashionstore.000*\n\n"
        f"📱 WhatsApp : {WHATSAPP_NUMBER}\n"
        f"📢 Channel  : {CHANNEL_LINK}\n"
        f"👥 Group    : {GROUP_LINK}\n"
        f"📸 Instagram: @fashionstore.000\n\n"
        f"❝ ᴛʜᴇ ᴅᴀʀᴋ ᴋɴɪɢʜᴛ ɪs ᴀʟᴡᴀʏs ʜᴇʀᴇ... ❞ 🐺⚔️"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]))

async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(DARK_WELCOME, reply_markup=main_menu_keyboard())

# ─────────────────────────────────────────────
#  ADMIN — ADD PRODUCT WITH PHOTO
# ─────────────────────────────────────────────
# Usage: send a photo with caption:
#   /addproduct L|Itachi Tshirt|299|S M L XL XXL
#   /addproduct K1|Pink Kurti|349|S M L XL
#
# Code rules:
#   L  → auto becomes L1, L2, L3... (Loot Bazar)
#   K  → auto becomes K1, K2, K3... (K Loot Bazar)
#   Or specify full code: L5, K3 etc.

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("☠️ Access denied. Dark Knight Admin only!")
        return

    if not update.message.photo:
        await update.message.reply_text(
            "📸 *How to add a product:*\n\n"
            "Send a *photo* with caption:\n"
            "`/addproduct L|Product Name|Price|S M L XL`\n\n"
            "For Loot Bazar use *L* prefix\n"
            "For K Loot Bazar use *K* prefix\n\n"
            "*Examples:*\n"
            "`/addproduct L|Itachi Tshirt|299|S M L XL XXL`\n"
            "`/addproduct K|Pink Kurti|349|S M L XL`",
            parse_mode="Markdown"
        )
        return

    caption = update.message.caption or ""
    if not caption.strip().startswith("/addproduct"):
        return  # ignore photos not meant for addproduct
    if not caption.startswith("/addproduct"):
        await update.message.reply_text("❌ Caption must start with /addproduct\nExample: `/addproduct L|Name|299|S M L XL`", parse_mode="Markdown")
        return

    try:
        parts = caption.replace("/addproduct", "").strip().split("|")
        cat_raw = parts[0].strip().upper()
        name    = parts[1].strip()
        price   = parts[2].strip()
        sizes   = parts[3].strip().split()
    except Exception:
        await update.message.reply_text("❌ Wrong format!\nUse: `/addproduct L|Name|Price|S M L XL`", parse_mode="Markdown")
        return

    products = get_products()

    # Auto-generate code
    if cat_raw in ("L", "K"):
        cat = cat_raw
        existing = [k for k in products[cat].keys()]
        nums = [int(re.sub(r"[^\d]", "", k) or 0) for k in existing]
        next_num = max(nums, default=0) + 1
        code = f"{cat}{next_num}"
    elif cat_raw.startswith("L"):
        cat = "L"
        code = cat_raw
    elif cat_raw.startswith("K"):
        cat = "K"
        code = cat_raw
    else:
        await update.message.reply_text("❌ Code must start with L (Loot Bazar) or K (K Loot Bazar)")
        return

    photo_id = update.message.photo[-1].file_id
    products[cat][code] = {"name": name, "price": price, "sizes": sizes, "photo_id": photo_id}
    save_products(products)

    collection = "🔥 Loot Bazar" if cat == "L" else "👑 K Loot Bazar"
    await update.message.reply_text(
        f"✅ *Product Added!*\n\n"
        f"🏷️ Code       : `{code}`\n"
        f"👗 Name       : {name}\n"
        f"💰 Price      : Rs.{price}\n"
        f"📐 Sizes      : {' | '.join(sizes)}\n"
        f"📂 Collection : {collection}",
        parse_mode="Markdown"
    )

async def remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/removeproduct L1`", parse_mode="Markdown")
        return
    code = args[0].upper()
    cat = "L" if code.startswith("L") else "K"
    products = get_products()
    if code in products[cat]:
        del products[cat][code]
        save_products(products)
        await update.message.reply_text(f"✅ Product `{code}` removed!", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Product `{code}` not found!", parse_mode="Markdown")

async def update_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: `/updateprice L1 349`", parse_mode="Markdown")
        return
    code = args[0].upper()
    cat = "L" if code.startswith("L") else "K"
    products = get_products()
    if code in products[cat]:
        products[cat][code]["price"] = args[1]
        save_products(products)
        await update.message.reply_text(f"✅ Price for `{code}` updated to Rs.{args[1]}", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Product `{code}` not found!")

async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    d = get_data()
    orders = d.get("orders", {})
    if not orders:
        await update.message.reply_text("📦 No orders yet!")
        return
    text = "📦 *All Orders:*\n\n"
    for oid, o in list(orders.items())[-20:]:
        text += (
            f"🆔 {oid} | {o.get('product','')} {o.get('size','')} | "
            f"Rs.{o.get('price','')} | {o.get('status','Pending')} | {o.get('name','')}\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

async def update_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: `/updatestatus ORD0001 Dispatched`", parse_mode="Markdown")
        return
    oid = args[0]
    status = " ".join(args[1:])
    d = get_data()
    if oid in d["orders"]:
        d["orders"][oid]["status"] = status
        save_data(d)
        # Notify customer
        uid = d["orders"][oid].get("user_id")
        if uid:
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=f"⚔️ *Order Update!*\n\n🆔 {oid}\n🚦 Status: *{status}*\n\n❝ ᴛʜᴇ ᴅᴀʀᴋ ᴋɴɪɢʜᴛ ᴡᴀᴛᴄʜᴇs ᴏᴠᴇʀ ʏᴏᴜʀ ᴏʀᴅᴇʀ... ❞ 🐺",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        await update.message.reply_text(f"✅ Order `{oid}` status → *{status}*", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Order `{oid}` not found!")

async def view_customers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    d = get_data()
    customers = d.get("customers", {})
    total = len(customers)
    buyers = sum(1 for c in customers.values() if c.get("orders"))
    text = (
        f"👥 *Customer Report*\n\n"
        f"Total Visitors : {total}\n"
        f"Buyers         : {buyers}\n\n"
    )
    for uid, c in list(customers.items())[-10:]:
        text += f"• {c.get('name','?')} | @{c.get('username','?')} | Visits: {c.get('visits',1)} | Orders: {len(c.get('orders',[]))}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = (
        "⚔️ *Dark Knight Admin Panel*\n\n"
        "📸 *Add Product* _(send photo with caption)_:\n"
        "`/addproduct L|Name|Price|S M L XL`\n"
        "`/addproduct K|Name|Price|S M L XL`\n\n"
        "🗑️ *Remove Product*:\n"
        "`/removeproduct L1`\n\n"
        "💰 *Update Price*:\n"
        "`/updateprice L1 349`\n\n"
        "🚦 *Update Order Status*:\n"
        "`/updatestatus ORD0001 Dispatched`\n\n"
        "📦 *View All Orders*:\n"
        "`/orders`\n\n"
        "👥 *View Customers*:\n"
        "`/customers`\n\n"
        "📂 *Collections:*\n"
        "• L prefix = 🔥 Loot Bazar (L1, L2, L3...)\n"
        "• K prefix = 👑 K Loot Bazar (K1, K2, K3...)"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def admin_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0] == ADMIN_SECRET:
        d = get_data()
        uid = update.effective_user.id
        if uid not in d["admins"]:
            d["admins"].append(uid)
            save_data(d)
        await update.message.reply_text("⚔️ *Admin access granted! Welcome, my King.* 🐺🔥\n\nType `/adminhelp` to see all commands.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Wrong secret code.")

# ─────────────────────────────────────────────
#  POST PRODUCT TO CHANNEL (admin command)
# ─────────────────────────────────────────────
async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/postchannel L1`\nPosts that product to your channel with ORDER NOW button.", parse_mode="Markdown")
        return
    code = args[0].upper()
    cat = "L" if code.startswith("L") else "K"
    products = get_products()
    info = products[cat].get(code)
    if not info:
        await update.message.reply_text(f"❌ Product `{code}` not found!")
        return

    sizes = " | ".join(info.get("sizes", []))
    collection = "🔥 Loot Bazar" if cat == "L" else "👑 K Loot Bazar"
    caption = (
        f"🩸 *NEW DROP* 🩸\n\n"
        f"👗 *{info['name']}*\n"
        f"🏷️ Code       : `{code}`\n"
        f"💰 Price      : Rs.{info['price']}\n"
        f"📐 Sizes      : {sizes}\n"
        f"📂 Collection : {collection}\n\n"
        f"❝ ᴀ ᴘɪᴇᴄᴇ ꜰɪᴛ ꜰᴏʀ ᴍʏ ᴋɪɴɢ's ᴄᴏᴜʀᴛ ❞ 🐺⚔️"
    )
    bot_username = (await context.bot.get_me()).username
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ ORDER NOW", url=f"https://t.me/{bot_username}?start=order_{code}")]
    ])

    try:
        if info.get("photo_id"):
            await context.bot.send_photo(chat_id=CHANNEL_LINK, photo=info["photo_id"], caption=caption, parse_mode="Markdown", reply_markup=kb)
        else:
            await context.bot.send_message(chat_id=CHANNEL_LINK, text=caption, parse_mode="Markdown", reply_markup=kb)
        await update.message.reply_text(f"✅ Product `{code}` posted to channel! 🔥", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not post to channel.\nMake sure bot is admin in channel!\nError: {e}")

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Order conversation
    order_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_order, pattern="^start_order$"),
            CallbackQueryHandler(start_order, pattern="^order_item_"),
        ],
        states={
            ASK_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name_received)],
            ASK_PRODUCT: [CallbackQueryHandler(product_picked, pattern="^pick_")],
            ASK_SIZE:    [CallbackQueryHandler(size_picked, pattern="^size_")],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address_received)],
            ASK_PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_received)],
            ASK_PAYMENT: [MessageHandler(filters.PHOTO, payment_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel_order)],
        per_message=False
    )

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("adminsetup", admin_setup))
    app.add_handler(CommandHandler("adminhelp", admin_help))
    app.add_handler(CommandHandler("orders", view_orders))
    app.add_handler(CommandHandler("customers", view_customers))
    app.add_handler(CommandHandler("removeproduct", remove_product))
    app.add_handler(CommandHandler("updateprice", update_price))
    app.add_handler(CommandHandler("updatestatus", update_status))
    app.add_handler(CommandHandler("postchannel", post_to_channel))

    # Add product (photo with caption)
    app.add_handler(MessageHandler(filters.PHOTO & filters.Regex(r"(?s).*"), add_product))

    # Order conversation
    app.add_handler(order_conv)

    # Callbacks
    app.add_handler(CallbackQueryHandler(browse_products, pattern="^browse$"))
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(show_product, pattern="^product_"))
    app.add_handler(CallbackQueryHandler(track_order, pattern="^track$"))
    app.add_handler(CallbackQueryHandler(contact_us, pattern="^contact$"))
    app.add_handler(CallbackQueryHandler(back_home, pattern="^back_home$"))

    # Group new member
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome))

    print("⚔️ Dark Knight Bot is running... 🐺🔥")
    app.run_polling()

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Dark Knight Bot is running!")
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    main()
