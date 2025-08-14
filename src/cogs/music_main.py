# This file is part of DisMu.
# Licensed under the GNU GPL v3 or later – see LICENSE.md for details.

import asyncio
import logging

import discord
import yt_dlp
from discord.ext import commands

from src.utility.helpers import send_and_delete, ensure_guild_settings, after_song, play_next_in_queue, embed_and_delete
from src.utility.views import SearchView


class MusicMainCog(commands.Cog, name="1. Main"):
    """
    Cog with main commands for music playback
    """
    def __init__(self, bot):
        logging.basicConfig(level=logging.INFO)
        self.bot = bot
        self.logger = logging.getLogger('music_main')

    @commands.command(name='join', help='Bot joins the voice channel')
    async def join(self, ctx):
        """
        Makes the bot join the user's current voice channel.

        Checks if the user is in a voice channel and connects the bot to that channel.
        If the bot is already connected to a voice channel, sends a notification.
        Ensures guild settings are initialized after joining.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await send_and_delete(ctx, f"👀 I'm already in {channel}", self.bot.default_delete_time)
                return
            await channel.connect()
            ensure_guild_settings(ctx.guild.id, self.bot)
            await send_and_delete(ctx, f"🟢 Joined channel {channel}", self.bot.default_delete_time)
        else:
            await send_and_delete(ctx, "🔴 You need to be in a voice channel for me to join.", self.bot.default_delete_time)

    @commands.command(name='play', help='Plays audio from a YouTube URL')
    async def play(self, ctx, url: str = commands.param(description="- The URL of a YouTube video.")):
        """
        Plays audio from a YouTube URL immediately, stopping any current playback.

        Connects to the user's voice channel if not already connected, then extracts
        audio information from the provided YouTube URL using yt-dlp. Stops any
        currently playing audio and starts playing the new track with the configured
        volume settings.

        Args:
            ctx: The command context containing information about the message and guild.
            url (str): The YouTube URL to play audio from.
        """
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await send_and_delete(ctx, "🔴 You need to be in a voice channel to play audio.",
                                    self.bot.default_delete_time)
                return

        ensure_guild_settings(ctx.guild.id, self.bot)
        try:
            # Run yt-dlp call in a separate thread
            def extractor():
                with yt_dlp.YoutubeDL(self.bot.ydl_opts_single) as ydl:
                    return ydl.extract_info(url, download=False)

            info = await asyncio.to_thread(extractor)

            audio_url = info['url']
            title = info.get('title', 'Unknown Title')

            self.bot.guild_settings[ctx.guild.id]['currently_playing'] = (title, url)

            ctx.voice_client.stop()
            await send_and_delete(ctx, f"🔎 Now playing: {title}", self.bot.default_delete_time)

            volume = self.bot.guild_settings[ctx.guild.id]['volume']
            volume_filter = f"volume={volume}"
            ctx.voice_client.play(
                discord.FFmpegPCMAudio(audio_url, before_options=self.bot.before_opts,
                                    options=f"-loglevel error -filter:a '{volume_filter}'"),
                after=lambda e1: after_song(ctx, e1, self.bot)
            )
        except Exception as e:
            self.logger.error(f"Error: {e}")
            await send_and_delete(ctx, "🔴 An error occurred while trying to play the audio.",
                                self.bot.default_delete_time)

    @commands.command(name='playlist', help='Plays audio from a YouTube playlist')
    async def playlist(self, ctx, url: str = commands.param(description="- The URL of a YouTube playlist.")):
        """
        Adds all songs from a YouTube playlist to the queue in random order.

        Connects to the user's voice channel if not already connected, then extracts
        all entries from the provided YouTube playlist URL. Shuffles the songs and
        adds them to the guild's song queue. If nothing is currently playing,
        starts playing the first song from the queue.

        Args:
            ctx: The command context containing information about the message and guild.
            url (str): The YouTube playlist URL to process.
        """
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await send_and_delete(ctx, "🔴 You need to be in a voice channel to play audio.", self.bot.default_delete_time)
                return

        ensure_guild_settings(ctx.guild.id, self.bot)

        def fetch_playlist_info():
            with yt_dlp.YoutubeDL(self.bot.ydl_opts_playlist) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            playlist_info = await asyncio.to_thread(fetch_playlist_info)

            if 'entries' not in playlist_info:
                await send_and_delete(ctx, "🟡 This doesn't seem to be a playlist.", self.bot.default_delete_time)
                return

            temp_list = []
            for entry in playlist_info['entries']:
                title = entry.get('title', entry.get('url', 'Unknown Title'))
                temp_list.append((title, entry['url']))

            import random
            random.shuffle(temp_list)
            for item in temp_list:
                self.bot.guild_settings[ctx.guild.id]['song_queue'].append(item)

            await send_and_delete(ctx, f"🟢 Added {len(playlist_info['entries'])} songs from playlist: {playlist_info['title']}", self.bot.default_delete_time)

            if not ctx.voice_client.is_playing():
                await play_next_in_queue(ctx, self.bot)

        except Exception as e:
            self.logger.error(f"Error: {e}")
            await send_and_delete(ctx, "🔴 An error occurred while processing the playlist.", self.bot.default_delete_time)

    @commands.command(name='np', help='Shows the name and the url of the currently playing song')
    async def now_playing(self, ctx):
        """
        Shows information about the currently playing song.

        Displays the title and URL of the track that is currently playing.
        If no song is currently playing, informs the user accordingly.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        ensure_guild_settings(ctx.guild.id, self.bot)
        current = self.bot.guild_settings[ctx.guild.id]['currently_playing']
        if current:
            title, url = current
            await send_and_delete(ctx, f"🔎 Currently playing: {title}\n{url}", self.bot.default_delete_time)
        else:
            await send_and_delete(ctx, "🟡 No song is currently playing.", self.bot.default_delete_time)

    @commands.command(name='search', help='Searches YouTube for a query and lets you pick a track to play')
    async def search(self, ctx, *, query: str = commands.param(description="- The query to search for on YouTube.")):
        """
            Searches YouTube for a query and allows the user to select a track to add to queue.

            Connects to the user's voice channel if not already connected, then performs
            a YouTube search for the provided query. Displays up to 10 results in an embed
            and waits for the user to select a track by typing a number (1-10). The selected
            track is added to the queue and will play if nothing is currently playing.

            Args:
                ctx: The command context containing information about the message and guild.
                query (str): The search term to look for on YouTube.
            """
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await send_and_delete(ctx, "🔴 You need to be in a voice channel to play audio.", self.bot.default_delete_time)
                return

        ensure_guild_settings(ctx.guild.id, self.bot)

        def yt_search(q):
            with yt_dlp.YoutubeDL(self.bot.ydl_opts_playlist) as ydl:
                return ydl.extract_info(f"ytsearch10:{q}", download=False)['entries']

        results = await asyncio.to_thread(yt_search, query)
        if not results:
            await send_and_delete(ctx, "🔴 No results found.", self.bot.default_delete_time)
            return

        view = SearchView(results, songs_per_page=10)
        embed = view.get_embed()
        message = await embed_and_delete(ctx, embed, view, self.bot.embed_autodelete)
        view.message = message

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            msg = await self.bot.wait_for('message', timeout=self.bot.search_timeout, check=check)
            choice = int(msg.content)
            if 1 <= choice <= 10:
                selected = results[choice - 1]
                self.bot.guild_settings[ctx.guild.id]['song_queue'].append(
                    (selected.get('title', 'Unknown Title'), selected['url']))
                await send_and_delete(ctx, f"🟢 Added **{selected.get('title', 'Unknown Title')}** to the queue.", self.bot.default_delete_time)
                if not ctx.voice_client.is_playing():
                    await play_next_in_queue(ctx, self.bot)
            else:
                await send_and_delete(ctx, "🔴 Invalid choice. Canceling.", self.bot.default_delete_time)
        except asyncio.TimeoutError:
            await send_and_delete(ctx, "🔴 You took too long to respond. Canceling.", self.bot.default_delete_time)

    @commands.command(name='replay', help='Replays the current song from the beginning')
    async def replay(self, ctx):
        """
        Replays the currently playing song from the beginning.

        Takes the current song and adds it to the front of the queue, then stops
        the current playback. This triggers the after_song callback which will
        immediately start playing the song again from the beginning.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        ensure_guild_settings(ctx.guild.id, self.bot)
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await send_and_delete(ctx, "🟡 There isn't anything currently playing to replay.",
                                self.bot.default_delete_time)
            return

        current = self.bot.guild_settings[ctx.guild.id].get('currently_playing')
        if not current:
            await send_and_delete(ctx, "🟡 No song is currently playing to replay.", self.bot.default_delete_time)
            return

        # Add the current song to the front of the queue to be played next
        self.bot.guild_settings[ctx.guild.id]['song_queue'].appendleft(current)

        # Stop the current playback, which will trigger the 'after' callback
        ctx.voice_client.stop()
        await send_and_delete(ctx, "🟢 Replaying...", self.bot.default_delete_time)


async def setup(bot):
    await bot.add_cog(MusicMainCog(bot))
