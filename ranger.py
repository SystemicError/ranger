import discord, random

fin = open("token")
TOKEN = fin.read()
fin.close()

fin = open("superusers")
SUPERUSER_IDS = [int(line) for line in fin.readlines()]
fin.close()

client = discord.Client()

STORY_THRESHHOLD = 10

def increment_scoreboard(user_id, scoreboard):
    if user_id in scoreboard.keys():
        scoreboard[user_id]["deeds"] += 1
    else:
        scoreboard[user_id] = {"deeds": 1, "stories": 0}
    return scoreboard

def increment_stories(user_id, scoreboard):
    if user_id in scoreboard.keys():
        scoreboard[user_id]["stories"] += 1
    else:
        scoreboard[user_id] = {"deeds": 0, "stories": 1}
    return scoreboard

def scoreboard_string(client, scoreboard):
    msg = "Here is the current scoreboard:\n"
    for user_id in scoreboard.keys():
        if scoreboard[user_id] != 1:
            plural = "s"
        else:
            plural = ""
        user = client.get_user(int(user_id))
        members = client.get_all_members()
        member = None
        for m in members:
            if int(m.id) == int(user_id):
                member = m
        if member.nick != None:
            nick = member.nick
        else:
            nick = member.name
        msg = msg + str(nick) + " has confessed " + str(scoreboard[user_id]["deeds"]) + " time" + plural + ".\n"
    return msg


async def prompt_stories(client, channel, scoreboard):
    for user_id in scoreboard.keys():
        deeds = scoreboard[user_id]["deeds"]
        stories = scoreboard[user_id]["stories"]
        if int(deeds / STORY_THRESHHOLD) > stories:
            users = client.users
            for u in users:
                if u.id == user_id:
                    user = u
            msg = "{0.mention}, you have reached a score of ".format(user) + str(scoreboard[user.id]["deeds"]) + ".  Time to tell us a story!"
            if user != client.user:
                await channel.send(msg)

async def scan_channel(client):
    scoreboard = {}
    print("Attempting to read message history:")
    channels = client.get_all_channels()
    for c in channels:
        if str(c) == "campfire":
            channel = c
    async for message in channel.history(limit=10000):
        if message.content.startswith('!nhie') or message.content.startswith('!never') or message.content.startswith('!Never') or message.content.startswith('!Nhie') or message.content.startswith('!NHIE'):
            print(message.content)
            for reaction in message.reactions:
                if str(reaction) == '\U0000261D':
                    async for user in reaction.users():
                        scoreboard = increment_scoreboard(user.id, scoreboard)
        if message.author == client.user and not message.content.startswith("Hello"):
            if len(message.mentions) == 1:
                member = message.mentions[0]
                print("RANGER mentioned this member:")
                print(member.id)
                print("Compare this to the scoreboard:")
                print(scoreboard)
                increment_stories(member.id, scoreboard)
    await prompt_stories(client, channel, scoreboard)
    return scoreboard


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello, {0.author.mention}!'.format(message)
        await message.channel.send(msg)

    if str(message.channel) == "campfire":
        if message.content.startswith('!scoreboard'):
            scoreboard = await scan_channel(client)
            msg = scoreboard_string(client, scoreboard)
            await message.channel.send(msg)

        if message.content.startswith('!nhie') or message.content.startswith('!never') or message.content.startswith('!Never') or message.content.startswith('!Nhie') or message.content.startswith('!NHIE'):
            emoji = '\U0000261D'
            await message.add_reaction(emoji)

        # Superuser commands
        if message.author.id in SUPERUSER_IDS: #superuser IDs
            if message.content.startswith('!shutdown'):
                msg = "Shutting down for now.  See you next camping trip."
                await message.channel.send(msg)
                exit(0)

    print("Found a message with these properties:")
    print(message)
    print("(" + str(message.content) + ")")

@client.event
async def on_reaction_add(reaction, user):
    # don't react to own reactions
    if user == client.user:
        return
    if reaction.emoji == '\U0000261D':
        print("got finger up reaction to nhie.")
        await scan_channel(client)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await scan_channel(client)

client.run(TOKEN)
