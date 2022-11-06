import discord
from discord.ext import tasks, commands

import api_call
import asyncio


client = commands.Bot(command_prefix="!", help_command=None)

def clientRun():
    file = open("token.txt", "r")
    client.run(file.read())
    file.close()

def checkForDuplicates(collectionToAdd, collectionList):
    duplicate = False
    for i in collectionList:
        if i == collectionToAdd:
            duplicate = True
            break
    return duplicate


mainChannel = "" # put channel ID here
collectionWatchList = []
collectionChannels = []

collectionAlertsList = [["dyor_nerds",0,0]]

@tasks.loop(count=1)
async def wait_until_ready():
    await client.wait_until_ready()
    print("Bot Online\nBen's NFT Bot is active in:")
    for guild in client.guilds:
        print(f"- {guild.id} (name: {guild.name})")
    channel = client.get_channel(mainChannel)
    #await channel.send("Bot Online.")
    global call
    call = api_call.APICall()
    if not activityCallLoop.is_running():
        activityCallLoop.start()
    if not listingsCallLoop.is_running():
        listingsCallLoop.start()  # <---- fix


@client.command()
async def collection_watch(ctx, arg):
    isDuplicate = checkForDuplicates(arg,collectionWatchList)
    if isDuplicate == False:
        exists = call.verifyCollection(arg)
        if exists == True:
            while True:
                embed = discord.Embed(title="Adding to the collection watch list", color=0x0d3fea)
                embed.add_field(name="Collection:",value=arg,inline=False)
                await ctx.send(embed=embed)
                break
            try:
                collectionWatchList.append(arg)
                guild = ctx.message.guild
                await guild.create_text_channel(arg)
                getChannel = discord.utils.get(ctx.guild.channels, name=arg)
                channelID = getChannel.id
                collectionChannels.append([arg,channelID])
            except:
                await ctx.send("Error")
        else:
            while True:
                embed = discord.Embed(title="Error",color=0x0d3fea)
                valueForMessage = arg + "is not found"
                embed.add_field(name="Check your spelling",value=valueForMessage,inline=False)
                await ctx.send(embed=embed)
                break

@client.command()
async def collection_alerts(ctx, arg):
    isDuplicate = checkForDuplicates(arg, collectionAlertsList)
    if isDuplicate == False:
        exists = call.verifyCollection(arg)
        if exists == True:
            while True:
                embed = discord.Embed(title="Adding to the collection alerts list", color=0x0d3fea)
                embed.add_field(name="Collection:", value=arg,inline=False)
                await ctx.send(embed=embed)
                break
            collectionAlertsList.append([arg,0,0])
        else:
            while True:
                embed = discord.Embed(title="Error",color=0x0d3fea)
                valueForMessage = arg + "is not found"
                embed.add_field(name="Check your spelling",value=valueForMessage,inline=False)
                await ctx.send(embed=embed)
                break

@client.command()
async def collection_alerts_remove(ctx, arg):
    try:
        num = 0
        for i in collectionAlertsList:
            if i[0] == arg:
                break
            num += 1
        print("Removing",collectionAlertsList[num])
        del collectionAlertsList[num]
        print("Removed",arg)
        while True:
            embed = discord.Embed(title="Removing...", color=0x0d3fea)
            valueForMessage = arg + " has been removed from the collections alerts list"
            embed.add_field(name="Success", value=valueForMessage, inline=False)
            await ctx.send(embed=embed)
            break
    except Exception as e:
        print(e)
        while True:
            embed = discord.Embed(title="Removing...", color=0x0d3fea)
            valueForMessage = arg + " is not recognised and hasn't been removed"
            embed.add_field(name="Fail", value=valueForMessage, inline=False)
            await ctx.send(embed=embed)
            break

@client.command()
async def collection_watch_remove(ctx, arg):
    try:
        num = 0
        for i in collectionWatchList:
            if i == arg:
                break
            num += 1
        print("Removing",collectionWatchList[num])
        channelToRemove = collectionWatchList[num]
        guild = ctx.message.guild
        del collectionWatchList[num]
        del collectionChannels[num]
        channel = discord.utils.get(guild.channels, name=channelToRemove)
        await channel.delete()
        print("Removed",arg)
        while True:
            embed = discord.Embed(title="Removing...", color=0x0d3fea)
            valueForMessage = arg + " has been removed from the collections alerts list"
            embed.add_field(name="Success", value=valueForMessage, inline=False)
            await ctx.send(embed=embed)
            break
    except Exception as e:
        print(e)
        while True:
            embed = discord.Embed(title="Removing...", color=0x0d3fea)
            valueForMessage = arg + " is not recognised and hasn't been removed"
            embed.add_field(name="Fail", value=valueForMessage, inline=False)
            await ctx.send(embed=embed)
            break

@client.command()
async def list_collections(ctx):
    collections = "List here"
    await ctx.send(collections)


@client.command()
async def help(ctx):
    while True:
        embed = discord.Embed(title="Help",colour=0x0d3fea)
        string = """```collection_watch [collection_name]\nCreates a channel and sends a message every time an NFT out of the collection is bought/sold

collection_alerts [collection_name]\nSends a message in a chosen channel every time the collection's FP or listings go above or below a certain %  
```"""
        embed.add_field(name="Commands",value=string,inline=False)
        await ctx.send(embed=embed)
        break


@tasks.loop(seconds=30.0)  # was 45
async def activityCallLoop():
    global channelID
    try:
        activity = await call.activityCall(collectionWatchList)
        for i in activity:
            while True:
                embed = discord.Embed(title="Magic Eden Activity", description=i[0], color=0x0d3fea)
                embed.set_image(url=i[4])
                embed.add_field(name="Number",value=i[1],inline=True)
                price = str(i[3]) + " Sol"
                embed.add_field(name="Price",value=price,inline=True)
                formattedTime = i[5].strftime("%H:%M:%S ")
                embed.add_field(name="Time", value=formattedTime, inline=True)
                for j in collectionChannels:
                    if j[0] == i[0]:
                        channelID = j[1]
                        break
                channel = client.get_channel(channelID)
                await channel.send(embed=embed)
                break
    except Exception as e:
        print(e)
        print("Discord Activity Loop Error - Continuing in 20...")
        await asyncio.sleep(20)

hourlyReset = 0
halfDailyReset = 0

@tasks.loop(seconds=300) # was 300
async def listingsCallLoop():
    global collectionAlertsList
    global hourlyReset
    global halfDailyReset
    try:
        listings, collectionAlertsListUpdate = await call.listingsCall(collectionAlertsList)
        collectionAlertsList = collectionAlertsListUpdate
        channel = client.get_channel(mainChannel)
        for i in listings:
            if i[0] == 1:  # percDifference message
                while True:
                    embed = discord.Embed(title=("**:bar_chart:" + i[3] + ":bar_chart:**"),color=0x0d3fea)
                    #embed.add_field(name="% Change", value=round(i[1],3),inline=False)
                    formattedTime = i[2]
                    #embed.add_field(name="Since",value=formattedTime[-15:19],inline=False)
                    #embed.add_field(name="FP",value=i[4],inline=False)
                    #embed.add_field(name="Listed",value=i[5],inline=False)
                    string = "**:blue_square: % Change:`" + str(round(i[1], 3)) + "`\n:blue_square: Since:`" + str(
                        formattedTime[-15:19]) + "`\n:blue_square: FP:`" + str(
                        i[4]) + "`\n:blue_square: Listed:`" + str(i[5]) + "`**"
                    embed.add_field(name="Stats:",value=string)
                    await channel.send(embed=embed)
                    break
            elif i[0] == 2:  # percDifference message
                while True:
                    embed = discord.Embed(title=("**:bar_chart:" + i[3] + ":bar_chart:**"),color=0x0d3fea)
                    #embed.add_field(name="% Change", value=round(i[1],3),inline=False)
                    formattedTime = i[2]
                    #embed.add_field(name="Since Yesterday At",value=formattedTime[-15:19],inline=False)
                    #embed.add_field(name="FP",value=i[4],inline=False)
                    #embed.add_field(name="Listed",value=i[5],inline=False)

                    string = "**:blue_square: % Change:`" + str(round(i[1], 3)) + "`\n:blue_square: Since:`" + str(
                        formattedTime[-15:19]) + "`\n:blue_square: FP:`" + str(i[4]) + "`\n:blue_square: Listed:`" + str(i[5]) + "`**"
                    embed.add_field(name="**Stats: (24hr)**",value=string)
                    await channel.send(embed=embed)
                    break
    except Exception as e:
        print(e)
        print("Discord Listings Loop Error - Continuing in 20...")
        await asyncio.sleep(20)
    hourlyReset += 1
    halfDailyReset += 1
    if hourlyReset == 12:  # to prevent spam notifications
        hourlyReset = 0
        for i in collectionAlertsList:
            i[1] = 0
    if halfDailyReset == 144:
        halfDailyReset = 0
        for i in collectionAlertsList:
            i[2] = 0



wait_until_ready.start()
clientRun()
