import discord, os, re, requests
from dotenv import load_dotenv
from discord.ext import commands
#from aiohttp import web
#import json

load_dotenv()
discordToken = os.getenv('DISCORD_BOT_TOKEN')
speedtestChannelID = int(os.getenv('DISCORD_CHANNEL_LISTEN'))
apiKey = os.getenv('WEBSITE_KEY')

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
                r = requests.post(url = "https://starlinktrack.com/speedtests/add", data = {'api-key': apiKey, 'discord-user-id': message.author.id, 'url': messageData}) # Submit POST with bot identifier
                #r = requests.post(url = "http://127.0.0.1:5000/speedtests/add", data = {'bot': True, 'url': messageData}) # Development
                await message.reply(r.text)

# async def newFirmware(request):
#     try:
#         ## happy path where name is set
#         firmware = request.query['firmware']
#         ## Process our new user
#         print(firmware)

#         response_obj = { 'status' : 'success' }
#         ## return a success json response with status code 200 i.e. 'OK'
#         return web.Response(text=json.dumps(response_obj), status=200)
#     except Exception as e:
#         ## Bad path where name is not set
#         response_obj = { 'status' : 'failed', 'reason': str(e) }
#         ## return failed with a status code of 500 i.e. 'Server Error'
#         return web.Response(text=json.dumps(response_obj), status=500)


# app = web.Application()
# app.router.add_post('/new-firmware', newFirmware)

# web.run_app(app)
                
bot.run(discordToken)