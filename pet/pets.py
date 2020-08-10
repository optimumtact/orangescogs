#Standard Imports
import random

#Discord Imports
import discord

#Redbot Imports
from redbot.core import commands

__version__ = "1.2.1"
__author__ = "oranges"

BaseCog = getattr(commands, "Cog", object)

class Pets(BaseCog):
    def __init__(self, bot):
        self.bot = bot
        self.coffee = [
        "Affogato",
        "Americano",
        "Caffè Latte",
        "Caffè Mocha",
        "Cafè Au Lait",
        "Cappuccino",
        "Double Espresso (doppio)",
        "Espresso",
        "Espresso Con Panna",
        "Espresso Macchiato",
        "Flat White",
        "Frappé",
        "Freakshake",
        "Irish Coffee",
        "Latte Macchiato",
        "Lungo",
        "Ristretto",
        ]
        self.temps = [
        "n iced",
        " steaming hot",
        " disappointingly lukewarm"
        ]

    @commands.command()
    async def pet(self, ctx, *, name: str):
        """
        Pet a user
        """
        await ctx.send("*{} pets {} gently on the head*".format(ctx.author.name, name))

    @commands.command(aliases=["tailpull"])
    async def pull(self, ctx, *, name: str):
        """
        Tail pulling
        """
        await ctx.send("*pulls {}'s tail*".format(name))

    @commands.command(aliases=["tailbrush"])
    async def brush(self, ctx, *, name: str):
        """
        Tail brushing
        """
        await ctx.send("*brushes {}'s tail gently*".format(name))

    @commands.command()
    async def coffee(self, ctx, *, name: str):
        """
        Give a user a nice coffee
        """
        await ctx.send("*{} serves {} a{} {}*".format(ctx.author.name, name, random.choice(self.temps), random.choice(self.coffee)))