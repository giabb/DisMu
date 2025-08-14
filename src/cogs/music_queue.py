# This file is part of DisMu.
# Licensed under the GNU GPL v3 or later – see LICENSE.md for details.

import asyncio
import logging

import yt_dlp
from discord.ext import commands

from src.utility.helpers import send_and_delete, play_next_in_queue, embed_and_delete
from src.utility.views import QueueView


class MusicQueueCog(commands.Cog, name="3. Queue"):
    """
    Cog to control queue
    """
    def __init__(self, bot):
        logging.basicConfig(level=logging.INFO)
        self.bot = bot
        self.logger = logging.getLogger('music_queue')

    @commands.command(name='queue', help='Shows the currently queued songs with pagination')
    async def show_queue(self, ctx):
        """
        Displays the current song queue with pagination controls.

        Shows up to 10 songs per page in an embed format with navigation buttons.
        If the queue is empty, informs the user accordingly. The embed includes
        song titles and positions in the queue.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        if not self.bot.guild_settings[ctx.guild.id]['song_queue']:
            await send_and_delete(ctx, "🟡 The queue is empty.", self.bot.default_delete_time)
            return

        view = QueueView(self.bot.guild_settings[ctx.guild.id]['song_queue'], songs_per_page=10)
        embed = view.get_embed()
        message = await embed_and_delete(ctx, embed, view, self.bot.embed_autodelete)
        view.message = message

    @commands.command(name='skip', help='Skips the current song')
    async def skip(self, ctx):
        """
        Skips the currently playing song and moves to the next in queue.

        Stops the current playback which triggers the after_song callback to play
        the next song in the queue. Also disables looping for the current track.
        If no song is playing, informs the user accordingly.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        if ctx.voice_client and ctx.voice_client.is_playing():
            self.bot.guild_settings[ctx.guild.id]['loop'] = False
            ctx.voice_client.stop()
            await send_and_delete(ctx, "🟢 Skipped the current song.", self.bot.default_delete_time)
        else:
            await send_and_delete(ctx, "🔴 No song is currently playing.", self.bot.default_delete_time)

    @commands.command(name='skipto', help='Skips directly to a specific song number in the queue')
    async def skip_to(self, ctx, position: int = commands.param(description="- The song number in the queue to skip to.")):
        """
        Skips directly to a specific song number in the queue.

        Removes all songs before the specified position from the queue and either
        stops current playback (if playing) or starts playing the target song.
        The position must be within the valid range of the current queue.

        Args:
            ctx: The command context containing information about the message and guild.
            position (int): The queue position (1-based) to skip to.
        """
        if not self.bot.guild_settings[ctx.guild.id]['song_queue']:
            await send_and_delete(ctx, "🟡 The queue is empty.", self.bot.default_delete_time)
            return

        if position < 1 or position > len(self.bot.guild_settings[ctx.guild.id]['song_queue']):
            await send_and_delete(ctx, "🔴 That position is out of range.", self.bot.default_delete_time)
            return

        for _ in range(position - 1):
            self.bot.guild_settings[ctx.guild.id]['song_queue'].popleft()

        await send_and_delete(ctx, f"🔎 Skipping ahead to song number {position}...", self.bot.default_delete_time)

        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        else:
            await play_next_in_queue(ctx, self.bot)

    @commands.command(name='bump', help='Bumps a song to be the next one played')
    async def bump(self, ctx, position: int = commands.param(description="- The song number in the queue to bump on top of the queue.")):
        """
        Moves a song from a specified position to the front of the queue.

        Takes a song at the given position and moves it to be the next song
        that will play after the current song finishes. The position must be
        within the valid range of the current queue.

        Args:
            ctx: The command context containing information about the message and guild.
            position (int): The queue position (1-based) of the song to bump.
        """
        # Ensure the guild has a queue initialized
        if ctx.guild.id not in self.bot.guild_settings or not self.bot.guild_settings[ctx.guild.id]['song_queue']:
            await send_and_delete(ctx, "🟡 The queue is empty.", self.bot.default_delete_time)
            return

        queue = self.bot.guild_settings[ctx.guild.id]['song_queue']

        # Validate the position input from the user
        if not 1 <= position <= len(queue):
            await send_and_delete(ctx, "🔴 That queue position is invalid.", self.bot.default_delete_time)
            return

        songs_list = list(queue)
        bumped_song = songs_list.pop(position - 1)
        songs_list.insert(0, bumped_song)

        # Clear the old queue and repopulate it with the new, reordered list
        queue.clear()
        queue.extend(songs_list)

        title, _ = bumped_song
        await send_and_delete(ctx, f'🟢 Bumped "**{title}**" to the next spot in the queue.', #✅
                            self.bot.default_delete_time)

    @commands.command(name='remove', help='Removes a song from the queue at a given position')
    async def remove(self, ctx, position: int = commands.param(description="- The song number in the queue to remove.")):
        """
        Removes a song from the queue at the specified position.

        Permanently removes the song at the given position from the queue.
        The position must be within the valid range of the current queue.
        Shows the title of the removed song in the confirmation message.

        Args:
            ctx: The command context containing information about the message and guild.
            position (int): The queue position (1-based) of the song to remove.
        """
        if position < 1 or position > len(self.bot.guild_settings[ctx.guild.id]['song_queue']):
            await send_and_delete(ctx, f"🔴 That position is out of range. Please choose a number between 1 and {len(self.bot.guild_settings[ctx.guild.id]['song_queue'])}", self.bot.default_delete_time)
            return

        songs_list = list(self.bot.guild_settings[ctx.guild.id]['song_queue'])
        removed_song = songs_list.pop(position - 1)
        self.bot.guild_settings[ctx.guild.id]['song_queue'].clear()
        self.bot.guild_settings[ctx.guild.id]['song_queue'].extend(songs_list)

        title, _ = removed_song
        await send_and_delete(ctx, f"🟢 Removed \"{title}\" from the queue.", self.bot.default_delete_time)

    @commands.command(name='move', help='Moves a song from one position in the queue to another')
    async def move(self, ctx, from_pos: int = commands.param(description="- The song number in the queue to move"), to_pos: int = commands.param(description="- The new song number in the queue to move the from_pos song to.")):
        """
        Moves a song from one position in the queue to another.

        Takes a song at the 'from' position and moves it to the 'to' position,
        shifting other songs accordingly. Both positions must be within the
        valid range of the current queue.

        Args:
            ctx: The command context containing information about the message and guild.
            from_pos (int): The current position (1-based) of the song to move.
            to_pos (int): The target position (1-based) where the song should be moved.
        """
        if (from_pos < 1 or from_pos > len(self.bot.guild_settings[ctx.guild.id]['song_queue'])) or (to_pos < 1 or to_pos > len(self.bot.guild_settings[ctx.guild.id]['song_queue'])):
            await send_and_delete(ctx, "🔴 Positions are out of range.", self.bot.default_delete_time)
            return

        songs_list = list(self.bot.guild_settings[ctx.guild.id]['song_queue'])
        song = songs_list.pop(from_pos - 1)
        songs_list.insert(to_pos - 1, song)
        self.bot.guild_settings[ctx.guild.id]['song_queue'].clear()
        self.bot.guild_settings[ctx.guild.id]['song_queue'].extend(songs_list)

        title, _ = song
        await send_and_delete(ctx, f"🟢 Moved \"{title}\" from position {from_pos} to {to_pos}.", self.bot.default_delete_time)

    @commands.command(name='shuffle', help='Shuffles the current queue')
    async def shuffle_queue(self, ctx):
        """
        Randomly shuffles all songs in the current queue.

        Reorders all songs in the queue randomly. Requires at least 2 songs
        in the queue to perform the shuffle operation. The currently playing
        song is not affected by the shuffle.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        if len(self.bot.guild_settings[ctx.guild.id]['song_queue']) < 2:
            await send_and_delete(ctx, "🔴 Not enough songs in the queue to shuffle.", self.bot.default_delete_time)
            return

        import random
        songs_list = list(self.bot.guild_settings[ctx.guild.id]['song_queue'])
        random.shuffle(songs_list)
        self.bot.guild_settings[ctx.guild.id]['song_queue'].clear()
        self.bot.guild_settings[ctx.guild.id]['song_queue'].extend(songs_list)
        await send_and_delete(ctx, "🟢 Queue shuffled!", self.bot.default_delete_time)

    @commands.command(name='add', help='Adds a song to the front of the queue')
    async def add(self, ctx, url: str = commands.param(description="- The YouTube URL of the song to add to the queue.")):
        """
        Adds a song from a YouTube URL to the front of the queue.

        Connects to the user's voice channel if not already connected, then
        extracts song information from the provided YouTube URL and adds it
        as the next song to play. If nothing is currently playing, starts
        playing the added song immediately.

        Args:
            ctx: The command context containing information about the message and guild.
            url (str): The YouTube URL of the song to add to the queue.
        """
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await send_and_delete(ctx, "🔴 You must be in a voice channel to add a song.",
                                    self.bot.default_delete_time)
                return

        processing_msg = await ctx.send("🔎 Adding song to the front of the queue...")

        try:
            def extractor():
                with yt_dlp.YoutubeDL(self.bot.ydl_opts_single) as ydl:
                    return ydl.extract_info(url, download=False)

            info = await asyncio.to_thread(extractor)
            title = info.get('title', 'Unknown Title')

            self.bot.guild_settings[ctx.guild.id]['song_queue'].appendleft((title, url))

            await processing_msg.delete()
            await send_and_delete(ctx, f'🟢 Added "**{title}**" as the next song.', self.bot.default_delete_time)

            if not ctx.voice_client.is_playing():
                await play_next_in_queue(ctx, self.bot)

        except Exception as e:
            await processing_msg.delete()
            self.logger.error(f"Error in 'add' command: {e}")
            await send_and_delete(ctx, "🔴 Sorry, I couldn't add that song. Are you sure there is a queue?", self.bot.default_delete_time)

async def setup(bot):
    await bot.add_cog(MusicQueueCog(bot))
