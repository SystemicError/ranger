import discord, random, time, asyncio

fin = open("token")
print("Reading auth token . . .")
TOKEN = fin.read().strip()
print("Got token '" + TOKEN + "'.")
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
    for user_id in sorted(scoreboard.keys(), key=lambda x: scoreboard[x]["deeds"]):
        if scoreboard[user_id]["deeds"] != 1:
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
        if message.content.lower().startswith('!nhie') or message.content.lower().startswith('!never'):
            print(message.content)
            for reaction in message.reactions:
                if str(reaction) == '\U0000261D':
                    async for user in reaction.users():
                        scoreboard = increment_scoreboard(user.id, scoreboard)
        if message.author == client.user and message.content.endswith("Time to tell us a story!"):
            if len(message.mentions) == 1:
                member = message.mentions[0]
                #print("RANGER mentioned this member:")
                #print(member.id)
                #print("Compare this to the scoreboard:")
                #print(scoreboard)
                increment_stories(member.id, scoreboard)
        if message.content.lower().startswith('!two') or message.content.startswith('!2'):
            print(message.reactions)
    await prompt_stories(client, channel, scoreboard)
    return scoreboard

async def comment_on_nhie(channel):
    fin = open("nhie.comments")
    comments = fin.readlines()
    msg = random.choice(comments)
    await channel.send(msg)

async def background_scan():
    while True:
        print("Scheduled scanning . . .")
        await scan_channel(client)
        print("Completed scan at time:")
        print(time.asctime(time.localtime(time.time())))
        await asyncio.sleep(1800)

async def active_ttaal(channel):
    "Checks if there is an active two truths and a lie already open in this channel."
    first = True
    async for message in channel.history(limit=1000):
        if first:
            first = False
        else:
            if message.author == client.user and message.content.endswith("points this time."):
                return None
            if message.content.lower().startswith("!two") or message.content.startswith("!2"):
                return message
    return None

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

        if message.content.lower().startswith('!nhie') or message.content.lower().startswith('!never'):
            emoji = '\U0000261D'
            await message.add_reaction(emoji)
            if random.random() < 0.1:
                await comment_on_nhie(message.channel)
            else:
                print("Rolled too high.")

        # Two truths and a lie functions
        if message.content.lower().startswith('!two') or message.content.startswith('!2'):
            ttaal = await active_ttaal(message.channel)
            if ttaal == None:
                one = '1⃣'
                two = '2⃣'
                three = '3⃣'
                await message.add_reaction(one)
                await message.add_reaction(two)
                await message.add_reaction(three)
            else:
                print("Found ttaal:" + ttaal.content)
                if ttaal.author.nick == None:
                    nm = ttaal.author.name
                else:
                    nm = ttaal.author.nick
                msg = "I can't do that, {0.author.mention}.  ".format(message) + nm + "'s question is still open for voting."
                await message.channel.send(msg)

        if message.content.lower().startswith("!reveal"):
            ttaal = await active_ttaal(message.channel)
            if ttaal != None:
                if ttaal.author.nick == None:
                    nm = ttaal.author.name
                else:
                    nm = ttaal.author.nick
            if ttaal == None:
                msg = "There's no active question, camper!  You have to start one with !two or !2 first."
                await message.channel.send(msg)
            elif ttaal.author == message.author:
                fields = message.content.lower().split()
                if len(fields) < 2:
                    msg = "You have to reveal a number, camper!"
                    await message.channel.send(msg)
                else:
                    lie = fields[1]
                    if lie == "one" or lie == "1":
                        lie = 1
                    elif lie == "two" or lie == "2":
                        lie = 2
                    elif lie == "three" or lie == "3":
                        lie = 3
                    if not lie in [1, 2, 3]:
                        msg = "I don't recognize that number, camper!"
                        await message.channel.send(msg)
                    else:
                        tricked = []
                        not_tricked = []
                        for reaction in ttaal.reactions:
                            pass
                        msg = "Mystery revealed!  I'm not smart enough to do anything about it, yet.  Some folks probably won some points this time."
                        await message.channel.send(msg)
            else:
                msg = "You can't reveal the answer to " + nm + "'s question, {0.author.mention}!  Wait your turn, please.".format(message)
                await message.channel.send(msg)

        # Superuser commands
        if message.author.id in SUPERUSER_IDS: #superuser IDs
            if message.content.startswith('!shutdown'):
                msg = "Shutting down for now.  See you next camping trip."
                await message.channel.send(msg)
                exit(0)


@client.event
async def on_reaction_add(reaction, user):
    # don't react to own reactions
    if user == client.user:
        return
    # Uncommenting this will cause RANGER launch multiple concurrent scans if !nhies are reacted to in rapid succession.
    #if reaction.emoji == '\U0000261D':
        #print("got finger up reaction to nhie.")
    #    await scan_channel(client)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    client.loop.create_task(background_scan())

client.run(TOKEN)
