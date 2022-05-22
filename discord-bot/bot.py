import discord, os, re, requests
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
discordToken = os.getenv('DISCORD_BOT_TOKEN')
speedtestChannelID = int(os.getenv('DISCORD_CHANNEL_LISTEN'))

bot = commands.Bot(command_prefix=']]')

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(name="Speedtests", type=3))
    print('Success')

@bot.event
async def on_message(message):
    if message.channel.id == speedtestChannelID:
        channel = bot.get_channel(message.channel.id)
        messageData = str(message.content)
        if re.search('https://www.speedtest.net/result', messageData): # If url is valid
            if re.search('\d', messageData): # If url contains any digits
                r = requests.post(url = "https://starlinkversions.com/speedtest/add", data = {'bot': True, 'url': messageData})
                await channel.send(r.text)

bot.run(discordToken)