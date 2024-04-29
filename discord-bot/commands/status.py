import nextcord, requests
from nextcord.ext import commands
from nextcord.ui import View, Button


# Button view for the status command. Buttons:
# https://github.com/nextcord/nextcord/blob/master/examples/views/confirm.py
class BotWebStatus(View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @nextcord.ui.button(label="Website", style=nextcord.ButtonStyle.primary)
    async def website_status(self, button: Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        r = requests.get("https://starlinktrack.com")
        if r.status_code != 200:
            await interaction.message.edit(content=f"Website is not responding, Response code {r.status_code}")
        else:
            await interaction.message.edit(content=f"Website is online, Response code {r.status_code}")

    @nextcord.ui.button(label="Bot", style=nextcord.ButtonStyle.primary)
    async def bot_status(self, button: Button, interaction: nextcord.Interaction):
        latency = self.bot.latency
        await interaction.message.edit(content=f"{round(latency * 1000)}ms round trip from Discord API to bot")


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="status", description="Check the status of the bot or website")
    async def status(self, interaction: nextcord.Interaction):
        view = BotWebStatus(self.bot)
        await interaction.send("Would you like to check the status of the website or the bot?",view=view)
        await view.wait()
