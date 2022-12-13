from re import L
import discord
from discord.ext import commands
import asyncio

from datetime import datetime

class Elections(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id != int(self.bot.staff_channel):
            return
        async with self.bot.pool.acquire() as con:
            data = await con.fetchrow("SELECT * FROM candidates WHERE verification_message = $1", payload.message_id)
            if data is None or data["verified"] == True:
                return

            if payload.emoji == discord.PartialEmoji.from_str("❌"):
                c = await self.bot.fetch_channel(self.bot.staff_channel)
                m = await c.fetch_message(payload.message_id)
                if m:
                    await m.edit(content=f"<@{data['uid']}> ({data['uid']}) has been rejected by <@{payload.user_id}> ({payload.user_id})", embed=m.embeds[0])
                    await m.clear_reactions()
                await con.execute("DELETE FROM candidates WHERE verification_message = $1", payload.message_id)
                member = await self.bot.fetch_user(data["uid"])
                if member:
                    try:
                        await member.send("Your application has been rejected. Please make sure that you follow our rules and guidelines on any future attempts.")
                    except discord.Forbidden:
                        return

            elif payload.emoji == discord.PartialEmoji.from_str("✅"):
                c = await self.bot.fetch_channel(self.bot.staff_channel)
                m = await c.fetch_message(payload.message_id)
                if m:
                    await m.edit(content=f"<@{data['uid']}> ({data['uid']}) has been accepted by <@{payload.user_id}> ({payload.user_id})", embed=m.embeds[0])
                    await m.clear_reactions()
                await con.execute("UPDATE candidates SET verified = true WHERE verification_message = $1", payload.message_id)
                member = await self.bot.fetch_user(data["uid"])
                if member:
                    try:
                        await member.send("Your application has been accepted. You can now ask people to vote for you.")
                    except discord.Forbidden:
                        return
                channel = await self.bot.fetch_channel(self.bot.channel)
                candidate = await self.bot.fetch_user(data["uid"])
                embed = discord.Embed(title=str(candidate), description=f"You can now vote on this santa.")
                embed.add_field(name="head elf", value="<@" + str(data["first_person"]) + ">", inline=False)
                embed.add_field(name="Speech", value=data["speech"], inline=False)
                await channel.send(f"<@{data['uid']}> is running during this election", embed=embed)

    @commands.command(help="Run for santa")
    async def run(self, ctx):
        async with self.bot.pool.acquire() as con:
            check1 = await con.fetchrow("SELECT uid FROM candidates WHERE uid = $1", ctx.author.id)
            if check1:
                try:
                    await ctx.author.send("You are already running for santa.")
                except discord.Forbidden:
                    await ctx.reply("You are already running for santa.", delete_after=10)
                finally:
                    return

            check2 = await con.fetchrow("SELECT uid FROM candidates WHERE first_person = $1", ctx.author.id)
            if check2:
                try:
                    await ctx.author.send("You are selected as a head elf and thus cannot run for santa.")
                except discord.Forbidden:
                    await ctx.reply("You are selected as a head elf and thus cannot run for santa.", delete_after=10)
                finally:
                    return

            def check(m):
                return m.author == ctx.author and m.guild is None
            try:
                await ctx.author.send("Who is your head elf. Please respond with their userID or mention. Type cancel to cancel")
            except discord.Forbidden:
                await ctx.reply("I need to be able to DM you to ask you a few questions. Please turn on your DMs in your settings.")
                return
            while True:
                try:
                    msg = await self.bot.wait_for('message', check=check, timeout=120)
                    if msg.content.lower() == "cancel":
                        await ctx.author.send("Cancelled")
                        return
                    try:
                        first_person: discord.Member = await commands.MemberConverter().convert(ctx, msg.content)
                        if first_person == ctx.author:
                            await ctx.author.send("You cannot be your own head elf.")
                            continue
                    except commands.BadArgument:
                        await ctx.author.send("That is not a valid userID or mention")
                        continue
                    break
                except asyncio.TimeoutError:
                    await ctx.author.send("You took too long to respond. Please try again.")
                    return

            await ctx.author.send("Please write your speech")
            try:
                while True:
                    speech = await self.bot.wait_for('message', check=check, timeout=300)
                    if speech.content.lower() == "cancel":
                        await ctx.author.send("Cancelled")
                        return
                    if len(speech.content) > 2000:
                        await ctx.author.send("Your speech is too long. Please try again.")
                        continue
                    break
            except asyncio.TimeoutError:
                await ctx.author.send("You took too long to respond. Please try again.")
                return

            embed = discord.Embed(title="Your application", description="Please check your application. React with ✅ to confirm or ❌ to cancel")
            embed.add_field(name="Head elf", value=str(first_person), inline=False)
            embed.add_field(name="Speech", value=speech.content, inline=False)
            embed.set_footer(text="This application will be reviewed by the moderation team after submitting")

            msg = await ctx.author.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=lambda r, u: r.message.id == msg.id and u == ctx.author and r.emoji in ["✅", "❌"], timeout=60)
                    await msg.remove_reaction("✅", self.bot.user)
                    await msg.remove_reaction("❌", self.bot.user)
                except asyncio.TimeoutError:
                    await msg.delete()
                    await ctx.author.send("You took too long to respond. Please try again.")
                    return
                if reaction.emoji == "✅":
                    embed.title = f"New application from {ctx.author}"
                    embed.description = "Please verify this application. React with ✅ to verify or ❌ to deny"
                    embed.set_footer(text=f"Submitted at {datetime.utcnow().strftime('%Y-%m-%d %H:%m')} UTC")

                    c = await self.bot.fetch_channel(int(self.bot.staff_channel))
                    verification_message = await c.send(f"{ctx.author.mention} has submitted an application", embed=embed)
                    await verification_message.add_reaction("✅")
                    await verification_message.add_reaction("❌")
                    await ctx.author.send("Your application has been submitted. Please wait for the moderation team to review it.")
                    await con.execute("INSERT INTO candidates (uid, first_person, speech, verified, verification_message) VALUES ($1, $2, $3, $4, $5)", ctx.author.id, first_person.id, speech.content, False, verification_message.id)
                    return
                elif reaction.emoji == "❌":
                    await msg.delete()
                    await ctx.author.send("Cancelled")
                    return

    @commands.command(help="Vote on a candidate. You may only vote once per election.")
    @commands.dm_only()
    async def vote(self, ctx, candidate: discord.User):
        async with self.bot.pool.acquire() as con:
            check1 = await con.fetchrow("SELECT uid FROM candidates WHERE uid = $1", candidate.id)
            if not check1:
                try:
                    await ctx.author.send("That user is not running for santa.")
                finally:
                    return

            check2 = await con.fetchrow("SELECT uid FROM votes WHERE uid = $1", ctx.author.id)
            if check2:
                try:
                    await ctx.author.send("You have already voted.")
                finally:
                    return

            check3 = await con.fetchrow("SELECT uid FROM candidates WHERE uid = $1", ctx.author.id)
            if check3:
                try:
                    await ctx.author.send("You are running for santa and can't vote.")
                finally:
                    return

            await con.execute("INSERT INTO votes (uid, vote) VALUES ($1, $2)", ctx.author.id, candidate.id)
            try:
                await ctx.author.send("You have voted for " + str(candidate))
            except discord.Forbidden:
                await ctx.reply("You have voted for " + str(candidate), delete_after=20)

async def setup(bot):
    await bot.add_cog(Elections(bot))