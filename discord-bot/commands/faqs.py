import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Button


# Define the buttons for the FAQ gaming command. Buttons:
# https://github.com/nextcord/nextcord/blob/master/examples/views/confirm.py
class CliGui(View):
    def __init__(self):
        super().__init__()

    @nextcord.ui.button(label="GUI", style=nextcord.ButtonStyle.primary)
    async def bot_status(self, button: Button, interaction: nextcord.Interaction):
        await interaction.message.edit(content="# GUI\n\n Open Settings and go to Network & Internet > Change adapter "
                                               "Options > Right click on your network adapter > Properties > Uncheck "
                                               "Internet Protocol Version 6 (TCP/IPv6) > OK\n\n")

    @nextcord.ui.button(label="CLI", style=nextcord.ButtonStyle.primary)
    async def website_status(self, button: Button, interaction: nextcord.Interaction):
        await interaction.message.edit(content='# CLI\n ## CMD \n **WARNING, THIS EDITS YOUR REGISTRY!!** Open Command'
                                               'Prompt as administrator and run the command: `reg add '
                                               r'"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip6'
                                               r'\Parameters" /v DisabledComponents /t REG_DWORD /d 255 /f`\n\n '
                                               '## PowerShell \n Run PowerShell as administrator and run the command: '
                                               '`Disable-NetAdapterBinding -Name "Ethernet" -ComponentID '
                                               'ms_tcpip6`replacing "Ethernet" with your network adapter name')


class Faqs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command()
    async def faq(self, interaction: nextcord.Interaction):
        """
        Never Called, DON'T USE OR TOUCH, subcommand base
        """

    @faq.subcommand(name="obstructions", description="View information about obstructions")
    async def obstructions(self, interaction: nextcord.Interaction):
        await interaction.response.send_message("Obstructions FAQ")

    @faq.subcommand(name="gaming", description="How to fix gaming services")
    async def gaming(self, interaction: nextcord.Interaction):
        description = (
            "Some gaming services require some sort of IPv4 to function online, one of these being Minecraft. "
            "A fix for this is to disabled Internet Protocol Version 6 (IPv6) on your network adapter. This "
            "can be done by following any of these tutorials for Windows 10/11\n# USE GUI IF YOU DONT KNOW WHAT YOU "
            "ARE DOING\n")
        view = CliGui()
        await interaction.send(f"# Gaming Services FAQ\n{description}", view=view)

    @faq.subcommand(name="dishystarlinkcom", description="What happened to dishy.starlink.com?")
    async def dishy_web(self, interaction: nextcord.Interaction):
        await interaction.response.send_message("# TL;DR, dishy.starlink.com was depreciated by Starlink and is no "
                                                "longer usable. \n Unfortunately, there is no way to access the web "
                                                "interface for the dishy anymore due to Starlink shutting it down. "
                                                "You can still access stats using [DanOpsTech's Starlink]("
                                                "<https://github.com/danopstech/starlink>) self hosted monitoring "
                                                "service.")

    @faq.subcommand(name="starlinktrack", description="What is Starlinktrack?")
    async def starlinktrack(self, interaction: nextcord.Interaction):
        await interaction.response.send_message("Starlinktrack is a community project to track Starlink "
                                                "speedtests, show firmware updates, check up on Starlink network "
                                                "progess, and view Starlink products, created by alimicky.")
