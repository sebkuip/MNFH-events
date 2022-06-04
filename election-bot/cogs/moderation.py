import discord
from discord.ext import commands
import asyncio

import time
import datetime
import typing

class Moderation(commands.Cog):
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

    @commands.command(help="Get info for a user")
    @commands.has_permissions(manage_messages=True)
    async def info(self, ctx, user: discord.User):
        async with self.bot.pool.acquire() as con:
            vote = await con.fetchrow("SELECT * FROM votes WHERE uid = $1", user.id)
            candidate = await con.fetchrow("SELECT * FROM candidates WHERE uid = $1", user.id)
            president = await con.fetch("SELECT * FROM presidents WHERE uid = $1", user.id)

            embeds = []
            if vote:
                embed = discord.Embed(title="Vote info", description=f"{user} has voted for <@{vote['vote']}> ({vote['vote']})", color=0x00ff00)
                embeds.append(embed)

            if candidate:
                embed = discord.Embed(title="Candidate info", description=f"{user} is running for office", color=0x00ff00)
                embed.add_field(name="fist person", value=f"<@{candidate['first_person']}> ({candidate['first_person']})", inline=False)
                embed.add_field(name="speech", value=candidate['speech'], inline=False)
                embeds.append(embed)

            if president:
                embed = discord.Embed(title=f"{user} has been elected {len(president)} times", color=0x00ff00)
                for i, p in enumerate(president):
                    if i == 25:
                        embed.add_field(name="too much data for discord to show", value="\u200b")
                        break
                    embed.add_field(name=f"id: {i}", value=p['date'])
                embeds.append(embed)

            if len(embeds) > 0:
                await ctx.reply(embed=embeds[0], mention_author=False)
            else:
                await ctx.reply("User has no info", mention_author=False)

    @commands.group(help="End an election, tally votes and announce the winner", invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def tally(self, ctx):
        async with self.bot.pool.acquire() as con:
            candidates = await con.fetch("SELECT * FROM candidates")
            if candidates is None or len(candidates) == 0:
                await ctx.reply("No candidates to tally", mention_author=False)
                return
            votecount = {}
            total = 0
            for candidate in candidates:
                m = await ctx.guild.fetch_member(candidate['uid'])
                if m is None:
                    continue
                votecount[candidate['uid']] = await con.fetchval("SELECT COUNT(*) FROM votes WHERE vote = $1", candidate['uid'])
                votecount[candidate['uid']] += candidate['misc_votes']
                total += votecount[candidate['uid']]

            winner = max(votecount, key=votecount.get)

            message = await ctx.reply(f"The winner is <@{winner}> ({winner}) with {votecount[winner]} votes. Do you wish to elect them?", mention_author=False)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            try:
                r, _ = await self.bot.wait_for("reaction_add", check=lambda r, u: u.id == ctx.author.id and r.message.id == message.id and r.emoji in ["✅", "❌"], timeout=60)
            except asyncio.TimeoutError:
                await message.delete()
                return
            if r.emoji == "✅":
                await con.execute("INSERT INTO presidents (uid, date) VALUES ($1, $2)", winner, datetime.datetime.utcnow())
                await con.execute("DELETE FROM candidates")
                await con.execute("DELETE FROM votes")
                c = await self.bot.fetch_channel(self.bot.channel)
                m = await ctx.guild.fetch_member(winner)
                r = ctx.guild.get_role(self.bot.role)
                await m.add_roles(r)
                await c.send(f"<@{winner}> has been elected president with {round(votecount[winner] / total * 100, 2)}% of the votes")
            elif r.emoji == "❌":
                await ctx.reply("Tally cancelled", mention_author=False)
                return

    @tally.command(help="Get a list of all candidates and their votes")
    @commands.has_permissions(manage_messages=True)
    async def list(self, ctx):
        msg = await ctx.reply("Counting votes...", mention_author=False)
        async with ctx.typing():
            async with self.bot.pool.acquire() as con:
                candidates = await con.fetch("SELECT * FROM candidates")
                if candidates is None or len(candidates) == 0:
                    await ctx.reply("No candidates to tally", mention_author=False)
                    return
                votecount = {}
                total = 0
                for candidate in candidates:
                    try:
                        m = await ctx.guild.fetch_member(candidate['uid'])
                    except discord.NotFound:
                        continue
                    votecount[candidate['uid']] = await con.fetchval("SELECT COUNT(*) FROM votes WHERE vote = $1", candidate['uid'])
                    votecount[candidate['uid']] += candidate['misc_votes']
                    total += votecount[candidate['uid']]

                body = ""
                i = 1
                for k, v in sorted(votecount.items(), key=lambda item: item[1], reverse=True):
                    body += f"{i}. <@{k}> ({k}) - {v} votes\n"
                    i+=1
                embed = discord.Embed(title="Candidates", description=body, color=0x00ff00)
                await msg.edit(content="", embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def remove(self, ctx):
        await ctx.reply("Please specify a sub-command to remove", mention_author=False)

    @remove.command(help="Remove a candidate")
    @commands.has_permissions(manage_messages=True)
    async def candidate(self, ctx, user: discord.User):
        async with self.bot.pool.acquire() as con:
            uid = await con.fetchrow("DELETE FROM candidates WHERE uid = $1 RETURNING uid", user.id)
            if uid:
                await con.execute("DELETE FROM votes WHERE vote = $1", user.id)
                await ctx.reply("Removed candidate", mention_author=False)
            else:
                await ctx.reply("Candidate not found", mention_author=False)

    @remove.command(help="Remove a vote from a specific user")
    @commands.has_permissions(manage_messages=True)
    async def vote(self, ctx, user: discord.User):
        async with self.bot.pool.acquire() as con:
            uid = await con.fetchrow("DELETE FROM votes WHERE uid = $1 RETURNING uid", user.id)
            if uid:
                await ctx.reply("Removed vote", mention_author=False)
            else:
                await ctx.reply("Vote not found", mention_author=False)


async def setup(bot):
    await bot.add_cog(Moderation(bot))