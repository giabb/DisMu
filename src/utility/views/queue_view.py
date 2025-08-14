# This file is part of DisMu.
# Licensed under the GNU GPL v3 or later – see LICENSE.md for details.

import discord

class QueueView(discord.ui.View):
    """
    A Discord UI View for displaying the music queue with pagination controls.

    Provides a paginated interface to browse through the current song queue
    with Previous/Next buttons. Each page displays up to 10 songs by default
    with their position numbers, titles, and URLs. Automatically disables
    navigation buttons when at the first/last page and times out after 2 minutes.

    Attributes:
        queue (list): Copy of the current queue data as a list of (title, url) tuples.
        songs_per_page (int): Number of songs to display per page.
        current_page (int): Currently displayed page number (0-based).
        message (discord.Message): The message object this view is attached to.
    """
    def __init__(self, queue_data, songs_per_page=10):
        """
        Initializes the queue view with pagination controls.

        Creates a paginated view of the queue data with Previous/Next buttons.
        Automatically disables buttons based on initial page state and sets
        a 2-minute timeout for user inactivity.

        Args:
            queue_data: The queue data structure (deque or list) containing (title, url) tuples.
            songs_per_page (int): Number of songs to display per page. Defaults to 10.
        """
        super().__init__(timeout=120)  # View will expire after 2 minutes of inactivity
        self.queue = list(queue_data)  # Copy current queue as a list
        self.songs_per_page = songs_per_page
        self.current_page = 0
        self.message = None

        # Initially, if we don't have a next page, disable next button
        if self.total_pages() <= 1:
            self.next_button.disabled = True
        self.previous_button.disabled = True  # Starting at first page, no "previous" page

    def total_pages(self):
        """
        Calculates the total number of pages needed for the current queue.

        Returns:
            int: Total number of pages required to display all songs in the queue.
        """
        return (len(self.queue) - 1) // self.songs_per_page + 1

    def get_embed(self):
        """
        Generates a Discord embed for the current page of the queue.

        Creates an embed showing the current page number, total pages, and
        the songs on the current page with their position numbers, titles,
        and URLs. Handles empty queue gracefully.

        Returns:
            discord.Embed: Formatted embed ready to be sent to Discord.
        """
        embed = discord.Embed(
            title="Current Queue",
            description=f"Page {self.current_page+1}/{self.total_pages()}",
            color=discord.Color.blue()
        )

        start = self.current_page * self.songs_per_page
        end = start + self.songs_per_page
        page_songs = self.queue[start:end]

        for i, (title, url) in enumerate(page_songs, start=start+1):
            embed.add_field(name=f"{i}. {title}", value=url, inline=False)

        if not page_songs:
            embed.description = "There are no songs in the queue."

        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Handles the Previous button interaction to navigate to the previous page.

        Moves to the previous page if available and updates button states.
        Disables the Previous button when reaching the first page and ensures
        the Next button is enabled when moving away from the last page.

        Args:
            interaction (discord.Interaction): The button interaction event.
            button (discord.ui.Button): The button that was pressed.
        """
        if self.current_page > 0:
            self.current_page -= 1
            # If we're now at the first page, disable previous
            if self.current_page == 0:
                self.previous_button.disabled = True
            # Enable next since we might not be at the last page now
            self.next_button.disabled = False

            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Handles the Next button interaction to navigate to the next page.

        Moves to the next page if available and updates button states.
        Disables the Next button when reaching the last page and ensures
        the Previous button is enabled when moving away from the first page.

        Args:
            interaction (discord.Interaction): The button interaction event.
            button (discord.ui.Button): The button that was pressed.
        """
        if self.current_page < self.total_pages() - 1:
            self.current_page += 1
            # If we're at the last page now, disable next
            if self.current_page == self.total_pages() - 1:
                self.next_button.disabled = True
            # Enable previous because we moved forward
            self.previous_button.disabled = False

            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def on_timeout(self):
        """
        Handles view timeout after 2 minutes of inactivity.

        Disables all interactive components (buttons) in the view and updates
        the message to reflect the disabled state. This prevents further
        interactions with expired view components.
        """
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)