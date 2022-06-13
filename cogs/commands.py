from ast import alias
import discord
from discord.ext import commands

import typing
import time
import random

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Shows the latency the bot is experiencing")
    async def ping(self, ctx):
        before = time.perf_counter()
        msg = await ctx.reply("testing...", mention_author=False)
        await msg.edit(content=f"pong!\nbot latency: {round((time.perf_counter() - before) * 1000)}ms\nwebsocket latency: {round(self.bot.latency * 1000)}ms")

    @commands.command(help="Send a message as the bot")
    @commands.has_permissions(manage_messages=True)
    async def echo(
        self, ctx, channel: typing.Optional[discord.TextChannel] = None, *, text
    ):
        if channel is None:
            channel = ctx.channel
        await channel.send(text)
        await ctx.message.delete()

    @commands.command(help="Assign or remove a role to/from a user")
    @commands.has_permissions(manage_messages=True)
    async def role(self, ctx, member: discord.Member, role: discord.Role):
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.reply(f"Removed {role.name} from {member.mention} ({member.id})", mention_author=False)
        else:
            await member.add_roles(role)
            await ctx.reply(f"Added {role.name} to {member.mention} ({member.id})", mention_author=False)

    @commands.command(help="Change the bot's activity")
    @commands.has_permissions(manage_messages=True)
    async def activity(self, ctx, *, activity: str):
        await self.bot.change_presence(activity=discord.CustomActivity(activity))
        await ctx.reply(f"Activity changed to {activity}")

    @commands.command(help="Roll the dice", aliases=["rtd", "rollthedice"])
    async def dice(self, ctx, *, dice: typing.Optional[str] = None):
        if "d" in dice:
            dice = dice.split("d")
            if len(dice) == 2:
                dice[0] = int(dice[0])
                dice[1] = int(dice[1])
                if dice[0] > 0 and dice[1] > 0:
                    result = 0
                    for _ in range(dice[0]):
                        result += random.randint(1, dice[1])
                    await ctx.reply(f"You rolled {dice[0]}d{dice[1]} and got {result}")
            else:
                await ctx.reply("Invalid dice format")
        elif dice is not None:
            try:
                await ctx.reply(f"You rolled {random.randint(1, int(dice))}")
            except ValueError:
                await ctx.reply("Invalid dice format")
        else:
            await ctx.reply(f"You rolled {random.randint(1, 6)}")

async def setup(bot):
    await bot.add_cog(Commands(bot))