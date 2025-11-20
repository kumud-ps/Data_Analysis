#!/usr/bin/env python3
"""
Setup script for Telegram Bot
"""
import os
import subprocess
import sys

def create_telegram_bot():
    """Instructions for creating a Telegram bot."""
    print("🤖 Telegram Bot Setup for AI Email Agent")
    print("=" * 50)

    print("\n📋 Step 1: Create a Telegram Bot")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot to BotFather")
    print("3. Follow the instructions to create your bot")
    print("4. Save the bot token that BotFather gives you")

    print("\n📋 Step 2: Get your Telegram User ID")
    print("1. Open Telegram and search for @userinfobot")
    print("2. Send any message to @userinfobot")
    print("3. Save your User ID that it shows")

    print("\n📋 Step 3: Configure Environment")
    print("Add these lines to your .env file:")
    print(f"TELEGRAM_BOT_TOKEN=your_bot_token_here")
    print(f"TELEGRAM_USER_ID=your_user_id_here  # Optional: For restricted access")

    print("\n📋 Step 4: Test the Bot")
    print("1. Start your AI Email Agent API (python src/main.py)")
    print("2. Run: python telegram_bot.py")
    print("3. Open Telegram and send /start to your bot")

    print("\n🔗 Bot Commands Available:")
    print("/start - Start the bot")
    print("/help - Show help")
    print("/status - Check system status")
    print("/health - Health check")
    print("/start_monitoring [minutes] - Start monitoring")
    print("/stop_monitoring - Stop monitoring")
    print("/process_emails [limit] - Process emails")
    print("/stats - View statistics")

if __name__ == "__main__":
    create_telegram_bot()