import discord, os, re, requests
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
discordToken = os.getenv('DISCORD_BOT_TOKEN')
speedtestChannelID = int(os.getenv('DISCORD_CHANNEL_LISTEN'))
apiKey = os.getenv('WEBSITE_KEY')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=']]', intents=intents)

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
        if re.search('https://www.speedtest.net', messageData): # Only submit messages that contain speedtest results to minimise API usage.
            r = requests.post(url = "https://starlinktrack.com/speedtests/add", data = {'api-key': apiKey, 'discord-user-id': message.author.id, 'urls': messageData}) # Submit POST with bot identifier
            await message.reply(r.text)

bot.run(discordToken)
