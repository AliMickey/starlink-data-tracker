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

# Function to listen to #speedtests channel in the Starlink Discord
@bot.event
async def on_message(message):
    if message.channel.id == speedtestChannelID:
        #channel = bot.get_channel(message.channel.id) # Use if replying to message is not desired
        messageData = str(message.content)
        if re.search('https://www.speedtest.net', messageData): # If url is valid
            if re.search('\d', messageData): # If url contains any digits
                r = requests.post(url = "https://starlinkversions.com/speedtests/add", data = {'source': 'discord-starlink', 'url': messageData}) # Submit POST with bot identifier
                #r = requests.post(url = "http://127.0.0.1:5000/speedtests/add", data = {'bot': True, 'url': messageData}) # Development
                await message.reply(r.text)
                
bot.run(discordToken)