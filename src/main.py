# This file is part of DisMu.
#
# DisMu is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DisMu is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DisMu. If not, see <https://www.gnu.org/licenses/>.

import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from src.utility.helpers import send_and_delete

os.environ["FFMPEG_LOGLEVEL"] = "quiet"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('main')
load_dotenv()

# HTTP headers for YouTube requests to avoid bot detection
common_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.youtube.com/'
}
header_str = "".join([f"{k}: {v}\\r\\n" for k, v in common_headers.items()])

# Discord bot configuration
intents = discord.Intents.default()
intents.message_content = True # Required for reading message content in Discord API v10+
default_prefix = os.getenv('DEFAULT_PREFIX') or '%'
help_command = commands.DefaultHelpCommand(no_category='Other Commands')
bot = commands.Bot(command_prefix=default_prefix, intents=intents, help_command=help_command)
bot.default_delete_time = int(os.getenv('DEFAULT_DELETE_TIME') or '15')
bot.default_prefix = default_prefix
bot.embed_autodelete = int(os.getenv('EMBED_AUTODELETE') or '60')
bot.guild_settings = {}  # {guild_id: {'volume': float, 'loop': bool, 'currently_playing': (title, url), 'song_queue': deque}}
bot.search_timeout = int(os.getenv('SEARCH_TIMEOUT') or '60')

# FFmpeg options for reliable audio streaming with error suppression
bot.before_opts = (
    f"-loglevel error " # Suppress verbose FFmpeg output
    f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 " # Auto-reconnect on stream failures
    f"-headers \"{header_str.strip()}\"" # Include HTTP headers for YouTube requests
)

# yt-dlp configuration for single track extraction
bot.ydl_opts_single = {
    'format': 'bestaudio/best',  # Prefer best audio quality
    'noplaylist': True,  # Extract only single video, not entire playlist
    'quiet': True,  # Suppress yt-dlp output
    'socket_timeout': 15,  # Connection timeout in seconds
    'retries': 3,  # Number of retry attempts on failure
    'no_warnings': True,  # Suppress warning messages
    'http_headers': common_headers,  # Use custom headers to avoid detection
    'postprocessor_args': ['-loglevel', 'error']  # Suppress post-processing output
}

# yt-dlp configuration for playlist processing (metadata only)
bot.ydl_opts_playlist = {
    'format': 'bestaudio/best',  # Audio format preference
    'quiet': True,  # Suppress output
    'extract_flat': True,  # Extract metadata only, don't download
    'no_warnings': True,  # Suppress warnings
    'http_headers': common_headers,  # Custom headers
    'postprocessor_args': ['-loglevel', 'error']  # Suppress post-processing output
}


@bot.listen("on_command")
async def log_command(ctx):
    """
    Logs all commands executed by users across all guilds.

    Captures and logs information about each command invocation including
    the command name, user who executed it, and the guild where it was used.
    Handles both guild and direct message contexts appropriately.

    Args:
        ctx: The command context containing command and user information.
    """
    logger.info(f"Command received: {ctx.command} from {ctx.author} in {ctx.guild.name if ctx.guild else 'DMs'}")


@bot.event
async def on_command_error(ctx, error):
    """
    Global error handler for all command execution errors.

    Handles common command errors gracefully by providing user-friendly
    error messages. Specifically handles missing required arguments and
    logs detailed error information for debugging. Sends temporary error
    messages that auto-delete to keep channels clean.

    Args:
        ctx: The command context where the error occurred.
        error: The exception that was raised during command execution.
    """
    if isinstance(error, commands.MissingRequiredArgument):
        await send_and_delete(ctx, f"Missing argument: {error.param.name}. Please provide it!", bot.default_delete_time)
        logger.warning(f"Missing argument for command {ctx.command}: {error.param.name}")
    else:
        await send_and_delete(ctx, "An error occurred while processing the command.", bot.default_delete_time)
        logger.error(f"Unhandled error in command {ctx.command}: {error}")


async def main():
    """
    Main entry point for the Discord music bot.

    Initializes the bot, loads all music-related cogs (main, queue, control),
    and starts the bot connection to Discord. Logs configuration information
    including prefix, timeouts, and auto-delete settings. Handles cog loading
    errors and ensures proper bot startup sequence.

    Raises:
        Exception: If any cogs fail to load or bot startup fails.
    """
    async with bot:
        logger.info(f"Configured default prefix: {bot.default_prefix}")
        logger.info(f"Configured search timeout: {bot.search_timeout}")
        logger.info(f"Configured time for message autodelete: {bot.default_delete_time}")

        try:
            await bot.load_extension('src.cogs.music_main')
            await bot.load_extension('src.cogs.music_queue')
            await bot.load_extension('src.cogs.music_control')
            logger.info("Successfully loaded all cogs")
        except Exception as e:
            logger.error(f"Failed to load cogs: {e}")
            raise

        await bot.start(os.getenv('BOT_TOKEN'))


if __name__ == "__main__":
    asyncio.run(main())