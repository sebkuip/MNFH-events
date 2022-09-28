import asyncpg
import discord
from discord.ext import commands

from dotenv import load_dotenv
import os
from os import getenv

load_dotenv(".env")
token = getenv("TOKEN")
guild_id = getenv("GUILD")

class MyBot(commands.Bot):
    def __init__(self):
        activity = discord.Activity(type=discord.ActivityType.custom, name=f"& | Running events")
        self.guild_id = guild_id
        super().__init__(intents=discord.Intents.all(), command_prefix="&", case_insensitive=True, activity=activity)

bot = MyBot()
bot.staff_channel = getenv("STAFF_CHANNEL")
bot.role = getenv("ROLE")

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    print(f"Username is {bot.user.name}")
    print(f"ID is {bot.user.id}")
    print(f"Keep this window open to keep the bot running.")

    # database
    print("Connecting to database")
    await get_db()

    # extensions
    await load_extensions()

async def get_db():
    HOST=getenv("HOST")
    PORT=getenv("PORT")
    DATABASE=getenv("DATABASE")
    USER=getenv("USER")
    PASSWORD=getenv("PASSWORD")
    bot.pool = await asyncpg.create_pool(
        host=HOST, port=PORT, database=DATABASE, user=USER, password=PASSWORD
    )

    async with bot.pool.acquire() as con:
        result = await con.fetchrow("SELECT version()")
        db_version = result[0]
        print(f"Database version: {db_version}")


async def load_extensions():
    if __name__ == "__main__":

        status = {}
        for extension in os.listdir("./cogs"):
            if extension.endswith(".py"):
                status[extension] = "X"
        errors = []

        for extension in status:
            if extension.endswith(".py"):
                try:
                    await bot.load_extension(f"cogs.{extension[:-3]}")
                    status[extension] = "L"
                except Exception as e:
                    errors.append(e)

        maxlen = max(len(str(extension)) for extension in status)
        for extension in status:
            print(f" {extension.ljust(maxlen)} | {status[extension]}")
        print(errors) if errors else print("no errors during loading")
        print("loading p-loaded extensions")
        async with bot.pool.acquire() as con:
            groups = await con.fetch("SELECT * FROM pload")
            if len(groups) == 0:
                print("No p-loaded extensions")
            else:
                status = {}
                for group in groups:
                    for extension in os.listdir(f"./{group['name']}"):
                        if extension.endswith(".py"):
                            status[group['name'] + "." + extension] = "X"
                errors = []
                for extension in status:
                    try:
                        await bot.load_extension(f"{extension[:-3]}")
                        status[extension] = "L"
                    except Exception as e:
                        errors.append(e)
                maxlen = max(len(str(extension)) for extension in status)
                for extension in status:
                    print(f" {extension.ljust(maxlen)} | {status[extension]}")
                print(errors) if errors else print("no errors during loading")
        await bot.load_extension('jishaku')

@bot.command(help="Perma load a cog group")
@commands.is_owner()
async def pload(ctx, name):
    name = name.lower()
    async with bot.pool.acquire() as con:
        await con.execute("INSERT INTO pload (name) VALUES ($1) ON CONFLICT (name) DO NOTHING", name)
    status = {}
    for extension in os.listdir(f"./{name}"):
        if extension.endswith(".py"):
            status[extension] = "X"
    errors = []

    for extension in status:
        if extension.endswith(".py"):
            try:
                await bot.load_extension(f"{name}.{extension[:-3]}")
                status[extension] = "L"
            except Exception as e:
                errors.append(e)

    maxlen = max(len(str(extension)) for extension in status)
    extensionstatus = ""
    for extension in status:
        extensionstatus += (f" {extension.ljust(maxlen)} | {status[extension]}\n")
    embed = discord.Embed(title=f"load report of {name}", description=extensionstatus, color=0x00ff00 if not errors else 0xFF0000)
    if errors:
        embed.add_field(name="Errors", value=str(errors))
    await ctx.send(embed=embed)

@bot.command(help="Perma unload a cog group")
@commands.is_owner()
async def punload(ctx, name):
    name = name.lower()
    async with bot.pool.acquire() as con:
        await con.execute("DELETE FROM pload WHERE name = $1", name)
    status = {}
    for extension in os.listdir(f"./{name}"):
        if extension.endswith(".py"):
            status[extension] = "X"
    errors = []

    for extension in status:
        if extension.endswith(".py"):
            try:
                await bot.unload_extension(f"{name}.{extension[:-3]}")
                status[extension] = "U"
            except Exception as e:
                errors.append(e)

    maxlen = max(len(str(extension)) for extension in status)
    extensionstatus = ""
    for extension in status:
        extensionstatus += (f" {extension.ljust(maxlen)} | {status[extension]}\n")
    embed = discord.Embed(title=f"Unload report of {name}", description=extensionstatus, color=0x00ff00 if not errors else 0xFF0000)
    if errors:
        embed.add_field(name="Errors", value=str(errors))
    await ctx.send(embed=embed)

@bot.command(help="Load a cog")
@commands.is_owner()
async def load(ctx, name):
    name = name.lower()
    status = {}
    for extension in os.listdir(f"./{name}"):
        if extension.endswith(".py"):
            status[extension] = "X"
    errors = []

    for extension in status:
        if extension.endswith(".py"):
            try:
                await bot.load_extension(f"{name}.{extension[:-3]}")
                status[extension] = "L"
            except Exception as e:
                errors.append(e)

    maxlen = max(len(str(extension)) for extension in status)
    extensionstatus = ""
    for extension in status:
        extensionstatus += (f" {extension.ljust(maxlen)} | {status[extension]}\n")
    embed = discord.Embed(title=f"load report of {name}", description=extensionstatus, color=0x00ff00 if not errors else 0xFF0000)
    if errors:
        embed.add_field(name="Errors", value=str(errors))
    await ctx.send(embed=embed)


@bot.command(help="Unload a cog")
@commands.is_owner()
async def unload(ctx, name):
    name = name.lower()
    status = {}
    for extension in os.listdir(f"./{name}"):
        if extension.endswith(".py"):
            status[extension] = "X"
    errors = []

    for extension in status:
        if extension.endswith(".py"):
            try:
                await bot.unload_extension(f"{name}.{extension[:-3]}")
                status[extension] = "U"
            except Exception as e:
                errors.append(e)

    maxlen = max(len(str(extension)) for extension in status)
    extensionstatus = ""
    for extension in status:
        extensionstatus += (f" {extension.ljust(maxlen)} | {status[extension]}\n")
    embed = discord.Embed(title=f"Unload report of {name}", description=extensionstatus, color=0x00ff00 if not errors else 0xFF0000)
    if errors:
        embed.add_field(name="Errors", value=str(errors))
    await ctx.send(embed=embed)


@bot.command(help="Reload a cog")
@commands.is_owner()
async def reload(ctx, name):
    name = name.lower()
    status = {}
    for extension in os.listdir(f"./{name}"):
        if extension.endswith(".py"):
            status[extension] = "X"
    errors = []

    for extension in status:
        if extension.endswith(".py"):
            try:
                await bot.reload_extension(f"{name}.{extension[:-3]}")
                status[extension] = "R"
            except Exception as e:
                errors.append(e)

    maxlen = max(len(str(extension)) for extension in status)
    extensionstatus = ""
    for extension in status:
        extensionstatus += (f" {extension.ljust(maxlen)} | {status[extension]}\n")
    embed = discord.Embed(title=f"Reload report of {name}", description=extensionstatus, color=0x00ff00 if not errors else 0xFF0000)
    if errors:
        embed.add_field(name="Errors", value=str(errors))
    await ctx.send(embed=embed)

@bot.command(help="Show all loaded cogs")
@commands.is_owner()
async def loaded(ctx):
    embed = discord.Embed(title="Loaded cogs", description="\n".join(bot.cogs), color=0x00ff00)
    await ctx.reply(embed=embed, mention_author=False)

bot.run(token)