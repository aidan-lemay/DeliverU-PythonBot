import discord
from discord.ext import commands
import storage
from pymongo import MongoClient
from pandas import DataFrame
import datetime
from bson.objectid import ObjectId

# Bot Setup
intents = discord.Intents.default()
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)

locations = {
    2760: { # RIT
        "guild_id": 979541976938598410, # ID of server
        "control": 984459945900662784, # ID of this bot in server
        "general": 981001960566185984, # ID of #General text channel
        "clock": 993325622262759444, # ID of channel where clock-in/out messages are sent
        "dispatch": 984464477019844639, # ID of Dispatch bot in this server
        "orders": 993327814482874479, # ID of PRIVATE channel where bot order logs are dumped
        "control_id": 976117168318066708, # ID of PRIVATE channel where bot control and logging is dumped
        "dispatch_id": 983565042123427870, # ID of channel where orders are dispatched from
        "clocked_role": 984463229466075136, # ID of ClockedIN role
        "dash_role": 994984065465847878 # ID of Dashers role
    },
    5816: { # UNC
        "guild_id": 1008479273314697246, # ID of server
        "control": 976117168318066708, # ID of this bot in server
        "general": 1010554238788718622, # ID of #General text channel
        "clock": 1010554335802970163, # ID of channel where clock-in/out messages are sent
        "dispatch": 983565042123427870, # ID of Dispatch bot in this server
        "orders": 1010554530976514110, # ID of PRIVATE channel where bot order logs are dumped
        "control_id": 1010554597548490773, # ID of PRIVATE channel where bot control and logging is dumped
        "dispatch_id": 1008489666883899432, # ID of channel where orders are dispatched from

        "clocked_role": 1010554684697747466, # ID of ClockedIN role
        "dash_role": 1008491557122482226 # ID of Dashers role
    }
}

# MongoDB Setup
CONNECTION_STRING = storage.connection
client = MongoClient(CONNECTION_STRING)
dbname = client.get_database()
clock_collection = dbname['clockedIn']
user_collection = dbname['dasherInformation']
order_collection = dbname['orders']

@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    for l in locations:

        control = locations[l]['control']
        clock = locations[l]['clock']

        ctrl = bot.get_channel(control)
        await ctrl.send('DeliverU Control is Online!')

        channel = bot.get_channel(clock)
        smessage = await channel.send('<@&'  + str(locations[l]['dash_role']) + '> Good Morning from DeliverU Control! Please use the reaction below to clock in and out:\nReact :white_check_mark: to clock in, and :negative_squared_cross_mark: to clock out!')
        await smessage.add_reaction(u"\u2705")
        await smessage.add_reaction(u"\u274E")

bot.run(storage.ctoken)