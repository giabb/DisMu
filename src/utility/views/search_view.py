# This file is part of DisMu.
# Licensed under the GNU GPL v3 or later – see LICENSE.md for details.

import discord

class SearchView(discord.ui.View):
    """
    A Discord UI View for displaying YouTube search results with pagination.

    Provides a paginated interface to browse through YouTube search results.
    Each page displays up to 10 results by default with their position numbers,
    titles, and clickable links. Times out after 2 minutes of inactivity.

    Attributes:
        results (list): List of search result dictionaries from yt-dlp.
        songs_per_page (int): Number of results to display per page.
        current_page (int): Currently displayed page number (0-based).
        message (discord.Message): The message object this view is attached to.
    """
    def __init__(self, results, songs_per_page=10):
        super().__init__(timeout=120)
        self.results = list(results)
        self.songs_per_page = songs_per_page
        self.current_page = 0
        self.message = None

    def total_pages(self):
        return (len(self.results) - 1) // self.songs_per_page + 1

    def get_embed(self):
        embed = discord.Embed(
            title="YouTube Search Results",
            description=f"Page {self.current_page + 1}/{self.total_pages()}",
            color=discord.Color.blue()
        )

        start = self.current_page * self.songs_per_page
        end = start + self.songs_per_page
        page_results = self.results[start:end]

        for i, r in enumerate(page_results, start=start + 1):
            embed.add_field(
                name=f"{i}. {r.get('title', 'Unknown Title')}",
                value=f"[Link]({r.get('url', 'No URL')})",
                inline=False
            )

        if not page_results:
            embed.description = "No results found."

        return embed

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)