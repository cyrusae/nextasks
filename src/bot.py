"""
Nextcloud Tasks Discord Bot - v0.1 MVP

Features:
- /task add <title> - Create task due today at 11:59 PM
- /task list - Show today's incomplete tasks
- /task complete <id> - Mark task complete by ID

Usage:
    python src/bot.py

Environment Variables Required:
    DISCORD_TOKEN - Your Discord bot token
    NEXTCLOUD_URL - Your Nextcloud base URL (e.g., https://nextcloud.dawnfire.casa)
    NEXTCLOUD_USER - Nextcloud username (e.g., taskbot)
    NEXTCLOUD_PASSWORD - Nextcloud app password
"""

import os
import logging
import asyncio
from datetime import datetime, time
from typing import Optional, List, Dict

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from caldav_client import NextcloudTasksClient, Task

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
NEXTCLOUD_URL = os.getenv('NEXTCLOUD_URL')
NEXTCLOUD_USER = os.getenv('NEXTCLOUD_USER')
NEXTCLOUD_PASSWORD = os.getenv('NEXTCLOUD_PASSWORD')

# Validate required environment variables
if not all([DISCORD_TOKEN, NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD]):
    raise ValueError(
        "Missing required environment variables. Please set:\n"
        "  DISCORD_TOKEN\n"
        "  NEXTCLOUD_URL\n"
        "  NEXTCLOUD_USER\n"
        "  NEXTCLOUD_PASSWORD"
    )


class TaskBot(commands.Bot):
    """Discord bot for managing Nextcloud tasks."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Required for DM handling in v1.1
        
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize Nextcloud client
        self.tasks_client = NextcloudTasksClient(
            url=NEXTCLOUD_URL,
            username=NEXTCLOUD_USER,
            password=NEXTCLOUD_PASSWORD
        )
        
        # Cache for task ID mapping (task number -> CalDAV UID)
        # This will be per-user in v2.0, for now it's global
        self.task_cache: Dict[int, str] = {}
        
    async def setup_hook(self):
        """Called when bot is starting up. Sync slash commands."""
        logger.info("Setting up bot...")
        
        # Verify Nextcloud connection
        try:
            await asyncio.to_thread(self.tasks_client.test_connection)
            logger.info("✅ Connected to Nextcloud successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Nextcloud: {e}")
            raise
        
        # Sync slash commands
        await self.tree.sync()
        logger.info("✅ Slash commands synced")
    
    async def on_ready(self):
        """Called when bot is fully ready."""
        logger.info(f'🤖 Logged in as {self.user} (ID: {self.user.id})')
        logger.info(f'📡 Connected to {len(self.guilds)} server(s)')
        logger.info('🎉 Bot is ready!')


# Create bot instance
bot = TaskBot()


@bot.tree.command(name="task-add", description="Add a new task (due today at 11:59 PM)")
@app_commands.describe(title="What needs to be done?")
async def task_add(interaction: discord.Interaction, title: str):
    """Add a new task to Nextcloud."""
    await interaction.response.defer(thinking=True)
    
    try:
        # Create task with due date of today at 11:59 PM
        today = datetime.now().date()
        due_datetime = datetime.combine(today, time(23, 59))
        
        logger.info(f"Creating task: '{title}' due {due_datetime}")
        
        # Create task via CalDAV (runs in thread to avoid blocking)
        task = await asyncio.to_thread(
            bot.tasks_client.create_task,
            title=title,
            due=due_datetime
        )
        
        # Send confirmation
        embed = discord.Embed(
            title="✅ Task Created",
            description=f"**{title}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Due", value="Today at 11:59 PM", inline=True)
        embed.add_field(name="Status", value="📝 To Do", inline=True)
        embed.set_footer(text="Use /task-list to see all tasks")
        
        await interaction.followup.send(embed=embed)
        logger.info(f"✅ Task created: {task.uid}")
        
    except Exception as e:
        logger.error(f"❌ Failed to create task: {e}", exc_info=True)
        await interaction.followup.send(
            f"❌ Failed to create task: {str(e)}",
            ephemeral=True
        )


@bot.tree.command(name="task-list", description="List today's tasks")
async def task_list(interaction: discord.Interaction):
    """List all tasks due today."""
    await interaction.response.defer(thinking=True)
    
    try:
        logger.info("Fetching today's tasks...")
        
        # Fetch tasks from Nextcloud
        tasks = await asyncio.to_thread(bot.tasks_client.get_tasks_due_today)
        
        if not tasks:
            embed = discord.Embed(
                title="📋 Today's Tasks",
                description="No tasks for today! 🎉",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Filter to incomplete tasks only (v0.1 doesn't show completed)
        incomplete_tasks = [t for t in tasks if not t.completed]
        
        # Update task cache for completion command
        bot.task_cache.clear()
        for idx, task in enumerate(incomplete_tasks, 1):
            bot.task_cache[idx] = task.uid
        
        # Build embed
        embed = discord.Embed(
            title="📋 Today's Tasks",
            description=f"You have {len(incomplete_tasks)} task(s) to complete",
            color=discord.Color.blue()
        )
        
        for idx, task in enumerate(incomplete_tasks, 1):
            due_str = task.due.strftime("%I:%M %p") if task.due else "No time set"
            embed.add_field(
                name=f"{idx}. {task.title}",
                value=f"Due: {due_str}",
                inline=False
            )
        
        embed.set_footer(text="Use /task-complete <number> to mark tasks done")
        
        await interaction.followup.send(embed=embed)
        logger.info(f"✅ Listed {len(incomplete_tasks)} tasks")
        
    except Exception as e:
        logger.error(f"❌ Failed to list tasks: {e}", exc_info=True)
        await interaction.followup.send(
            f"❌ Failed to list tasks: {str(e)}",
            ephemeral=True
        )


@bot.tree.command(name="task-complete", description="Mark a task as complete")
@app_commands.describe(task_id="Task number from /task-list")
async def task_complete(interaction: discord.Interaction, task_id: int):
    """Mark a task as complete."""
    await interaction.response.defer(thinking=True)
    
    try:
        # Validate task ID
        if task_id not in bot.task_cache:
            await interaction.followup.send(
                f"❌ Invalid task number: {task_id}\n"
                f"Use /task-list to see current task numbers.",
                ephemeral=True
            )
            return
        
        # Get CalDAV UID from cache
        task_uid = bot.task_cache[task_id]
        
        logger.info(f"Completing task {task_id} (UID: {task_uid})")
        
        # Mark complete via CalDAV
        task_title = await asyncio.to_thread(
            bot.tasks_client.complete_task,
            uid=task_uid
        )
        
        # Send celebration
        embed = discord.Embed(
            title="✅ Task Completed!",
            description=f"~~{task_title}~~",
            color=discord.Color.green()
        )
        embed.set_footer(text="Great job! 🎉")
        
        await interaction.followup.send(embed=embed)
        logger.info(f"✅ Task completed: {task_uid}")
        
        # Remove from cache
        del bot.task_cache[task_id]
        
    except Exception as e:
        logger.error(f"❌ Failed to complete task: {e}", exc_info=True)
        await interaction.followup.send(
            f"❌ Failed to complete task: {str(e)}",
            ephemeral=True
        )


@bot.tree.command(name="task-help", description="Show help for task commands")
async def task_help(interaction: discord.Interaction):
    """Display help information."""
    embed = discord.Embed(
        title="📖 Task Bot Help - v0.1 MVP",
        description="Manage your Nextcloud tasks from Discord!",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="/task-add <title>",
        value="Create a new task due today at 11:59 PM\nExample: `/task-add Buy groceries`",
        inline=False
    )
    
    embed.add_field(
        name="/task-list",
        value="Show all incomplete tasks due today",
        inline=False
    )
    
    embed.add_field(
        name="/task-complete <number>",
        value="Mark a task as complete\nExample: `/task-complete 1`",
        inline=False
    )
    
    embed.set_footer(text="More features coming in v1.0!")
    
    await interaction.response.send_message(embed=embed)


def main():
    """Main entry point."""
    try:
        logger.info("🚀 Starting Nextcloud Tasks Bot v0.1...")
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()