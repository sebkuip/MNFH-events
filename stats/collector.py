import discord
from discord.ext import commands

class Collector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.message_count = {}
        self.bot.member_count = {"join": 0, "leave": 0}

    @commands.Cog.listener()
    async def on_message(self, message):
        async with self.bot.stats_lock:
            if message.channel.id in self.bot.member_count.keys():
                self.bot.member_count[message.channel.id] += 1
            else:
                self.bot.member_count[message.channel.id] = 1

    @commands.Cog.listener()
    async def on_member_join(self, _):
        async with self.bot.stats_lock:
            self.bot.member_count["join"] += 1

    @commands.Cog.listener()
    async def on_raw_member_remove(self, _):
        async with self.bot.stats_lock:
            self.bot.member_count["leave"] += 1

async def setup(bot):
    bot.add_cog(Collector(bot))