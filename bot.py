import discord
from discord.ext import commands
import storage
from pymongo import MongoClient
from pandas import DataFrame
import datetime

# Bot Setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# MongoDB Setup
CONNECTION_STRING = storage.connection
client = MongoClient(CONNECTION_STRING)
dbname = client.get_database()
collection_name = dbname['clockedIn']

async def clockIn(user):
    data = DataFrame(collection_name.find({'user_id': user.id}))
    
    if data['clockedIn'].bool() == True:
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Already Clocked In Today")
    else:
        userDoc = {
            'user_id': user.id,
            'user_name': user.name,
            'user_discriminator': user.discriminator,
            'clockedIn': True,
            'in_time': datetime.datetime.now(),
            'out_time': ""
        }
        collection_name.insert_one(userDoc)
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked In!")

async def clockOut(user):
    data = DataFrame(collection_name.find({'user_id': user.id}))
    
    if data['clockedIn'].bool() == True:
        collection_name.update_one({'user_id': user.id},{'$set':{'clockedIn': False, 'out_time': datetime.datetime.now()}})
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
        elif reaction.emoji == '❎':
            await clockOut(user)

# @bot.command()
# async def test(ctx):
#     await ctx.send("Test!")

bot.run(storage.token)