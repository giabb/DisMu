# This file is part of DisMu.
# Licensed under the GNU GPL v3 or later – see LICENSE.md for details.

import logging

from discord.ext import commands

from src.utility.helpers import send_and_delete, ensure_guild_settings


class MusicControlCog(commands.Cog, name="2. Control"):
    """
    Cog to control music playback
    """
    def __init__(self, bot):
        logging.basicConfig(level=logging.INFO)
        self.bot = bot
        self.logger = logging.getLogger('music_control')

    @commands.command(name='pause', help='Pauses the currently playing song')
    async def pause(self, ctx):
        """
        Pauses the currently playing song.

        Checks if the bot is connected to a voice channel and if music is currently playing.
        If both conditions are met, pauses the playback and sends a confirmation message.
        Otherwise, informs the user that no music is playing.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await send_and_delete(ctx, "🟢 Paused the music.", self.bot.default_delete_time)
        else:
            await send_and_delete(ctx, "🟡 No music is playing.", self.bot.default_delete_time)

    @commands.command(name='resume', help='Resumes the paused music')
    async def resume(self, ctx):
        """
        Resumes paused music playback.

        Checks if the bot is connected to a voice channel and if music is currently paused.
        If both conditions are met, resumes the playback and sends a confirmation message.
        Otherwise, informs the user that the music is not paused.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await send_and_delete(ctx, "🟢 Resumed the music.", self.bot.default_delete_time)
        else:
            await send_and_delete(ctx, "🟡 The music is not paused.", self.bot.default_delete_time)

    @commands.command(name='volume', help='Adjusts the playback volume for future tracks (0.0 to 2.0)')
    async def volume(self, ctx, vol: float = commands.param(description="- A number from 0.0 to 2.0 to set the volume.")):
        """
        Adjusts the playback volume for future tracks.

        Sets the volume level for the guild, which will be applied to the next track
        that starts playing (after a skip or replay command). Volume must be between
        0.0 and 2.0, where 1.0 is normal volume.

        Args:
            ctx: The command context containing information about the message and guild.
            vol (float): The desired volume level between 0.0 and 2.0.
        """
        if not vol or vol < 0.0 or vol > 2.0:
            await send_and_delete(ctx, "🔴 Volume must be between 0.0 and 2.0!", self.bot.default_delete_time)
            return
        ensure_guild_settings(ctx.guild.id, self.bot)
        self.bot.guild_settings[ctx.guild.id]['volume'] = vol
        await send_and_delete(ctx, f"🟢 Volume set to {vol}. The change will apply at the next track start, after a skip or when replay is invoked.", self.bot.default_delete_time)

    @commands.command(name='loop', help='Toggles looping for the currently playing track')
    async def loop_track(self, ctx):
        """
        Toggles looping mode for the currently playing track.

        Switches the loop setting for the guild between enabled and disabled.
        When enabled, the current track will repeat indefinitely until looping
        is disabled or the track is skipped/stopped.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        ensure_guild_settings(ctx.guild.id, self.bot)
        self.bot.guild_settings[ctx.guild.id]['loop'] = not self.bot.guild_settings[ctx.guild.id]['loop']
        state = "enabled" if self.bot.guild_settings[ctx.guild.id]['loop'] else "disabled"
        await send_and_delete(ctx, f"🔎 Looping is now {state}.", self.bot.default_delete_time)

    @commands.command(name='stop', help='Stops the music and cleans the queue')
    async def stop(self, ctx):
        """
        Stops music playback and clears the entire queue.

        If music is currently playing, stops the playback, clears all songs from
        the queue, and resets the currently playing track. Sends appropriate
        feedback based on whether music was playing or not.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            self.bot.guild_settings[ctx.guild.id]['song_queue'].clear()
            self.bot.guild_settings[ctx.guild.id]['currently_playing'] = None
            self.bot.guild_settings[ctx.guild.id]['loop'] = False
            await send_and_delete(ctx, "🟢 Stopped the music and cleared the queue.", self.bot.default_delete_time)
        else:
            await send_and_delete(ctx, "🟡 No music is playing.", self.bot.default_delete_time)

    @commands.command(name='leave', help='Bot leaves the voice channel')
    async def leave(self, ctx):
        """
        Disconnects the bot from the voice channel.

        If the bot is connected to a voice channel, stops any playing music,
        clears the song queue, and disconnects from the voice channel.
        Sends appropriate feedback based on the bot's connection status.

        Args:
            ctx: The command context containing information about the message and guild.
        """
        if ctx.voice_client:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                self.bot.guild_settings[ctx.guild.id]['song_queue'].clear()
                self.bot.guild_settings[ctx.guild.id]['currently_playing'] = None
                self.bot.guild_settings[ctx.guild.id]['loop'] = False
            await ctx.voice_client.disconnect()
            await send_and_delete(ctx, "🫰 Goodbye!", self.bot.default_delete_time)
        else:
            await send_and_delete(ctx, "🔴 I'm not in a voice channel.", self.bot.default_delete_time)


async def setup(bot):
    await bot.add_cog(MusicControlCog(bot))
