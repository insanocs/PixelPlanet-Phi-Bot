# https://github.com/DisnakeDev/disnake/blob/master/examples/views/button/paginator.py

from typing import List

import disnake
from disnake.ext import commands


# Defines a simple paginator of buttons for the embed.
class Menu(disnake.ui.View):
    def __init__(self, embeds: List[disnake.Embed], user, id=0):
        super().__init__(timeout=30.0)
        self.embeds = embeds
        self.embed_count = id - 1 if id != 0 else id
        self.user = user

        self.first_page.disabled = True if id == 0 else False
        self.prev_page.disabled = True if id == 0 else False

        # Sets the footer of the embeds with their respective page numbers.
        for i, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Page {i + 1} of {len(self.embeds)}")
    async def on_timeout(self):
        # Once the view times out, we disable the first button and remove the second button
        self.disable_button.disabled = True
        self.remove_item(self.remove_button)

        # make sure to update the message with the new buttons
        await self.message.edit(view=self)

    @disnake.ui.button(emoji="⏪", style=disnake.ButtonStyle.blurple)
    async def first_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if interaction.author == self.user:
            self.embed_count = 0
            embed = self.embeds[self.embed_count]
            embed.set_footer(text=f"Page 1 of {len(self.embeds)}")

            self.first_page.disabled = True
            self.prev_page.disabled = True
            self.next_page.disabled = False
            self.last_page.disabled = False
            await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(emoji="◀️", style=disnake.ButtonStyle.secondary)
    async def prev_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if interaction.author == self.user:
            self.embed_count -= 1
            embed = self.embeds[self.embed_count]

            self.next_page.disabled = False
            self.last_page.disabled = False
            if self.embed_count == 0:
                self.first_page.disabled = True
                self.prev_page.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(emoji="⏹️", style=disnake.ButtonStyle.gray)
    async def remove(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if interaction.author == self.user:
            await interaction.response.edit_message("ㅤ", view=None, embed=None)

    @disnake.ui.button(emoji="▶️", style=disnake.ButtonStyle.secondary)
    async def next_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if interaction.author == self.user:
            self.embed_count += 1
            embed = self.embeds[self.embed_count]

            self.first_page.disabled = False
            self.prev_page.disabled = False
            if self.embed_count == len(self.embeds) - 1:
                self.next_page.disabled = True
                self.last_page.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(emoji="⏩", style=disnake.ButtonStyle.blurple)
    async def last_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        if interaction.author == self.user:
            self.embed_count = len(self.embeds) - 1
            embed = self.embeds[self.embed_count]

            self.first_page.disabled = False
            self.prev_page.disabled = False
            self.next_page.disabled = True
            self.last_page.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)