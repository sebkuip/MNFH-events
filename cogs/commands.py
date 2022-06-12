import discord
from discord.ext import commands

import typing
import time
import asyncio

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

async def setup(bot):
    await bot.add_cog(Commands(bot))