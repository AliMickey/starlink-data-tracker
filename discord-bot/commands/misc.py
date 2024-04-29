import nextcord
from nextcord.ext import commands


# Misc commands
class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command for the invite link
    @nextcord.slash_command(name="invite", description="Get the servers perma invite")
    async def invite(self, interaction: nextcord.Interaction):
        await interaction.response.send_message("https://discord.gg/Rr2u4ystEe")
