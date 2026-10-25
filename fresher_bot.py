import os
import csv
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8815265724:AAGeM-mMfqjvhkE1X_cQLvufOzNY6uDN7NQ"
CSV_FILE = "students.csv"

# Helper function to generate a unique pass code (e.g., NITIN784)
def generate_pass_code(name):
    # Take first 3 letters of name (or full name if shorter) and add a random 3-digit number
    clean_name = ''.join(e for e in name if e.isalnum())[:3].upper()
    if not clean_name:
        clean_name = "VIP"
    rand_num = random.randint(100, 999)
    return f"{clean_name}{rand_num}"

# Helper function to save student and assign a pass code
def save_student(chat_id, name):
    file_exists = os.path.exists(CSV_FILE)
    
    # Check if student already exists
    if file_exists:
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if str(row.get('chat_id')) == str(chat_id):
                    return row.get('pass_code') # Return existing pass code if already registered

    # Generate a new unique pass code
    pass_code = generate_pass_code(name)

    # Append new student with pass code
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        fieldnames = ['chat_id', 'name', 'pass_code']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({'chat_id': chat_id, 'name': name, 'pass_code': pass_code})
    
    return pass_code

# 1. Triggered automatically when a student clicks your bot link and presses /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_user.id
    name = update.effective_user.first_name
    
    # Save them and get their unique pass code
    pass_code = save_student(chat_id, name)
    
    await update.message.reply_text(
        f"Hey **{name}**! Welcome to the Freshers' Party portal! 🎉\n\n"
        f"🎟️ Your Unique Pass Code: `{pass_code}`\n\n"
        "Stay tuned, your official broadcast invite will arrive here shortly! 🚀",
        parse_mode="Markdown"
    )

# 2. Type /broadcast in chat to send the invite (with their personal pass code) to everyone
async def broadcast_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(CSV_FILE):
        await update.message.reply_text("❌ No students registered yet! Share your bot link first.")
        return

    students = []
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            students.append(row)

    if not students:
        await update.message.reply_text("❌ No students found in the file.")
        return

    await update.message.reply_text(f"🚀 Broadcasting invite to {len(students)} registered students...")

    keyboard = [
        [
            InlineKeyboardButton("Ready! 🚀", callback_data="ready"),
            InlineKeyboardButton("Not Ready 😅", callback_data="not_ready"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    success_count = 0
    for student in students:
        name = student['name']
        chat_id = int(student['chat_id'])
        pass_code = student['pass_code']
        
        try:
            # Personalizing the message with their name AND unique pass code
            invite_text = (
                f"Hey **{name}**! 🎉 Are you ready for the ultimate Freshers' Party?\n\n"
                f"🎟️ Your Entry Pass Code: `{pass_code}`\n"
                "Keep this code safe for entry at the venue!"
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=invite_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            success_count += 1
        except Exception as e:
            print(f"Failed to send to {name}: {e}")

    await update.message.reply_text(f"✅ Sent successfully to {success_count} students!")

# 3. Handle button clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    
    if query.data == "ready":
        await query.edit_message_text(text="🎉 Status: **Ready! 🚀**\nSee you at the venue!", parse_mode="Markdown")
        
        hype_text = (
            "LET'S GOOO! 🔥💥\n\n"
            "The stage is set and the hype is real! Get your outfit sorted. "
            "More details and venue info coming your way very soon! 🪩🕺✨"
        )
        await context.bot.send_message(chat_id=chat_id, text=hype_text, parse_mode="Markdown")
        
    else:
        await query.edit_message_text(text="❌ Status: **Not Ready yet 😅**", parse_mode="Markdown")
        response_text = "Haha no worries! Get ready soon and come back! 🥳 We can't start the party without you! ⏳✨"
        await context.bot.send_message(chat_id=chat_id, text=response_text)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("broadcast", broadcast_invites))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot is live with Pass Code generator! Run /broadcast when ready.")
    app.run_polling()