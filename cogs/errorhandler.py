import discord
from discord.ext import commands

import traceback

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if hasattr(ctx.command, "on_error"):
            return

        error = getattr(error, "original", error)

        embed = discord.Embed(
            title=f"```***AN ERROR OCCURED***```",
            description=f"Uh oh, something went wrong. The following error appeared:",
            color=discord.Color.red(),
        )
        embed.set_thumbnail(url="https://i.imgur.com/R7ib9Fu.png")

        if isinstance(error, FileNotFoundError):
            return
        elif isinstance(error, commands.NotOwner):
            embed.add_field(
                name=f"**NotOwner**",
                value=f"Looks like you are not the owner of the bot and cannot use this command. "
                f"Developers only >:(",
            )
        elif isinstance(error, commands.MemberNotFound):
            embed.add_field(
                name=f"**MemberNotFound**",
                value=f"Looks like you tried to mention a user that doesn't exist. "
                f"Please try again.",
            )
        elif isinstance(error, commands.BadArgument):
            embed.add_field(
                name=f"**BadArgument**",
                value=f"Looks like you entered a wrong argument. Please check carefully. Maybe the "
                f"channel or user does not exist?\nIf this was an infraction, please manually add "
                f"the infraction to the database.",
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            # embed.add_field(name=f'**MissingRequiredArgument**',
            # value=f'Looks like you forgot to enter an argument for this command.')
            await ctx.send(
                f"Command usage: `>{ctx.command.name} {ctx.command.signature}`"
            )
            return
        elif isinstance(error, commands.CommandNotFound):
            embed.add_field(name=f"CommandNotFound", value=f"```{error}```")
        elif isinstance(error, commands.MissingPermissions):
            embed.add_field(
                name=f"**MissingPermissions**",
                value=f"Looks like you do not have the permission to execute the command.",
            )
        elif isinstance(error, commands.BotMissingPermissions):
            embed.add_field(
                name=f"**BotMissingPermissions**",
                value=f"Looks like the bot is missing permissions to execute this command.",
            )
        elif isinstance(error, discord.Forbidden):
            return
        elif isinstance(error, commands.UnexpectedQuoteError):
            return
        # elif isinstance(error, discord.ext.commands.errors.CommandInvokeError):
        # embed.add_field(name=f'**CommandInvokeError**',
        # value=f'Looks like something is wrong with the command. This could be because the page '
        # f'does not exist.')
        else:
            embed.add_field(
                name=f"**UnknownError**",
                value=f"An unknown error has appeared, check console",
            )
            traceback.print_exception(error)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))