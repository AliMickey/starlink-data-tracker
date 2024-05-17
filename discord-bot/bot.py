import nextcord, os, re, requests
from dotenv import load_dotenv
from nextcord.ext import commands
from commands import status, faqs, misc

load_dotenv()
discordToken = os.getenv('DISCORD_BOT_TOKEN')
speedtestChannelID = int(os.getenv('DISCORD_CHANNEL_LISTEN'))
apiKey = os.getenv('WEBSITE_KEY')

intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)
bot.add_cog(status.Status(bot))
bot.add_cog(faqs.Faqs(bot))
bot.add_cog(misc.Misc(bot))


@bot.event
async def on_ready():
    await bot.change_presence(activity=nextcord.Activity(name="Speedtests", type=3))
    print(f"Logged in as {bot.user.name}")


# Function to listen to #speedtests channel in the Starlink Discord
@bot.event
async def on_message(message):
    if message.channel.id == speedtestChannelID:
        # channel = bot.get_channel(message.channel.id) # Use if replying to message is not desired
        messageData = str(message.content)
        if re.search('https://www.speedtest.net', messageData):  # If url is valid
            if re.search('\\d', messageData):  # If url contains any digits
                r = requests.post(url="https://starlinktrack.com/speedtests/add",
                                  data={'api-key': apiKey, 'discord-user-id': message.author.id,
                                        'urls': messageData})  # Submit POST with bot identifier
                # r = requests.post(url = "http://127.0.0.1:5001/speedtests/add", data = {'bot': True,
                # 'url': messageData}) # Development
                await message.reply(r.text)


bot.run(discordToken)
