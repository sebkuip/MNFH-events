import discord
from discord.ext import commands
from discord import app_commands

activities = {
            "Watch Together": 880218394199220334,
            "Poker Night": 755827207812677713,
            "Betrayal.io": 773336526917861400,
            "Fishington.io": 814288819477020702,
            "Chess In The Park": 832012774040141894,
            "Sketch Heads": 902271654783242291,
            "Letter League": 879863686565621790,
            "Word Snacks": 879863976006127627,
            "SpellCast": 852509694341283871,
            "Checkers In The Park": 832013003968348200,
            "Blazing 8s": 832025144389533716,
            "Putt Party": 945737671223947305,
            "Land-io": 903769130790969345,
            "Bobble League": 947957217959759964,
            "Ask Away": 976052223358406656,
            "Know What I Meme": 950505761862189096,
            "Bash Out": 1006584476094177371
        }

class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx):
        res = await self.bot.tree.sync()
        await ctx.reply(f"synced: {res}")

    class ActivityTransformer(app_commands.Transformer):
        async def transform(self, interaction: discord.Interaction, value: str) -> int:
            return (value, activities[value])

    @app_commands.command(name="activities", description="Create an invite to start an activity")
    async def activities(self, interaction: discord.Interaction, channel: discord.VoiceChannel, activity: ActivityTransformer):
        invite = await channel.create_invite(target_type=discord.InviteTarget.embedded_application, target_application_id=activity[1])
        await interaction.response.send_message(f"[Click here to start {activity[0]} in {channel.mention}](<{invite}>)")

    @activities.autocomplete("activity")
    async def activity_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=name, value=name)
            for name in activities.keys()
            if name.lower().startswith(current.lower())
        ]

async def setup(bot):
    await bot.add_cog(Activities(bot))
