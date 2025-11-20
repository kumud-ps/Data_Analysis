#!/usr/bin/env python3
"""
Telegram Bot for controlling AI Email Agent
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests

# Configuration
API_BASE_URL = "http://localhost:8000"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramEmailBot:
    """Telegram bot for AI Email Agent control."""

    def __init__(self, token: str, api_url: str = API_BASE_URL):
        """Initialize the Telegram bot."""
        self.token = token
        self.api_url = api_url
        self.application = Application.builder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Setup Telegram bot command handlers."""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("start_monitoring", self.start_monitoring_command))
        self.application.add_handler(CommandHandler("stop_monitoring", self.stop_monitoring_command))
        self.application.add_handler(CommandHandler("process_emails", self.process_emails_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("health", self.health_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

    async def api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make API request with error handling."""
        try:
            url = f"{self.api_url}{endpoint}"

            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            else:
                return {"error": f"Unsupported method: {method}"}

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}"}

        except Exception as e:
            return {"error": f"Connection error: {str(e)}"}

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """
🤖 **AI Email Agent Bot**

Welcome! I can help you control your AI Email Agent through Telegram.

📋 **Available Commands:**
/status - Check system status
/health - Health check
/start_monitoring - Start email monitoring
/stop_monitoring - Stop email monitoring
/process_emails - Process emails manually
/stats - View statistics
/help - Show this help message

Use the buttons below for quick actions!
        """

        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("❤️ Health", callback_data="health")
            ],
            [
                InlineKeyboardButton("▶️ Start Monitoring", callback_data="start_monitoring"),
                InlineKeyboardButton("⏹️ Stop Monitoring", callback_data="stop_monitoring")
            ],
            [
                InlineKeyboardButton("🔄 Process Emails", callback_data="process_emails"),
                InlineKeyboardButton("📈 Stats", callback_data="stats")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
🤖 **AI Email Agent Bot - Help**

**📋 Commands:**
• `/status` - Current monitoring status
• `/health` - System health check
• `/start_monitoring [minutes]` - Start email monitoring (default: 5 minutes)
• `/stop_monitoring` - Stop email monitoring
• `/process_emails [limit]` - Process emails manually (default: 10)
• `/stats` - Processing statistics
• `/health` - Health check

**🔘 Buttons:**
Use the inline buttons for quick access to common actions.

**⚠️ Important:**
• Make sure the AI Email Agent API is running on localhost:8000
• You need to configure your Gmail credentials in .env file
• Ollama service must be running for AI responses

Need help? Check the logs or visit the web dashboard!
        """

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        await self.send_status(update.message)

    async def health_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /health command."""
        await update.message.reply_text("🔍 Checking system health...")

        health = await self.api_request("/health")

        if "error" in health:
            await update.message.reply_text(f"❌ Health check failed: {health['error']}")
            return

        status_emoji = "✅" if health.get("status") == "healthy" else "❌"
        health_text = f"""
{status_emoji} **System Health**

**Status:** {health.get('status', 'Unknown').upper()}
**Timestamp:** {health.get('timestamp', 'Unknown')}

**Details:**
{self.format_health_details(health.get('details', {}))}
        """

        await update.message.reply_text(health_text, parse_mode='Markdown')

    async def start_monitoring_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start_monitoring command."""
        # Parse interval from command args
        interval = 5  # default
        if context.args and len(context.args) > 0:
            try:
                interval = int(context.args[0])
                if interval < 1 or interval > 60:
                    interval = 5
            except ValueError:
                interval = 5

        await update.message.reply_text(f"🚀 Starting email monitoring with {interval} minute intervals...")

        result = await self.api_request(f"/monitoring/start?interval_minutes={interval}", "POST")

        if "error" in result:
            await update.message.reply_text(f"❌ Failed to start monitoring: {result.get('message', 'Unknown error')}")
        else:
            await update.message.reply_text(f"✅ Monitoring started successfully! Checking emails every {interval} minutes.")

    async def stop_monitoring_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop_monitoring command."""
        await update.message.reply_text("⏹️ Stopping email monitoring...")

        result = await self.api_request("/monitoring/stop", "POST")

        if "error" in result:
            await update.message.reply_text(f"❌ Failed to stop monitoring: {result.get('message', 'Unknown error')}")
        else:
            await update.message.reply_text("✅ Monitoring stopped successfully!")

    async def process_emails_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /process_emails command."""
        # Parse limit from command args
        limit = 10  # default
        if context.args and len(context.args) > 0:
            try:
                limit = int(context.args[0])
                if limit < 1 or limit > 50:
                    limit = 10
            except ValueError:
                limit = 10

        await update.message.reply_text(f"🔄 Processing {limit} emails...")

        result = await self.api_request("/emails/process", "POST", {"limit": limit})

        if "error" in result:
            await update.message.reply_text(f"❌ Failed to process emails: {result.get('message', 'Unknown error')}")
        else:
            processed = result.get('processed', 0)
            responded = result.get('responded', 0)
            skipped = result.get('skipped', 0)
            errors = result.get('errors', 0)

            process_text = f"""
📊 **Email Processing Complete**

**Processed:** {processed} emails
**Responded:** {responded} emails
**Skipped:** {skipped} emails
**Errors:** {errors} emails
**Time:** {result.get('processing_time', 0):.2f} seconds
            """

            await update.message.reply_text(process_text, parse_mode='Markdown')

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        await update.message.reply_text("📈 Fetching statistics...")

        stats = await self.api_request("/stats")

        if "error" in stats:
            await update.message.reply_text(f"❌ Failed to get statistics: {stats['error']}")
            return

        stats_data = stats.get('stats', {})

        stats_text = f"""
📊 **Processing Statistics**

**Total Processed:** {stats_data.get('total_processed', 0):,}
**Successful Responses:** {stats_data.get('successful_responses', 0):,}
**Failed Responses:** {stats_data.get('failed_responses', 0):,}
**Skipped Emails:** {stats_data.get('skipped_emails', 0):,}
**Errors:** {stats_data.get('errors', 0):,}

**Success Rate:** {self.calculate_success_rate(stats_data):.1f}%
        """

        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()

        action = query.data

        if action == "status":
            await self.send_status(query.message)
        elif action == "health":
            await self.send_health(query.message)
        elif action == "start_monitoring":
            await self.start_monitoring_command(update, context)
        elif action == "stop_monitoring":
            await self.stop_monitoring_command(update, context)
        elif action == "process_emails":
            await self.process_emails_command(update, context)
        elif action == "stats":
            await self.stats_command(update, context)

    async def send_status(self, message):
        """Send status message."""
        await message.reply_text("📊 Fetching status...")

        status = await self.api_request("/status")

        if "error" in status:
            await message.reply_text(f"❌ Failed to get status: {status['error']}")
            return

        is_monitoring = status.get('monitoring_active', False)
        last_check = status.get('last_check_time')
        next_check = status.get('next_check_time')
        stats = status.get('processing_stats', {})

        monitoring_emoji = "🟢" if is_monitoring else "🔴"
        monitoring_text = "Running" if is_monitoring else "Stopped"

        status_text = f"""
{monitoring_emoji} **System Status**

**Monitoring:** {monitoring_text}
**Last Check:** {self.format_datetime(last_check) or 'Never'}
**Next Check:** {self.format_datetime(next_check) or 'N/A'}

**Statistics:**
**Total Processed:** {stats.get('total_processed', 0):,}
**Successful:** {stats.get('successful_responses', 0):,}
**Failed:** {stats.get('failed_responses', 0):,}
        """

        await message.reply_text(status_text, parse_mode='Markdown')

    async def send_health(self, message):
        """Send health message."""
        await message.reply_text("🔍 Checking system health...")

        health = await self.api_request("/health")

        if "error" in health:
            await message.reply_text(f"❌ Health check failed: {health['error']}")
            return

        status_emoji = "✅" if health.get("status") == "healthy" else "❌"
        health_text = f"""
{status_emoji} **System Health**

**Status:** {health.get('status', 'Unknown').upper()}
**Timestamp:** {health.get('timestamp', 'Unknown')}

**Details:**
{self.format_health_details(health.get('details', {}))}
        """

        await message.reply_text(health_text, parse_mode='Markdown')

    def format_datetime(self, dt_str: str) -> str:
        """Format datetime string for display."""
        if not dt_str:
            return None

        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return dt_str

    def format_health_details(self, details: Dict) -> str:
        """Format health details for display."""
        if not details:
            return "No details available"

        formatted = []
        if 'monitoring_active' in details:
            status = "✅ Active" if details['monitoring_active'] else "❌ Inactive"
            formatted.append(f"• Monitoring: {status}")

        if 'scheduler_status' in details:
            formatted.append(f"• Scheduler: {details['scheduler_status']}")

        if 'email_processor_status' in details:
            formatted.append(f"• Email Processor: {details['email_processor_status']}")

        if 'time_since_last_check' in details:
            formatted.append(f"• Time Since Last Check: {details['time_since_last_check']}")

        if 'overall_health' in details:
            health_status = "✅ Healthy" if details['overall_health'] else "❌ Unhealthy"
            formatted.append(f"• Overall: {health_status}")

        return "\n".join(formatted) if formatted else "No details available"

    def calculate_success_rate(self, stats: Dict) -> float:
        """Calculate success rate percentage."""
        total = stats.get('total_processed', 0)
        successful = stats.get('successful_responses', 0)

        if total == 0:
            return 0.0

        return (successful / total) * 100

    def run(self):
        """Run the Telegram bot."""
        logger.info("Starting AI Email Agent Telegram Bot")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main function to run the Telegram bot."""
    import os

    # Get bot token from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
        print("Please set your Telegram bot token:")
        print("export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        return

    # Create and run bot
    bot = TelegramEmailBot(bot_token)
    bot.run()


if __name__ == "__main__":
    main()