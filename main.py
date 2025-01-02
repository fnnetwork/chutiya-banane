import telebot
from telebot import types
import random
import string
import logging
import time

# Define your bot token here
BOT_TOKEN = '7585534673:AAFKF_PB2mY62v6Y-0J1j3m3w0VmEiP70Lk'
bot = telebot.TeleBot(BOT_TOKEN)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants and Data Structures
order_messages = {}  # To track orders
user_data = {}  # User data storage
total_users = set()  # Track unique users
CHANNELS = [
    {"name": "CN NETWORK", "username": "@cnxnetworks"},
    {"name": "Abir X Official", "username": "@abir_x_official"},
    {"name": "Payment", "username": "@tgpreniumpay"}
]
FORWARD_GROUPS = [-1002308247260, -1002259798284]  # Replace with real group IDs
REVIEW_CHANNEL_ID = -1002308247260  # Replace with the review channel ID
# List of admin user IDs
ADMIN_IDS = [7303810912, 7271198694]  # Replace with actual admin IDs
# Add a dictionary to track referred users
referred_users = {}  # Key: referred_user_id, Value: referrer_id
# Subscription Options
options = {
    "Telegram Premium - 3 Months": {"cost": 50},
    "Telegram Premium - 6 Months": {"cost": 80},
}

# Helper Functions
def generate_order_id():
    """Generate a unique order ID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def get_main_menu_keyboard():
    """Return the main menu keyboard."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("💰 Balance", "👥 Referral", "💲 Withdraw")
    keyboard.row("👥 Submit Review", "📂 PROOFS", "📞 Support")
    keyboard.row("📊 Statistics", "💪🏻 LeaderBoard", "☑️ Update")
    return keyboard

def check_channel_subscription(user_id):
    """Check if the user has joined all required channels."""
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel["username"], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logging.error(f"Error checking channel {channel['username']} for user {user_id}: {e}")
            return False
    return True

@bot.message_handler(commands=['start'])
def start(message):
    """Handle the /start command."""
    try:
        user_id = message.from_user.id
        total_users.add(user_id)  # Track unique users

        # Extract the referrer ID if available
        referrer_id = int(message.text.split()[1]) if len(message.text.split()) > 1 else None

        # Register user if not already registered
        if user_id not in user_data:
            user_data[user_id] = {
                'balance': 0,
                'invited_users': 0,
                'bonus_claimed': False,
                'referred_by': None
            }

        # Process referral if the user is new and has a referrer
        if referrer_id and referrer_id != user_id:
            if user_id not in referred_users:  # Check if user has not been referred already
                referred_users[user_id] = referrer_id  # Mark this user as referred by referrer_id
                user_data[user_id]['referred_by'] = referrer_id
                bot.send_message(
                    referrer_id,
                    f"🎉 Referral received! Your invitee {message.from_user.first_name} must complete tasks to earn you points."
                )
            else:
                # Inform the referrer but take no further action
                bot.send_message(referrer_id, "❌ This user has already been referred. No points will be added.")
        elif referrer_id == user_id:
            bot.send_message(user_id, "❌ You cannot refer yourself!")

        # Send welcome message to the referred user
        message_text = (
            "<b>🟢 Welcome to Our Telegram Premium Subscription Bot</b>\n"
            "---------------------------------------\n"
        )
        for channel in CHANNELS:
            message_text += f"🔹 <a href='https://t.me/{channel['username'][1:]}'>{channel['name']}</a>\n"
        message_text += (
            "---------------------------------------\n\n"
            "✅ After completing all tasks, click on ✅ <b>Joined!</b>"
        )
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("✅ Joined", callback_data="joined"))

        # Send message with link preview disabled
        bot.send_message(user_id, message_text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Error in start handler: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "joined")
def joined_button(call):
    """Handle the Joined button."""
    try:
        user_id = call.from_user.id

        # Check if the user has joined all channels
        if check_channel_subscription(user_id):
            referrer_id = referred_users.get(user_id)  # Get the referrer ID from referred_users dictionary

            # Credit the referrer only if:
            # 1. Referrer exists.
            # 2. The referred user has not already been rewarded.
            if referrer_id and 'rewarded' not in user_data[user_id]:
                user_data[referrer_id]['balance'] += 1  # Add points to referrer
                user_data[referrer_id]['invited_users'] += 1
                user_data[user_id]['rewarded'] = True  # Mark referred user as rewarded
                bot.send_message(
                    referrer_id,
                    f"🎉 {call.from_user.first_name} joined all channels. You earned 1 point!"
                )

            bot.send_message(
                user_id,
                "🎉 Thank you for joining! You may now use the bot.",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined all required channels!")
    except Exception as e:
        logging.error(f"Error in joined_button handler: {e}")
@bot.message_handler(commands=['send'])
def send_broadcast(message):
    """Allow admins to broadcast messages to all users."""
    try:
        user_id = message.from_user.id

        # Check if the user is an admin
        if user_id not in ADMIN_IDS:
            bot.reply_to(message, "❌ You are not authorized to use this command.")
            return

        # Extract the message to broadcast
        broadcast_message = message.text.partition(" ")[2].strip()
        if not broadcast_message:
            bot.reply_to(message, "❌ Please provide a message to broadcast. Example: /send Hello users!")
            return

        # Broadcast the message
        successful = 0
        failed = 0

        for target_user_id in user_data.keys():
            try:
                bot.send_message(target_user_id, broadcast_message, parse_mode="HTML")
                successful += 1
            except Exception as e:
                logging.error(f"Failed to send message to {target_user_id}: {e}")
                failed += 1

        # Send a summary to the admin
        bot.reply_to(message, f"✅ Broadcast completed!\n\nSuccessful: {successful}\nFailed: {failed}")

    except Exception as e:
        logging.error(f"Error in send_broadcast handler: {e}")
        bot.reply_to(message, "❌ An error occurred while broadcasting the message.")
# Other Handlers (Balance, Referral, Withdraw, Reviews)
@bot.message_handler(func=lambda message: message.text == "💰 Balance")
def balance(message):
    user_id = message.from_user.id
    points = user_data.get(user_id, {}).get("balance", 0)
    bot.send_message(message.chat.id, f"💰 Your Balance: {points} POINTS\nRefer more to earn!", parse_mode="HTML")
            
@bot.message_handler(func=lambda message: message.text == "👥 Referral")
def referral(message):
    user_id = message.from_user.id
    referral_link = f"https://t.me/Tgxpremiumsbot?start={user_id}"
    invited_users = user_data.get(user_id, {}).get('invited_users', 0)
    bot.send_message(message.chat.id, f"👬 Your Invite Link: {referral_link}\nInvited Users: {invited_users}")
@bot.callback_query_handler(func=lambda call: call.data == "💪🏻 LeaderBoard")
def leaderboard_button(call):
    """Handle the Leaderboard button."""
    try:
        # Extract user points
        leaderboard = [
            (user_id, user_info['balance'])
            for user_id, user_info in user_data.items()
        ]
        
        # Sort by points in descending order
        leaderboard = sorted(leaderboard, key=lambda x: x[1], reverse=True)[:10]

        # Generate leaderboard message
        message_text = "<b>🏆 Top 10 Users Leaderboard 🏆</b>\n\n"
        for rank, (user_id, points) in enumerate(leaderboard, start=1):
            user = bot.get_chat(user_id)
            username = user.username or user.first_name or "Unknown"
            message_text += f"{rank}. @{username} - {points} points\n"

        # Send leaderboard message
        bot.send_message(call.from_user.id, message_text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error in leaderboard_button handler: {e}")
        bot.send_message(call.from_user.id, "❌ Unable to fetch leaderboard at this time.")

@bot.message_handler(func=lambda message: message.text == "📞 Support")
def support(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Message Admin", url="https://t.me/CnxCEO"))
    bot.send_message(message.chat.id, "If you have a major problem, you can directly contact the owner - @@CnxCEO", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "📂 PROOFS")
def proofs(message):
    bot.send_message(message.chat.id, "<b>📂 Join: @tgpreniumpay To Check Proofs 🥳</b>", parse_mode="HTML")
@bot.message_handler(func=lambda message: message.text == "☑️ Update")
def update_bot(message):
    user_id = message.chat.id

    # Step 1: Send the initial updating message
    updating_message = bot.send_message(user_id, "Bro Updating Telegram Premium ☑️ Bot..........")

    # Step 2: Simulate progress bar animation
    for i in range(0, 101, 10):  # Increment by 10 for smoother animation
        progress_bar = f"[{'█' * (i // 10)}{' ' * (10 - i // 10)}] {i}%"
        bot.edit_message_text(
            chat_id=user_id,
            message_id=updating_message.message_id,
            text=f"Bro Updating Telegram Premium ☑️ Bot..........\n{progress_bar}"
        )
        time.sleep(0.2)  # Adjust sleep time for a 2-second total animation

    # Step 3: Delete the progress bar message
    bot.delete_message(chat_id=user_id, message_id=updating_message.message_id)

    # Step 4: Send the final update message
    bot.send_message(
        user_id,
        "Hey Bro Bot Updated To Supreme 💎\nTo Check Use /start Command ☑️",
        parse_mode="HTML"
    )
@bot.message_handler(func=lambda message: message.text == "📊 Statistics")
def show_statistics(message):
    user_id = message.chat.id
    total_users_count = len(total_users)  # Get the count of unique users
    bot.send_message(
        user_id,
        f"📊 Bot Statistics:\n\n👥 Total Users: {total_users_count}",
        parse_mode="HTML"
    )

# Escape reserved MarkdownV2 characters
def escape_markdown(text, version="MarkdownV2"):
    """
    Escapes reserved characters for MarkdownV2 or Markdown.
    """
    if version == "MarkdownV2":
        reserved_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    else:  # For regular Markdown
        reserved_chars = ['_', '*', '[', ']', '(', ')', '~', '`']
    for char in reserved_chars:
        text = text.replace(char, f"\\{char}")
    return text

@bot.message_handler(func=lambda message: message.text == "💲 Withdraw")
def withdraw(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # First row: 2 buttons
    keyboard.row("Telegram Premium - 3 Months", "Telegram Premium - 6 Months")
    # Third row: 1 button (Back button)
    keyboard.row("🔙 Back")
    bot.send_message(message.chat.id, "Please choose one of the withdrawal options below:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == "🔙 Back")
def go_back_to_main_menu(message):
    bot.send_message(message.chat.id, "Returning to the main menu.", reply_markup=get_main_menu_keyboard())


@bot.message_handler(func=lambda message: message.text in options.keys())
def confirm_withdrawal(message):
    option = message.text
    cost = options[option]["cost"]
    message_text = f"Would you like to withdraw {option}? This will cost {cost} points."

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Confirm", callback_data=f"confirm_{option}"))
    keyboard.add(types.InlineKeyboardButton("Cancel", callback_data="cancel"))

    bot.send_message(message.chat.id, message_text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_") or call.data == "cancel")
def handle_confirm_or_cancel(call):
    user_id = call.from_user.id
    action = call.data.split("_")[0]
    option = call.data.split("_")[1] if action == "confirm" else None

    if action == "confirm":
        cost = options[option]["cost"]
        # Check user balance
        if user_data.get(user_id, {}).get("balance", 0) >= cost:
            user_data[user_id]["balance"] -= cost

            # Notify user
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ Your withdrawal for {option} has been confirmed. {cost} points deducted."
            )

            # Generate order ID and prepare message
            order_id = generate_order_id()
            message_text = escape_markdown(
                f"✅ *New Order Received*\n\n"
                f"🔰 *Service:* {option}\n"
                f"👤 *User:* {call.from_user.full_name}\n"
                f"🆔 *User ID:* {user_id}\n"
                f"📛 *Order ID:* [{order_id}]\n"
                f"🔗 *Profile Link:* Hidden\n\n"
                f"🚀 *Subscribe to Telegram Premium ➡️* @Tgxpremiumsbot"
            )

            # Forward message to groups
            for group_id in FORWARD_GROUPS:
                order_msg = bot.send_message(group_id, message_text, parse_mode="MarkdownV2")
                order_messages[order_msg.message_id] = user_id
        else:
            # Not enough points
            bot.answer_callback_query(call.id, "❌ You don't have enough points to make this withdrawal.")
    elif action == "cancel":
        # Handle cancellation
        bot.send_message(user_id, "Withdrawal request has been canceled.", reply_markup=get_main_menu_keyboard())


@bot.message_handler(func=lambda message: message.reply_to_message and message.reply_to_message.message_id in order_messages)
def handle_admin_reply(message):
    original_user_id = order_messages[message.reply_to_message.message_id]
    admin_reply = escape_markdown(message.text)

    # Notify the original user
    bot.send_message(
        chat_id=original_user_id,
        text=f"📩 *Reply from Admin:*\n{admin_reply}",
        parse_mode="MarkdownV2"
    )

    # Notify the group of the reply being sent
    bot.send_message(
        chat_id=message.chat.id,
        text=escape_markdown(f"✅ Reply has been sent to the user (User ID: {original_user_id})."),
        parse_mode="MarkdownV2"
    )

def generate_order_id():
    """
    Mock function to generate a unique order ID.
    Replace with your implementation as needed.
    """
    from random import randint
    return f"ORD-{randint(1000, 9999)}"

# <b>Review Submission</b>
@bot.message_handler(func=lambda message: message.text == "👥 Submit Review")
def submit_review(message):
    user_id = message.from_user.id
    # <b>Flag user for review submission</b>
    user_data.setdefault(user_id, {})["awaiting_review"] = True
    bot.send_message(
        user_id,
        "Please send your screenshot and review of our service. Failure to do so may result in a password change for the account."
    )

@bot.message_handler(content_types=['photo', 'text'])
def handle_review_submission(message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_data.setdefault(user_id, {})  # <b>Ensure user data exists for the user</b>
    is_waiting_for_review = user_data[user_id].get("awaiting_review", False)

    if is_waiting_for_review:
        try:
            if message.photo:
                # <b>Handle photo reviews</b>
                caption = message.caption or "No text provided."
                photo = message.photo[-1].file_id
                bot.send_photo(
                    REVIEW_CHANNEL_ID,
                    photo=photo,
                    caption=f"👤 User: {user_name} (ID: {user_id})\n\n📄 Review: {caption}",
                    parse_mode="Markdown"
                )
            elif message.text:
                # <b>Handle text reviews</b>
                bot.send_message(
                    REVIEW_CHANNEL_ID,
                    text=f"👤 User: {user_name} (ID: {user_id})\n\n📄 Review: {message.text}",
                    parse_mode="Markdown"
                )
            # <b>Mark review as submitted</b>
            user_data[user_id]["awaiting_review"] = False
            bot.send_message(user_id, "Thank you for your review!")
        except Exception as e:
            logging.error(f"Error in handle_review_submission: {e}")

# <b>Polling Loop</b>
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Polling Error: {e}")
        time.sleep(5)
