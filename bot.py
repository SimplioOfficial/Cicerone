#!/usr/bin/env python3
# Work with Python 3.7+

from discord.ext import tasks
import discord
import logging
import json
import asyncio
from pycoingecko import CoinGeckoAPI


logging.basicConfig(format="%(asctime)s | %(levelname)s:%(name)s:%(message)s",
                    filename='cicerone.log', level=logging.INFO)
logging.info('----- Started -----')

with open("auth.json") as data_file:
    auth = json.load(data_file)
with open("links.json") as data_file:
    data = json.load(data_file)


TOKEN = auth["token"]
BOT_PREFIX = "!"
TICKER = "SIO"


intents = discord.Intents(messages=True, guilds=True)
intents.reactions = True
intents.members = True
intents.emojis = True
intents.presences = True
intents.typing = False

client = discord.Client(intents=intents)
cg = CoinGeckoAPI()


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def save_diary_file(message):
    with open("dev-diary.json") as data_file:
        listed = json.load(data_file)
    listed.append(message)
    file = open("dev-diary.json", "w")
    file.write(json.dumps(listed, indent=2, sort_keys=True, default=str))
    file.close()


@tasks.loop(minutes=6)
# task runs every 6 minutes
async def update_members():
    await client.wait_until_ready()
    guild = client.get_guild(859581142159065128)
    total_channel = client.get_channel(887310034969710623)
    online_channel = client.get_channel(887310070088605766)
    while not client.is_closed():
        widget = await guild.widget()
        online_members = len(widget.members)
        total_members = guild.member_count
        await total_channel.edit(name=f"Total Members: {total_members}")
        await online_channel.edit(name=f"Online Members: {online_members}")


@tasks.loop(minutes=6)
# task runs every 7 minutes
async def update_price():
    await client.wait_until_ready()
    guild = client.get_guild(859581142159065128)
    price_channel = client.get_channel(887306329759297577)
    while not client.is_closed():
        sol_price = cg.get_price(ids='solana', vs_currencies='usd')[
            "solana"]["usd"]
        await price_channel.edit(name=f"SOL Price: {sol_price}$")


@client.event
async def on_message(msg):
    # Bot will save all the messages in #💻-dev-diary channel into a text file
    if msg.channel.id == 882693892254859274:

        dictionar = {}
        dictionar["author"] = msg.author.name
        dictionar["created_at"] = msg.created_at
        dictionar["content"] = msg.content
        for i in range(len(msg.embeds)):
            key = "embed_" + str(i)
            dictionar[key] = msg.embeds[i].to_dict()
        message = dictionar
        save_diary_file(message)
        return
    # We do not want the bot to respond to Bots or Webhooks
    if msg.author.bot:
        return
    # We want the bot to not answer to messages that have no content
    # (example only attachment messages)
    # Bot checks BOT_PREFIX
    if not msg.content or msg.content[0] != BOT_PREFIX:
        return
    # Bot ignore all system messages
    if msg.type is not discord.MessageType.default:
        return

    args = msg.content[1:].split()
    cmd = args[0].lower()

    # Bot runs in #🤖-bot-commands channel and private channels for everyone
    # Bot runs in all channels for specific roles
    if not (
        isinstance(msg.channel, discord.DMChannel)
        or msg.channel.name == "🤖-bot-commands"
        or "cicerone" in [role.name for role in msg.author.roles]
    ):
        message = f"{data['default']}"
        await msg.channel.send(message)
        return

    # -------- <help> --------
    elif cmd == "help":
        message = "\n".join(data["help"])
    # -------- <about> --------
    elif cmd == "about":
        message = "\n".join(data["about"])
    # -------- <ban(Amitabha only)> --------
    elif (
        cmd == "ban"
        and isinstance(msg.channel, discord.TextChannel)
        and msg.author.id == 359782573066551320
    ):
        if len(args) < 2:
            message = (
                f"Input a substring of users to ban, like `!ban SiO` will ban all users containing"
                + f" `SiO` in their names (_fuction is case-sensitive_)."
            )
            await msg.channel.send(message)
            return
        cmd1 = args[1]
        member = discord.utils.find(
            lambda m: cmd1 in m.name, msg.channel.guild.members)
        if member is None:
            count = 0
        else:
            count = 1
        while not (member is None):
            await msg.channel.guild.ban(member)
            member = discord.utils.find(
                lambda m: cmd1 in m.name, msg.channel.guild.members)
            if not (member is None):
                count += 1
        message = f"Banned {count} members! Nice!"
    # -------- <del(Amitabha only)> --------
    elif (
        cmd == "del"
        and isinstance(msg.channel, discord.TextChannel)
        and msg.author.id == 359782573066551320
    ):
        if len(args) < 2:
            message = "Enter the number of messages to delete"
            await msg.channel.send(message)
            return
        cmd1 = args[1]
        deleted = await msg.channel.purge(limit=int(cmd1))
        message = f"Deleted {len(deleted)} message(s)"

    else:
        message = f"{data['unknown']}"

    await msg.channel.send(message)


@client.event
async def on_raw_reaction_add(payload):
    guild = client.get_guild(859581142159065128)
    role = guild.get_role(882347739357249576)
    mbr = guild.get_member(payload.user_id)

    if (payload.message_id == 882670328097169458 and payload.emoji.name == "Simplio"):
        await mbr.add_roles(role)


@client.event
async def on_raw_reaction_remove(payload):
    guild = client.get_guild(859581142159065128)
    role = guild.get_role(882347739357249576)
    mbr = guild.get_member(payload.user_id)

    if (payload.message_id == 882670328097169458 and payload.emoji.name == "Simplio"):
        await mbr.remove_roles(role)


@client.event
async def on_member_join(mbr):
    for ban_word in data["banned_words"]:
        if mbr.guild.get_member(mbr.id) is not None and ban_word in mbr.name:
            await mbr.ban()
            logging.warning(f'Banned {mbr.name} with id: {mbr.id}')
            return


@client.event
async def on_member_update(before, after):
    # Bot ignore all members that have MEMBER_ID in ignored_ids list
    if after.id in data["ignored_ids"]:
        return
    for ban_word in data["banned_words"]:
        if after.guild.get_member(after.id) is not None and ban_word in after.name:
            await after.ban()
            logging.warning(f'Banned {after.name} with id: {after.id}')
            return


@client.event
async def on_ready():
    print(f"Logged in as: {client.user.name} {{{client.user.id}}}")

update_members.start()
update_price.start()
client.run(TOKEN)
logging.info('----- Finished -----')
