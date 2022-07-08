import discord
from discord.ext import commands
import numpy
import storage
from pymongo import MongoClient
from pandas import DataFrame
import datetime
from bson.objectid import ObjectId

# Bot Setup
intents = discord.Intents.default()
intents.reactions = True
bot = commands.Bot(command_prefix="/", intents=intents)

guild_id = 979541976938598410
control = 984459945900662784
general = 981001960566185984
clock = 993325622262759444
dispatch = 984464477019844639
orders = 993327814482874479
control_id = 976117168318066708
dispatch_id = 983565042123427870

role = 984463229466075136
dash_role = 994984065465847878

# MongoDB Setup
CONNECTION_STRING = storage.connection
client = MongoClient(CONNECTION_STRING)
dbname = client.get_database()
clock_collection = dbname['clockedIn']
user_collection = dbname['dasherInformation']
order_collection = dbname['orders']
# time_collection = dbname['timeWorked']

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
        await ctrl.send(str(user.name) + " Has Been Clocked In At" + datetime.datetime.now(datetime.timezone.utc))

        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked In!")

async def clockOut(user):
    # ToDo: When clocking out, record hours worked into seperate data table | clocked_out - clocked_in = timeWorked
    data = DataFrame(clock_collection.find({'user_id': user.id}))
    
    if data['clockedIn'].bool() == True:
        clock_collection.update_one({'user_id': user.id},{'$set':{'clockedIn': False, 'out_time': datetime.datetime.now(datetime.timezone.utc)}})
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked Out!")
        ctrl = bot.get_channel(control) # Bot Control Channel
        await ctrl.send(str(user.name) + " Has Been Clocked Out At" + datetime.datetime.now(datetime.timezone.utc))
    else:
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Not Clocked In Today")

@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    ctrl = bot.get_channel(control) # Bot Control Channel
    await ctrl.send('DeliverU Control is Online!')
    channel = bot.get_channel(clock) # Clock In/Out Server Channel
    smessage = await channel.send('<@&' + str(dash_role) + '> Good Morning from DeliverU Control! Please use the reaction below to clock in and out:\nReact :white_check_mark: to clock in, and :negative_squared_cross_mark: to clock out!')
    await smessage.add_reaction(u"\u2705")
    await smessage.add_reaction(u"\u274E")

@bot.event
async def on_reaction_add(reaction, user):
    if not user.id == control_id:
        if reaction.message.channel.id == clock:

            guild = bot.get_guild(guild_id)
            member = await guild.fetch_member(user.id)
            Role = discord.utils.get(member.guild.roles, name="ClockedIn")

            if reaction.emoji == '✅':
                await clockIn(user)
                await reaction.remove(user)
                
                await member.add_roles(Role)
            elif reaction.emoji == '❎':
                await clockOut(user)
                await reaction.remove(user)
                await member.remove_roles(Role)

        elif reaction.message.channel.id == dispatch:
            mid = reaction.message.content.split()[0]
            usr = DataFrame(clock_collection.find({'user_id': user.id}))
            dm = await bot.fetch_user(user.id)
            if usr['clockedIn'].bool() == True:
                ctime = datetime.datetime
                # clock_collection.update_one({'user_id': user.id},{'$set':{'clockedIn': True, 'in_time': datetime.datetime.now(datetime.timezone.utc), 'out_time': ''}})
                order_collection.update_one({'_id': mid[0]}, {'$set':{'dasherAssigned': True, 'acceptTime': datetime.datetime.now(datetime.timezone.utc), 'dasherID': user.id}})
                await dm.send("Order has been accepted")
            else:
                await dm.send("You are not clocked in - please clock in before accepting orders.")


@bot.event
async def on_message(message):
    if (message.channel.id == orders):
        msg = message.content.split( )
        order = DataFrame(order_collection.find({'_id': ObjectId(msg[0])}))
        channel = bot.get_channel(dispatch)
        smessage = await channel.send(str(msg[0]) + "\n<@&" + str(role) + "> A New Order Has Been Submitted!\nFROM: " + order.loc[0]['diningAddress'] + "\nTO: " + order.loc[0]['deliveryAddress'] + "\nReact with :white_check_mark: to claim!")
        await smessage.add_reaction(u"\u2705")

bot.run(storage.ctoken)