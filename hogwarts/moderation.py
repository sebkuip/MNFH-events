import discord
from discord.ext import commands

import random

def chunker(l, n):
    """Divide list l into n lists"""
    res = []
    for i in range(n):
        res.append(l[i::n])
    return res

class Hogwarts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Assign a candidate to a house")
    @commands.has_permissions(manage_messages=True)
    async def assign(self, ctx, user: discord.Member, house: str):
        house = house.lower()
        if house not in ["gryffindor", "hufflepuff", "slytherin", "ravenclaw"]:
            await ctx.reply("Invalid house")
            return
        async with self.bot.pool.acquire() as conn:
            await conn.execute("INSERT INTO users (uid, house) VALUES ($1, $2) ON CONFLICT (uid) DO UPDATE SET house = $2 WHERE uid = $1", user.id, house)
        await ctx.reply(f"{user.mention} has been assigned to {house}")

    @commands.command(help="Assign all users not in a house to a house randomly and evenly")
    @commands.has_permissions(manage_messages=True)
    async def assignall(self, ctx):
        async with self.bot.pool.acquire() as conn:
            users = await conn.fetch("SELECT uid FROM users WHERE house IS NULL")
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
            info = await conn.fetch("SELECT * FROM users WHERE uid = $1", user.id)
        if info is None:
            await ctx.reply("User has no record")
            return
        await ctx.reply(f"{user.mention} ({user.id}) is in {info['house']}")

    @info.command(help="See info about a house")
    @commands.has_permissions(manage_messages=True)
    async def house(self, ctx, house: str):
        house = house.lower()
        if house not in ["gryffindor", "hufflepuff", "slytherin", "ravenclaw"]:
            await ctx.reply("Invalid house")
            return
        async with self.bot.pool.acquire() as conn:
            info = await conn.fetch("SELECT * FROM houses WHERE house = $1", house)
        if info is None:
            await ctx.reply("This house has no record")
            return
        await ctx.reply(f"{house} has {info['points']} points")

    @commands.command(help="Award points to a house (or deduct with negative values)")
    @commands.has_permissions(manage_messages=True)
    async def award(self, ctx, house: str, points: int):
        house = house.lower()
        if house not in ["gryffindor", "hufflepuff", "slytherin", "ravenclaw"]:
            await ctx.reply("Invalid house")
            return
        async with self.bot.pool.acquire() as conn:
            await conn.execute("UPDATE houses SET points = points + $1 WHERE house = $2", points, house)
        await ctx.reply(f"{house} has been awarded {points} points")

async def setup(bot):
    await bot.add_cog(Hogwarts(bot))