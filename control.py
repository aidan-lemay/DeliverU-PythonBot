import discord
from discord.ext import commands
import pandas
import storage
from pymongo import MongoClient
from pandas import DataFrame
import datetime
from bson.json_util import dumps

# Bot Setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)
message = None

guild_id = 979541976938598410
control = 984459945900662784
clock = 981001960566185984
role = 984463229466075136

# MongoDB Setup
CONNECTION_STRING = storage.connection
client = MongoClient(CONNECTION_STRING)
dbname = client.get_database()
clock_collection = dbname['clockedIn']
user_collection = dbname['dasherInformation']
# time_collection = dbname['timeWorked']

# MongoDB ChangeStream Setup
change_stream = dbname.changestream.orders.watch()

async def clockIn(user):
    usrTest = DataFrame(user_collection.find({'user_id': user.id}))
    if usrTest.empty:
        dm = await bot.fetch_user(user.id)
        await dm.send("Your Information Has Not Yet Been Logged!\nPlease Fill Out The Following Information To Begin Your Shift.")
        
        await dm.send("Type your FIRST NAME")
        def check(msg):
            return msg.author == user and msg.channel.type == discord.ChannelType.private
        msg = await bot.wait_for("message", check=check)
        firstName = msg.content.upper()

        await dm.send("Type your LAST NAME")
        def check(msg):
            return msg.author == user and msg.channel.type == discord.ChannelType.private
        msg = await bot.wait_for("message", check=check)
        lastName = msg.content.upper()

        await dm.send("Type your University Location Code\n2760: Rochester Institute of Technology")
        def check(msg):
            return msg.author == user and msg.channel.type == discord.ChannelType.private
        msg = await bot.wait_for("message")
        loccode = msg.content
        code = False
        while code == False:
            if loccode != "2760":
                await dm.send("Type your University Location Code\n```2760: Rochester Institute of Technology```")
                def check(msg):
                    return msg.author == user and msg.channel.type == discord.ChannelType.private
                msg = await bot.wait_for("message")
                loccode = msg.content
            else:
                code = True

        userInfo = {
            'user_id': user.id,
            'user_firstname': firstName,
            'user_lastname': lastName,
            'user_locationcode': loccode,
            'time_joined': datetime.datetime.now(datetime.timezone.utc)
        }
        user_collection.insert_one(userInfo)

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
        
        ctrl = bot.get_channel(control) # Bot Control Channel
        await ctrl.send(str(user.id) + " Has Been Clocked In")
        
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked In!")
    elif data['clockedIn'].bool() == True:
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Already Clocked In Today")
    elif data['clockedIn'].bool() == False:
        clock_collection.update_one({'user_id': user.id},{'$set':{'clockedIn': True, 'in_time': datetime.datetime.now(datetime.timezone.utc), 'out_time': ''}})
        
        ctrl = bot.get_channel(control) # Bot Control Channel
        await ctrl.send(str(user.id) + " Has Been Clocked In")

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

        ctrl = bot.get_channel(control) # Bot Control Channel
        await ctrl.send(str(user.id) + " Has Been Clocked In")

        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked In!")

async def clockOut(user):
    # ToDo: When clocking out, record hours worked into seperate data table | clocked_out - clocked_in = timeWorked
    data = DataFrame(clock_collection.find({'user_id': user.id}))
    
    if data['clockedIn'].bool() == True:
        clock_collection.update_one({'user_id': user.id},{'$set':{'clockedIn': False, 'out_time': datetime.datetime.now(datetime.timezone.utc)}})
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked Out!")
    else:
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Not Clocked In Today")

@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    ctrl = bot.get_channel(control) # Bot Control Channel
    await ctrl.send('DeliverU Control is Online!')
    channel = bot.get_channel(clock) # Clock In/Out Server Channel
    message = await channel.send('Good Morning from DeliverU Control! Please use the reaction below to clock in and out:\nReact :white_check_mark: to clock in, and :negative_squared_cross_mark: to clock out!')
    await message.add_reaction(u"\u2705")
    await message.add_reaction(u"\u274E")

@bot.event
async def on_reaction_add(reaction, user, member):
    if not user.bot:
        if reaction.emoji == '✅':
            await clockIn(user)
            await reaction.remove(user)
            Role = discord.utils.get(user.guild.roles, name="ClockedIn")
            await member.add_roles(reaction.message.author, Role)
        elif reaction.emoji == '❎':
            await clockOut(user)
            await reaction.remove(user)
            Role = discord.utils.get(user.guild.roles, name="ClockedIn")
            await member.remove_roles(reaction.message.author, Role)
            


@bot.event
async def on_message(message):
    if (message.channel.id == control) and (message.content.find("Clocked") != -1):
        msg = message.content
        msg = msg.split( )

        # usr = await bot.fetch_user(msg[0])
        mbr = bot.get_all_members()
        for member in mbr:
            print(member)

        # Need to: Get guild, then get MEMBER from guild using ID and bot.get_member(id)

        # if message.content.find(" Has Been Clocked In") != -1:
        #     try:
        #         await usr.add_roles(role)
        #     except discord.Forbidden:
        #         await bot.send_message(message.channel, "I don't have perms to add roles.")
        # elif message.content.find(" Has Been Clocked Out") != -1:
        #     try:
        #         await usr.remove_roles(role)
        #     except discord.Forbidden:
        #         await bot.send_message(message.channel, "I don't have perms to add roles.")
bot.run(storage.ctoken)