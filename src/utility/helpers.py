# This file is part of DisMu.
# Licensed under the GNU GPL v3 or later – see LICENSE.md for details.

import asyncio
import logging
import re
from collections import deque
from datetime import datetime

import discord
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('helpers')


async def delete_command_message(ctx, delete_after_time):
    """
    Attempts to delete the user's command message after a specified delay.

    Waits for the specified time period then tries to delete the original
    command message sent by the user. Handles various Discord exceptions
    that may occur during deletion (permissions, network issues, etc.).

    Args:
        ctx: The command context containing the message to delete.
        delete_after_time (float): Time in seconds to wait before deletion.
    """
    try:
        await asyncio.sleep(delete_after_time)
        await ctx.message.delete()
    except discord.Forbidden:
        logger.error("Missing permission to delete other user messages.")
    except discord.HTTPException as e:
        logger.debug(f"A non blocking error occurred during user message cancellation: {e}")
    except asyncio.CancelledError:
        logger.debug("Message cancellation operation was cancelled.")


async def send_and_delete(ctx, content, delete_after_time):
    """
    Sends a message in an embed format and schedules both messages for deletion.

    Creates a Discord embed with the provided content and sends it to the channel.
    Also schedules deletion of both the bot's response and the user's original
    command message after the specified time. If the content contains a "Currently
    playing" message with a URL, extracts and sets the URL as the embed's link.

    Args:
        ctx: The command context for sending the message.
        content (str): The message content to display in the embed.
        delete_after_time (float): Time in seconds before messages are deleted.
    """
    # Schedule the deletion of the user's command message
    asyncio.create_task(delete_command_message(ctx, delete_after_time))

    # Extract URL if present
    pattern = r"(Currently playing: .+?)\n(https?://[^\s]+)"
    match = re.search(pattern, content)
    if match:
        content = match.group(1)
        url = match.group(2)
    else:
        url = None

    # Create an embed
    embed = discord.Embed(
        description=f"**{content}**",
        color=discord.Color.blue(),
        timestamp=datetime.now(),
        url=url
    )

    # Send the embed message
    await ctx.send(embed=embed, delete_after=delete_after_time)


async def embed_and_delete(ctx, embed, view, delete_after_time):
    """
    Sends a pre-built embed with view components and schedules messages for deletion.

    Sends the provided embed and view (for interactive components like buttons)
    to the channel, then schedules deletion of both the bot's response and the
    user's original command message after the specified time.

    Args:
        ctx: The command context for sending the message.
        embed (discord.Embed): The pre-built embed to send.
        view (discord.ui.View): Interactive view components (buttons, selects, etc.).
        delete_after_time (float): Time in seconds before messages are deleted.
    """
    # Schedule the deletion of the user's command message
    asyncio.create_task(delete_command_message(ctx, delete_after_time))

    # Send the bot's response and schedule its deletion
    await ctx.send(embed=embed, view=view, delete_after=delete_after_time)


def ensure_guild_settings(guild_id, bot):
    """
    Initializes or validates guild-specific settings for the music bot.

    Checks if the specified guild has music settings configured, and creates
    default settings if none exist. Also ensures all required setting keys
    are present, adding any missing keys with default values. Settings include
    volume, loop mode, currently playing track, song queue, and replay status.

    Args:
        guild_id (int): The Discord guild ID to check/initialize settings for.
        bot: The bot instance containing guild_settings dictionary.
    """
    if guild_id not in bot.guild_settings:
        bot.guild_settings[guild_id] = {
            'volume': 0.5,
            'loop': False,
            'currently_playing': None,
            'song_queue': deque(),
            'replay': False,
        }
    else:
        # Ensure all keys exist
        if 'volume' not in bot.guild_settings[guild_id]:
            bot.guild_settings[guild_id]['volume'] = 0.5
        if 'loop' not in bot.guild_settings[guild_id]:
            bot.guild_settings[guild_id]['loop'] = False
        if 'currently_playing' not in bot.guild_settings[guild_id]:
            bot.guild_settings[guild_id]['currently_playing'] = None
        if 'song_queue' not in bot.guild_settings[guild_id]:
            bot.guild_settings[guild_id]['song_queue'] = deque()
        if 'replay' not in bot.guild_settings[guild_id]:
            bot.guild_settings[guild_id]['replay'] = False


async def play_next_in_queue(ctx, bot):
    """
    Plays the next song from the guild's queue.

    Retrieves the next song from the queue, extracts its audio information using
    yt-dlp, and starts playback with the configured volume settings. Updates the
    currently playing track info and sends a notification. If the queue is empty,
    notifies users that playback has finished. Handles errors by attempting to
    play the next song in queue.

    Args:
        ctx: The command context containing guild and voice client information.
        bot: The bot instance containing settings and configuration.
    """
    if bot.guild_settings[ctx.guild.id]['song_queue']:
        title, video_url = bot.guild_settings[ctx.guild.id]['song_queue'].popleft()
        try:
            # Run blocking yt-dlp call in a separate thread
            def extractor():
                with yt_dlp.YoutubeDL(bot.ydl_opts_single) as ydl:
                    return ydl.extract_info(video_url, download=False)

            info = await asyncio.to_thread(extractor)

            audio_url = info['url']
            title = info.get('title', title)

            ensure_guild_settings(ctx.guild.id, bot)
            bot.guild_settings[ctx.guild.id]['currently_playing'] = (title, video_url)

            await send_and_delete(ctx, f"🔎 Now playing: {title}", bot.default_delete_time)
            volume = bot.guild_settings[ctx.guild.id]['volume']
            volume_filter = f"volume={volume}"

            ctx.voice_client.stop()
            ctx.voice_client.play(
                discord.FFmpegPCMAudio(
                    audio_url,
                    before_options=bot.before_opts,
                    options=f"-loglevel error -filter:a '{volume_filter}'"
                ),
                after=lambda elem: after_song(ctx, elem, bot)
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            await send_and_delete(ctx, "🔴 An error occurred while trying to play the audio.", bot.default_delete_time)
            # Try next in queue if error
            await play_next_in_queue(ctx, bot)
    else:
        await send_and_delete(ctx, "🟡 Queue is empty. Playback finished.", bot.default_delete_time)
        bot.guild_settings[ctx.guild.id]['currently_playing'] = None

def after_song(ctx, error, bot):
    """
    Callback function executed when a song finishes playing.

    Handles post-playback logic including error logging and loop functionality.
    If loop mode is enabled, re-adds the current song to the front of the queue.
    Always attempts to play the next song in queue afterwards. This function
    is called automatically by Discord.py when audio playback ends.

    Args:
        ctx: The command context containing guild information.
        error: Any error that occurred during playback (None if successful).
        bot: The bot instance containing settings and the event loop.
    """
    if error:
        logger.error(f"Error during playback: {error}")

    guild_id = ctx.guild.id
    if bot.guild_settings[guild_id]['loop'] and bot.guild_settings[guild_id]['currently_playing']:
        # Re-add the currently playing song to the front of the queue if loop enabled
        title, url = bot.guild_settings[guild_id]['currently_playing']
        bot.guild_settings[ctx.guild.id]['song_queue'].appendleft((title, url))

    asyncio.run_coroutine_threadsafe(play_next_in_queue(ctx, bot), bot.loop)
