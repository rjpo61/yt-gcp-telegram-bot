import asyncio
import os
import requests

from functions_framework import http
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    MessageHandler
)

# CoinGecko API endpoint to fetch cryptocurrency prices
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"

# Price mapping for different cryptocurrencies (Symbol: USD price)
CRYPTOCURRENCY_MAPPING = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'LTC': 'litecoin',
    'SOL': 'solana'
}

# Function to get crypto price in USD
async def get_crypto_price(symbol):
    crypto_id = CRYPTOCURRENCY_MAPPING.get(symbol.upper())
    if crypto_id:
        response = requests.get(COINGECKO_API, params={'ids': crypto_id, 'vs_currencies': 'usd'})
        data = response.json()
        return data[crypto_id]['usd']
    return None

# Start command handler
async def start(update: Update, context):
    # Display welcome message
    keyboard = [[InlineKeyboardButton("Enter shop 🛍️", callback_data="enter_shop")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="💎 Welcome to @GiftCardzCheap 💎\n\n"
             "The best ready-to-use gift cards on the market with a lot of happy customers and a reputable history!\n\n"
             "For support, contact: @Hytail\n\n"
             "Enter our shop and choose a product you like 🔽",
        reply_markup=reply_markup
    )

# Enter shop handler
async def enter_shop(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    # Display the list of countries/products
    keyboard = [
        [InlineKeyboardButton("🇺🇸 USA", callback_data="USA"),
         InlineKeyboardButton("🇨🇦 Canada", callback_data="Canada")],
        [InlineKeyboardButton("🇬🇧 UK", callback_data="UK"),
         InlineKeyboardButton("🇫🇷 France", callback_data="France")],
        [InlineKeyboardButton("🇳🇱 Netherlands", callback_data="Netherlands"),
         InlineKeyboardButton("🇮🇹 Italy", callback_data="Italy")],
        [InlineKeyboardButton("🇮🇳 India", callback_data="India"),
         InlineKeyboardButton("🇦🇪 UAE", callback_data="UAE")],
        [InlineKeyboardButton("🔸 Binance", callback_data="Binance"),
         InlineKeyboardButton("🅿️ PayPal", callback_data="PayPal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="Select a country to view available items:",
        reply_markup=reply_markup
    )

# Display available items based on country selected
async def display_items(update: Update, context):
    query = update.callback_query
    await query.answer()

    items = {
        "USA": [
            ("Amazon ($100)", "$35"), ("Apple ($100)", "$30"), ("Apple ($250)", "$55"),
            ("Google Play ($100)", "$35"), ("Uber Eats ($50)", "$25"), ("Steam ($100)", "$30"),
            ("PREPAID VISA ($100)", "$35"), ("PREPAID VISA ($500)", "$90")
        ],
        "Canada": [
            ("Amazon ($100)", "$30"), ("Google Play ($100)", "$30"), ("Steam ($100)", "$30"),
            ("Uber Eats ($50)", "$20")
        ],
        # Add more items for other countries here...
    }

    selected_country = query.data
    item_buttons = [
        [InlineKeyboardButton(f"{item[0]} - {item[1]}", callback_data=f"confirm_{item[0]}_{item[1]}")]
        for item in items.get(selected_country, [])
    ]

    # Add back button
    item_buttons.append([InlineKeyboardButton("↩️ Back", callback_data="enter_shop")])
    
    reply_markup = InlineKeyboardMarkup(item_buttons)

    await query.edit_message_text(
        text=f"Items available in {selected_country}:\n\nSelect an item:",
        reply_markup=reply_markup
    )

# Confirm purchase
async def confirm_purchase(update: Update, context):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_", 2)
    item_name = data[1]
    price = data[2]

    # Ask for confirmation
    keyboard = [
        [InlineKeyboardButton(f"Pay {price}", callback_data=f"pay_{item_name}_{price}")],
        [InlineKeyboardButton("↩️ Back", callback_data=f"back_to_items")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"You selected {item_name} - {price}\nProceed to checkout?",
        reply_markup=reply_markup
    )

# Proceed to payment selection
async def proceed_to_payment(update: Update, context):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_", 2)
    item_name = data[1]
    price = data[2]

    # Show payment method options
    keyboard = [
        [InlineKeyboardButton("Bitcoin", callback_data=f"pay_with_crypto_BTC_{item_name}_{price}")],
        [InlineKeyboardButton("Ethereum", callback_data=f"pay_with_crypto_ETH_{item_name}_{price}")],
        [InlineKeyboardButton("Litecoin", callback_data=f"pay_with_crypto_LTC_{item_name}_{price}")],
        [InlineKeyboardButton("Solana", callback_data=f"pay_with_crypto_SOL_{item_name}_{price}")],
        [InlineKeyboardButton("↩️ Back", callback_data=f"confirm_{item_name}_{price}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"Payment for {item_name} - {price}\nChoose your payment method:",
        reply_markup=reply_markup
    )

# Handle cryptocurrency payment
async def pay_with_crypto(update: Update, context):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_", 4)
    crypto_symbol = data[2]
    item_name = data[3]
    price_usd = data[4]

    # Get price in the chosen cryptocurrency
    crypto_price_usd = await get_crypto_price(crypto_symbol)
    if crypto_price_usd is None:
        await query.edit_message_text("Unable to fetch cryptocurrency price.")
        return

    # Calculate amount in cryptocurrency
    amount_in_crypto = round(float(price_usd) / crypto_price_usd, 6)
    
    # Payment address
    crypto_addresses = {
        'BTC': 'bc1qfvpn3ljm9ha9xfqxgjaaer4et7v4kyqylyjhh3',
        'ETH': '0x190cB0c41f495D5452AEa0A4CDE71Cb13644499e',
        'LTC': 'ltc1q7ksvkhn3hckcalwnwnd6w55j7z23crdnm56uzw',
        'SOL': '9qsPpQiWkpUHEEmuiu4YYWXe1jtpTWzt4wo1Nuum46zS'
    }
    address = crypto_addresses.get(crypto_symbol, "")

    # Display payment details
    payment_message = (
        f"ITEM: {item_name}\n"
        f"PRICE: {price_usd}\n\n"
        f"Please send: `{amount_in_crypto} {crypto_symbol}`\n\n"
        f"To the following address: \n\n"
        f"`{address}`\n\n"
        "Our bot will send you the gift card code once a payment is detected on the blockchain ✅\n\n"
        "This transaction is protected by nowpayments.io 📘"
    )

    await query.edit_message_text(payment_message)

# Main function to handle requests
@http
def telegram_bot(request):
    return asyncio.run(main(request))

async def main(request):
    token = 'YOUR_BOT_TOKEN'
    app = Application.builder().token(token).build()
    bot = app.bot

    # Add command and callback handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(enter_shop, pattern="enter_shop"))
    app.add_handler(CallbackQueryHandler(display_items, pattern="^(USA|Canada|UK|France|Netherlands|Italy|India|UAE|Binance|PayPal)$"))
    app.add_handler(CallbackQueryHandler(confirm_purchase, pattern="^confirm_"))
    app.add_handler(CallbackQueryHandler(proceed_to_payment, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(pay_with_crypto, pattern="^pay_with_crypto_"))

    if request.method == 'GET':
        await bot.set_webhook(f'https://{request.host}/telegram_bot')
        return "webhook set"

    # Handle the incoming update
    update = Update.de_json(request.json, bot)
    await app.process_update(update)

    return "ok"
