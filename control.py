import discord
from discord.ext import commands
import storage
from pymongo import MongoClient
from pandas import DataFrame
import datetime
from bson.objectid import ObjectId
from twilio.rest import Client

# Bot Setup
intents = discord.Intents.default()
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Twillio Setup
account_sid = storage.twSID
auth_token = storage.twAUTH
twillio = Client(account_sid, auth_token)

locations = storage.locations
# locations = storage.testing

# MongoDB Setup
CONNECTION_STRING = storage.connection
client = MongoClient(CONNECTION_STRING)
dbname = client.get_database()
clock_collection = dbname['clockedIn']
user_collection = dbname['dasherInformation']
order_collection = dbname['orders']

async def clockIn(user):
    usrTest = DataFrame(user_collection.find({'user_id': user.id}))
    loccode = 0
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

        await dm.send("Type your University Location Code\n```2760: Rochester Institute of Technology\n5816: University of North Carolina```")
        def check(msg):
            return msg.author == user and msg.channel.type == discord.ChannelType.private
        msg = await bot.wait_for("message")
        loccode = msg.content
        code = False
        while code == False:
            if loccode != "2760" and loccode != "5816":
                await dm.send("Type your University Location Code\n```2760: Rochester Institute of Technology\n5816: University of North Carolina```")
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
    
    userInfo = DataFrame(user_collection.find({'user_id': user.id}))

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
        
        ctrl = bot.get_channel(locations[int(userInfo['user_locationcode'][0])]['control-channel']) # Bot Control Channel
        await ctrl.send(str(user.name) + " Has Been Clocked In At " + str(datetime.datetime.now(datetime.timezone.utc)))
        
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked In!")
    elif data['clockedIn'].bool() == True:
        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Already Clocked In Today")
    elif data['clockedIn'].bool() == False:
        clock_collection.update_one({'user_id': user.id},{'$set':{'clockedIn': True, 'in_time': datetime.datetime.now(datetime.timezone.utc), 'out_time': ''}})
        
        ctrl = bot.get_channel(locations[int(userInfo['user_locationcode'][0])]['control-channel']) # Bot Control Channel
        await ctrl.send(str(user.name) + " Has Been Clocked In At " + str(datetime.datetime.now(datetime.timezone.utc)))

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

        ctrl = bot.get_channel(locations[user.loccode]['control']) # Bot Control Channel
        await ctrl.send(str(user.name) + " Has Been Clocked In At " + str(datetime.datetime.now(datetime.timezone.utc)))

        dm = await bot.fetch_user(user.id)
        await dm.send("You Have Been Clocked In!")

async def clockOut(user):
    data = DataFrame(clock_collection.find({'user_id': user.id}))
    usr = DataFrame(user_collection.find({'user_id': user.id}))

    if usr.empty:
        dm = await bot.fetch_user(user.id)
        await dm.send("You don't exist in our database! Please clock-in and sign-up before continuing!")

    else:
        loccode = usr['user_locationcode'][0]
        control = locations[int(loccode)]['control-channel']
        
        if data['clockedIn'].bool() == True:
            clock_collection.update_one({'user_id': user.id},{'$set':{'clockedIn': False, 'out_time': str(datetime.datetime.now(datetime.timezone.utc))}})
            dm = await bot.fetch_user(user.id)
            await dm.send("You Have Been Clocked Out!")
            ctrl = bot.get_channel(control)
            await ctrl.send(str(user.name) + " Has Been Clocked Out At " + str(datetime.datetime.now(datetime.timezone.utc)))
        else:
            dm = await bot.fetch_user(user.id)
            await dm.send("You Have Not Clocked In Today")

@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    for l in locations:

        control = locations[l]['control-channel']
        clock = locations[l]['clock-channel']

        ctrl = bot.get_channel(control)
        await ctrl.send('DeliverU Control is Online!')

        channel = bot.get_channel(clock)
        smessage = await channel.send('<@&'  + str(locations[l]['dash_role']) + '> Good Morning from DeliverU Control! Please use the reaction below to clock in and out:\nReact :white_check_mark: to clock in, and :negative_squared_cross_mark: to clock out!')
        await smessage.add_reaction(u"\u2705")
        await smessage.add_reaction(u"\u274E")

@bot.event
async def on_reaction_add(reaction, user):
    if not isinstance(reaction.message.channel, discord.DMChannel):
            for l in locations:
                if user.id != locations[l]['control-bot']:
                    if reaction.message.channel.id == locations[l]['clock-channel']:                      

                        if reaction.emoji == '✅':
                            await clockIn(user)
                            usr = DataFrame(user_collection.find({'user_id': user.id}))  
                            if not usr.empty:
                                loc = int(usr['user_locationcode'][0])

                                guild = bot.get_guild(locations[loc]['guild_id'])
                                member = await guild.fetch_member(user.id)
                                Role = discord.utils.get(member.guild.roles, name="ClockedIn")
                                await reaction.remove(user)
                                await member.add_roles(Role)

                        elif reaction.emoji == '❎':
                            await clockOut(user)
                            usr = DataFrame(user_collection.find({'user_id': user.id}))  
                            if not usr.empty:
                                loc = int(usr['user_locationcode'][0])

                                guild = bot.get_guild(locations[loc]['guild_id'])
                                member = await guild.fetch_member(user.id)
                                Role = discord.utils.get(member.guild.roles, name="ClockedIn")
                                await reaction.remove(user)
                                await member.remove_roles(Role)

                    elif reaction.message.channel.id == locations[l]['dispatch-channel']:
                        channel = reaction.message.channel.id
                        found = False
                        location = {}

                        for l in locations:
                            if found == False and channel == locations[l]['dispatch-channel']:
                                location = locations[l]
                                found = True

                        if found:

                            mid = reaction.message.content.split()[0]
                            usr = DataFrame(clock_collection.find({'user_id': user.id}))
                            order = DataFrame(order_collection.find({'_id': ObjectId(mid)}))
                            dm = await bot.fetch_user(user.id)

                            if usr.empty:
                                dm = await bot.fetch_user(user.id)
                                await dm.send("You don't exist in our database! Please clock-in and sign-up before continuing!")

                            else:
                                if user.bot == False:
                                    if order['dasherAssigned'].bool() == False:
                                        if usr['clockedIn'].bool() == True:
                                            order_collection.update_one({'_id': ObjectId(mid)}, {'$set':{'dasherAssigned': True, 'acceptTime': datetime.datetime.now(datetime.timezone.utc), 'dasherID': user.id}})
                                            order = DataFrame(order_collection.find({'_id': ObjectId(mid)}))
                                            dasher = DataFrame(user_collection.find({'user_id': user.id}))
                                            
                                            smessage = await dm.send(mid + " Order has been accepted!\nMobile Order Number: " + str(order.loc[0]['mobileOrderNumber']) + "\nPick Up From: " + str(order.loc[0]['diningAddress']) + "\nDeliver To: " + str(order.loc[0]['deliveryAddress']) + "\nRoom Number: " + str(order.loc[0]['roomNumber']) + "\nCustomer Name: " + str(order.loc[0]['customerName']) + "\nCustomer Phone Number: " + str(order.loc[0]['customerPhone']) + "\nCustomer Order Instructions: " + str(order.loc[0]['customerInstructions']) + "\nReact with :white_check_mark: to mark as complete!")
                                            await smessage.add_reaction(u"\u2705")

                                            # Twillio Order Info Dispatch
                                            toNum = "+1" + str(order.loc[0]['customerPhone'])
                                            fromNum = location['twPhone']
                                            name = order.loc[0]['customerName']
                                            twillio.messages.create(body='Hello ' + name + '!\nYour order has been picked up by ' + dasher.loc[0]['user_firstname'] + '\nYou will recieve a follow-up message when your order is delivered.\nThank you for choosing DeliverU!', from_=fromNum, to=toNum)

                                            channel = bot.get_channel(location['control-channel'])
                                            await channel.send("Order has been accepted by " + str(user.name) + " at " + str(datetime.datetime.now(datetime.timezone.utc)) + "\nMobile Order Number: " + str(order.loc[0]['mobileOrderNumber']) + "\nPick Up From: " + str(order.loc[0]['diningAddress']) + "\nDeliver To: " + str(order.loc[0]['deliveryAddress']) + "\nRoom Number: " + str(order.loc[0]['roomNumber']) + "\nCustomer Name: " + str(order.loc[0]['customerName']) + "\nCustomer Phone Number: " + str(order.loc[0]['customerPhone']) + "\nCustomer Order Instructions: " + str(order.loc[0]['customerInstructions']))
                                            await reaction.message.delete()
                                        else:
                                            await dm.send("You are not clocked in - please clock in before accepting orders.")
                                    else:
                                        await dm.send("Order has Already Been Accepted!")

    else:
        if reaction.emoji == '✅':
            if reaction.message.channel.type == discord.ChannelType.private:

                if user.bot == False:
                    usr = DataFrame(user_collection.find({'user_id': user.id}))

                    loccode = usr['user_locationcode'][0]
                    control = locations[int(loccode)]['control-channel']
                    
                    mid = reaction.message.content.split()[0]
                    order_collection.update_one({'_id': ObjectId(mid)}, {'$set':{'orderComplete': True, 'completeTime': datetime.datetime.now(datetime.timezone.utc)}})
                    channel = bot.get_channel(control)
                    await channel.send("Order " + str(mid) + " has been completed by " + str(user.name) + " at " + str(datetime.datetime.now(datetime.timezone.utc)))
                    await reaction.message.edit(content="Your Order Has Been Completed! Nice Job!")
                    
                    # Twillio Order Info Dispatch
                    order = DataFrame(order_collection.find({'_id': ObjectId(mid)}))
                    dasher = DataFrame(user_collection.find({'user_id': user.id}))                    
                    toNum = "+1" + str(order.loc[0]['customerPhone'])
                    fromNum = locations[int(loccode)]['twPhone']
                    name = order.loc[0]['customerName']
                    twillio.messages.create(body='Hello ' + name + '!\n' + dasher.loc[0]['user_firstname'] + ' has completed your order!\nThank you for choosing DeliverU!', from_=fromNum, to=toNum)

@bot.event
async def on_message(message):

    found = False
    dispatch = 0
    clocked_role = 0
    for l in locations:
        if message.channel.id == locations[l]['order-logging']:
            found = True
            dispatch = locations[l]['dispatch-channel']
            clocked_role = locations[l]['clocked_role']
            fromNum = locations[l]['twPhone']

    if (found == True):
        msg = message.content.split( )
        order = DataFrame(order_collection.find({'_id': ObjectId(msg[0])}))
        
        channel = bot.get_channel(dispatch)
        order = order.loc[0]
        dinAddr = order['diningAddress']
        delAddr = order['deliveryAddress']

        smessage = await channel.send(str(msg[0]) + "\n<@&" + str(clocked_role) + "> A New Order Has Been Submitted!\nFROM: " + dinAddr + "\nTO: " + delAddr + "\nReact with :white_check_mark: to claim!")
        await smessage.add_reaction(u"\u2705")

        # Twillio Order Info Dispatch
        toNum = "+1" + str(order['customerPhone'])
        name = order['customerName']
        twillio.messages.create(body='Hello ' + name + '!\nYour order has been recieved by our system and dispatched to our runners!\nYou will recieve a follow-up message when your order is accepted by a runner.\nThank you for choosing DeliverU!', from_=fromNum, to=toNum)

bot.run(storage.ctoken)