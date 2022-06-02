import discord
from discord.ext import commands, tasks

from datetime import datetime
import asyncio

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.stats_lock = asyncio.Lock()
        self.print_stats.start()
        self.upload_stats.start()

    @tasks.loop(hours=1)
    async def print_stats(self):
        async with self.bot.stats_lock:
            print("printing stats")

    @tasks.loop(minutes=10)
    async def upload_stats(self):
        async with self.bot.pool.acquire() as con:
            async with self.bot.stats_lock:
                messages = 0
                for k, v in self.bot.message_count.items():
                    messages += v
                    await con.execute("INSERT INTO channel_messages(datetime, cid, count) VALUES ($1, $2, $3)", datetime.now(), k, v)
                await con.execute("INSERT INTO messages(datetime, count) VALUES($1, $2)", datetime.utcnow(), messages)
                await con.execute("INSERT INTO members(datetime, joins, leaves) VALUES($1, $2, $3)", datetime.utcnow(), self.bot.member_count["join"], self.bot.member_count["leave"])

async def setup(bot):
    bot.add_cog(Tasks(bot))