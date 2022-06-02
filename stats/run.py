import asyncpg
import discord
from discord.ext import commands

from dotenv import load_dotenv
import os
from os import getenv

load_dotenv(".env")
token = getenv("TOKEN")

activity = discord.Activity(type=discord.ActivityType.custom, name=f"s! | Counting messages")
bot = commands.Bot(intents=discord.Intents.all(), command_prefix="s!", case_insensitive=True, activity=activity)
bot.channel = getenv("CHANNEL")
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
                status[extension] = "x"
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

@bot.command(help="Load a cog")
@commands.is_owner()
async def load(ctx, extension):
    await ctx.send(f"loading cog {extension}")
    try:
        await bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"loaded cog {extension}")
    except Exception as e:
        await ctx.send(f"Failed to load extension {extension}. {e}")
        await ctx.send(e)
        print(f"Failed to load extension {extension}.")
        print(e)


@bot.command(help="Unload a cog")
@commands.is_owner()
async def unload(ctx, extension):
    await ctx.send(f"unloading cog {extension}")
    try:
        await bot.unload_extension(f"cogs.{extension}")
        await ctx.send(f"unloaded cog {extension}")
    except Exception as e:
        await ctx.send(f"Failed to unload extension {extension}. {e}")
        await ctx.send(e)
        print(f"Failed to unload extension {extension}.")
        print(e)


@bot.command(help="Reload a cog")
@commands.is_owner()
async def reload(ctx, name):
    name = name.lower()
    await ctx.send(f"reloading cog {name}")
    await bot.unload_extension(f"cogs.{name}")
    try:
        await bot.load_extension(f"cogs.{name}")
        await ctx.send(f"reloaded cog {name}")
    except Exception as e:
        print(f"Failed to load extension {name}.")
        print(e)
        await ctx.send(e)

bot.run(token)