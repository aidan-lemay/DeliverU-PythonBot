import discord
from discord.ext import commands
import storage
from pymongo import MongoClient
from pandas import DataFrame
import datetime

# Bot Setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)
message = None

# MongoDB Setup
CONNECTION_STRING = storage.connection
client = MongoClient(CONNECTION_STRING)
dbname = client.get_database()
clock_collection = dbname['clockedIn']
# time_collection = dbname['timeWorked']

async def clockIn(user):
    data = DataFrame(clock_collection.find({'user_id': user.id}))
    if data.empty:
        userDoc = {
            'user_id': user.id,
            'user_name': user.name,
            'user_discriminator': user.discriminator,
            'clockedIn': True,
            'in_time': datetime.datetime.now(datetime.timezone.utc),
            'out_time': ""
        }
        clock_collection.insert_one(userDoc)
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked In!")
    elif data['clockedIn'].bool() == True:
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Already Clocked In Today")
    elif data['clockedIn'].bool() == False:
        clock_collection.update_one({'user_id': user.id},{'$set':{'clockedIn': True, 'in_time': datetime.datetime.now(datetime.timezone.utc), 'out_time': ''}})
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked In!")
    else:
        userDoc = {
            'user_id': user.id,
            'user_name': user.name,
            'user_discriminator': user.discriminator,
            'clockedIn': True,
            'in_time': datetime.datetime.now(datetime.timezone.utc),
            'out_time': ""
        }
        clock_collection.insert_one(userDoc)
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked In!")

async def clockOut(user):
    # ToDo: When clocking out, record hours worked into seperate data table | clocked_out - clocked_in = timeWorked
    data = DataFrame(clock_collection.find({'user_id': user.id}))
    
    if data['clockedIn'].bool() == True:
        clock_collection.update_one({'user_id': user.id},{'$set':{'clockedIn': False, 'out_time': datetime.datetime.now(datetime.timezone.utc)}})
        # data = DataFrame(clock_collection.find({'user_id': user.id}))
        # timeWorked = (data['out_time'] - data['in_time'])
        # print(timeWorked.seconds())
        # userTime = {
        #     'user_id': user.id,
        #     'user_name': user.name,
        #     'user_discriminator': user.discriminator,
        #     'timeWorked': timeWorked,
        #     'timeRecorded': datetime.datetime.now(datetime.timezone.utc)
        # }
        # time_collection.insert_one(userTime)
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked Out!")
    else:
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Not Clocked In Today")

@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    channel = bot.get_channel(979541977437716562) # Clock In/Out Server Channel
    message = await channel.send('Good Morning from DormDash Control! Please use the reaction below to clock in and out:\nReact :white_check_mark: to clock in, and :negative_squared_cross_mark: to clock out!')
    await message.add_reaction(u"\u2705")
    await message.add_reaction(u"\u274E")

@bot.event
async def on_reaction_add(reaction, user):
    if not user.bot:
        if reaction.emoji == '✅':
            await clockIn(user)
            await reaction.remove(user)
        elif reaction.emoji == '❎':
            await clockOut(user)
            await reaction.remove(user)

bot.run(storage.token)