import discord, random, time, asyncio, re, datetime

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
DIGIT_EMOJIS = ['1⃣', '2⃣', '3⃣']

def increment_scoreboard(user_id, scoreboard):
    if user_id in scoreboard.keys():
        scoreboard[user_id]["deeds"] += 1
    else:
        scoreboard[user_id] = {"deeds": 1, "stories": 0, "sleuth": 0}
    return scoreboard

def increment_stories(user_id, scoreboard):
    if user_id in scoreboard.keys():
        scoreboard[user_id]["stories"] += 1
    else:
        scoreboard[user_id] = {"deeds": 0, "stories": 1, "sleuth": 0}
    return scoreboard

def increment_sleuth(user_id, scoreboard, count):
    if user_id in scoreboard.keys():
        scoreboard[user_id]["sleuth"] += count
    else:
        scoreboard[user_id] = {"deeds": 0, "stories": 0, "sleuth": count}
    return scoreboard

def scoreboard_string(client, scoreboard):
    msg = "Here is the current scoreboard:\n"
    for user_id in sorted(scoreboard.keys(), key=lambda x: scoreboard[x]["deeds"]):
        if scoreboard[user_id]["deeds"] != 1:
            plural = "s"
        else:
            plural = ""
        if scoreboard[user_id]["sleuth"] != 1:
            sleuth_plural = "s"
        else:
            sleuth_plural = ""
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
        msg = msg + str(nick) + " has confessed " + str(scoreboard[user_id]["deeds"]) + " time" + plural + " and earned " + str(scoreboard[user_id]["sleuth"]) + " lie point" + sleuth_plural + ".\n"
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
            #print(message.content)
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
        if message.author == client.user and message.content.endswith("this time."):
            #print(message.content)
            for user in message.mentions[1:]:
                #print("Sleuth: " + str(user))
                increment_sleuth(user.id, scoreboard, 1)
            points = int(re.search(r" [0-9]+ ", message.content).group(0))
            #print("points: " + str(points))
            #print("Author: " + str(message.mentions[0]))
            increment_sleuth(message.mentions[0].id, scoreboard, points)
    await prompt_stories(client, channel, scoreboard)
    return scoreboard

async def comment_on_nhie(channel):
    fin = open("nhie.comments")
    comments = fin.readlines()
    msg = random.choice(comments)
    await channel.send(msg)

async def active_ttaal(channel, skip=True):
    "Checks if there is an active two truths and a lie already open in this channel."
    first = skip
    recent = None
    async for message in channel.history(limit=1000):
        if first:
            first = False
        else:
            if message.author == client.user and message.content.endswith("this time."):
                return recent
            if message.content.lower().startswith("!two") or message.content.startswith("!2"):
                recent = message
    return recent

async def background_scan():
    channels = client.get_all_channels()
    for c in channels:
        if str(c) == "campfire":
            channel = c
    while True:
        print("Scheduled scanning . . .")
        await scan_channel(client)
        print("Completed scan at time:")
        print(time.asctime(time.localtime(time.time())))
        ttaal = await active_ttaal(channel, skip=False)
        print("Active ttaal:" + str(ttaal))
        if ttaal != None:
            # check in on age of active ttaal
            print("Most recent ttaal:")
            creation = ttaal.created_at
            print(ttaal)
            print("Date:")
            print(creation)
            print("Age:")
            age = datetime.datetime.now() - creation
            print(age)
            if datetime.timedelta(hours=1) < age:
                msg = "{0.author.mention}, remember to !reveal your lie.".format(ttaal)
                await channel.send(msg)
        await asyncio.sleep(1800)

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
                for i in range(3):
                    await message.add_reaction(DIGIT_EMOJIS[i])
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
                    lie = re.search(r"[a-z0-9]+", fields[1]).group()
                    if lie == "one" or lie == "1":
                        lie = 0
                    elif lie == "two" or lie == "2":
                        lie = 1
                    elif lie == "three" or lie == "3":
                        lie = 2
                    if not lie in [0, 1, 2]:
                        msg = "I don't recognize that number, camper!"
                        await message.channel.send(msg)
                    else:
                        liar_points = 0
                        sleuths = {} # user: score
                        for reaction in ttaal.reactions:
                            async for user in reaction.users():
                                if user != client.user and user != ttaal.author:
                                    if str(reaction) == DIGIT_EMOJIS[lie]:
                                        # give a point to this sleuth
                                        if user in sleuths.keys():
                                            sleuths[user] += 1
                                        else:
                                            sleuths[user] = 1
                                    elif str(reaction) in DIGIT_EMOJIS:
                                        # give a point to the liar
                                        liar_points += 1
                                        # deduct a point from this sleuth
                                        if user in sleuths.keys():
                                            sleuths[user] -= 1
                                        else:
                                            sleuths[user] = -1
                        # filter out double-voters as folks whose score is < 1
                        lie_detectors = list(filter(lambda x: sleuths[x] == 1, sleuths.keys()))
                        msg = "Mystery revealed!\n"
                        msg2 = ""
                        if len(lie_detectors) > 0:
                            msg2 = "One point each to these players:  "
                            for lie_detector in lie_detectors:
                                msg2 = msg2 + "{0.mention} ".format(lie_detector)
                            msg2 = msg2 + "\n"
                        if liar_points == 1:
                            plural = ""
                        else:
                            plural = "s"
                        msg3 = "{0.author.mention} won ".format(message) + str(liar_points) + " point" + plural + " this time."
                        await message.channel.send(msg + msg2 + msg3)
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
