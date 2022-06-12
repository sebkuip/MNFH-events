import discord
from discord.ext import commands

import random
import typing
import asyncio

def chunker(l, n):
    """Divide list l into n lists"""
    res = []
    for i in range(n):
        res.append(l[i::n])
    return res

class Hogwarts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Assign a candidate to a house or reinstate them")
    @commands.has_permissions(manage_messages=True)
    async def assign(self, ctx, user: discord.Member, house: typing.Optional[str] = None):
        house = house.lower()
        if house and house not in ["gryffindor", "hufflepuff", "slytherin", "ravenclaw"]:
            await ctx.reply("Invalid house")
            return
        async with self.bot.pool.acquire() as conn:
            if house:
                await conn.execute("INSERT INTO users (uid, house, active) VALUES ($1, $2, true) ON CONFLICT (uid) DO UPDATE SET house = $2 AND active = true WHERE uid = $1", user.id, house)
            else:
                await conn.execute("INSERT INTO users (uid, active) VALUES ($1, true) ON CONFLICT (uid) DO UPDATE SET active = true WHERE uid = $1", user.id)
        await ctx.reply(f"{user.mention} has been assigned to {house}")

    @commands.command(help="Remove a user from the event")
    @commands.has_permissions(manage_messages=True)
    async def remove(self, ctx, user: discord.User):
        msg = await ctx.send(f"Are you sure you want to remove {user.mention} from the event?")
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and msg.id == reaction.message.id
        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=30)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.reply("Timed out")

        if str(reaction.emoji) == "✅":
            async with self.bot.pool.acquire() as conn:
                await conn.execute("UPDATE users SET active = false WHERE uid = $1", user.id)
                await ctx.reply(f"{user.mention} has been removed from the event")
            await msg.delete()
        else:
            await msg.delete()
            await ctx.reply("Cancelled")

    @commands.command(help="Assign all users not in a house to a house randomly and evenly")
    @commands.has_permissions(manage_messages=True)
    async def assignall(self, ctx):
        async with self.bot.pool.acquire() as conn:
            users = await conn.fetch("SELECT uid FROM users WHERE house IS NULL AND active = true")
            if len(users) == 0:
                await ctx.reply("No users to assign")
                return
            houses = ["gryffindor", "hufflepuff", "slytherin", "ravenclaw"]
            random.shuffle(users)
            chunks = chunker(users, len(houses))
            for house, users in zip(houses, chunks):
                for user in users:
                    await conn.execute("UPDATE users SET house = $1 WHERE uid = $2", house, user["uid"])
        await ctx.reply("All users assigned")

    @commands.group(help="See info about a house or user", invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def info(self, ctx):
        await ctx.reply("Please specify if you want info about a user or a house")

    @info.command(help="See info about a user")
    @commands.has_permissions(manage_messages=True)
    async def user(self, ctx, user: discord.User):
        async with self.bot.pool.acquire() as conn:
            info = await conn.fetchrow("SELECT * FROM users WHERE uid = $1", user.id)
        if info is None:
            await ctx.reply("User has no record")
            return
        await ctx.reply(f"{user.mention} ({user.id}) is in {info['house']} and status is {'active' if info['active'] else 'inactive'}")

    @info.command(help="See info about a house")
    @commands.has_permissions(manage_messages=True)
    async def house(self, ctx, house: str):
        house = house.lower()
        if house not in ["gryffindor", "hufflepuff", "slytherin", "ravenclaw"]:
            await ctx.reply("Invalid house")
            return
        async with self.bot.pool.acquire() as conn:
            info = await conn.fetchrow("SELECT * FROM houses WHERE house = $1", house)
        if info is None:
            await ctx.reply("This house has no record")
            return
        await ctx.reply(f"{house} has {info['points']} points")

    @commands.command(help="Award points to a house (or deduct with negative values)")
    @commands.has_permissions(manage_messages=True)
    async def award(self, ctx, house: str, points: int, silent: typing.Optional[bool] = False, reason: typing.Optional[str] = None):
        house = house.lower()
        if house not in ["gryffindor", "hufflepuff", "slytherin", "ravenclaw"]:
            await ctx.reply("Invalid house")
            return
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE houses SET points = points + $1 WHERE house = $2", points, house)
        if not silent:
            c = discord.utils.get(ctx.guild.channels, name=house)
            if c is None:
                await ctx.reply(f"{house} has been awarded {points} points" + (f" for {reason}" if reason is not None else ""))
            else:
                await c.send(f"{house} has awarded {points} points" + (f" for {reason}" if reason is not None else ""))

    @commands.command(help="Join the hogwarts event")
    async def reply(self, ctx):
        async with self.bot.pool.acquire() as conn:
            check = await conn.fetchrow("SELECT * FROM users WHERE uid = $1 AND active = false", ctx.author.id)
            if check is not None:
                await ctx.reply("You have already joined the event")
                return
            await conn.execute("INSERT INTO users (uid, active) VALUES ($1, true) ON CONFLICT (uid) DO UPDATE SET (active = true) WHERE uid = $1", ctx.author.id)
        await ctx.reply("You have joined the hogwarts event")

    @commands.command(help="Leave the hogwarts event")
    async def leave(self, ctx):
        async with self.bot.pool.acquire() as conn:
            check = await conn.fetchrow("SELECT * FROM users WHERE uid = $1 AND active = true", ctx.author.id)
            if check is None:
                await ctx.reply("You have not joined the event")
                return

            msg = await ctx.send("Are you sure you want to leave the event?")
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and msg.id == reaction.message.id
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=30)
            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.reply("Timed out")
                return

            if str(reaction.emoji) == "✅":
                await conn.execute("UPDATE users SET active = false WHERE uid = $1", ctx.author.id)
                await msg.delete()
                await ctx.reply("You have left the hogwarts event")
            else:
                await msg.delete()
                await ctx.reply("Cancelled")
                return

async def setup(bot):
    await bot.add_cog(Hogwarts(bot))