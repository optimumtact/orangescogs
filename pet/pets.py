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
        self.ethical_alternatives = [
            "Soy",
            "Oat",
            "Almond",
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
        await ctx.send("*{} pets {} gently on the head*".format(ctx.author.mention, name))

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
        await ctx.send("*{} serves {} a{} {}*".format(ctx.author.mention, name, random.choice(self.temps), random.choice(self.coffee)))

    @commands.command()
    async def throw(self, ctx, *, name: str):
        """
        Throw a coffee at someone
        """
        await ctx.send("*{} makes a{} {} and then picks it up and fucking hurls it at {}'s face*".format(ctx.author.mention, random.choice(self.temps), random.choice(self.coffee), name))

    @commands.command()
    async def sticky(self, ctx, *, name: str):
        """
        Give a user a smugly superior sense of self worth
        """
        await ctx.send("*{} serves {} a{} {} with {} milk. How ethical! Is that a hint of smug superiority on the face of {}?*".format(ctx.author.mention, name, random.choice(self.temps), random.choice(self.coffee), random.choice(self.ethical_alternatives), name))

    @commands.command()
    async def ruffle(self, ctx, *, name: str):
        """
        Ruffle their hair
        """
        await ctx.send("*{} ruffles {}'s hair gently, mussing it up a little*".format(ctx.author.mention, name))

    @commands.command()
    async def bap(self, ctx, *, name: str):
        """
        Bap!!!
        """
        await ctx.send("*{} baps {} on the head*".format(ctx.author.mention, name))
    
    @commands.command()
    async def hug(self, ctx, *, name: str):
        """
        hug, awww!!!
        """
        await ctx.send("*{} gathers {} up in their arms and wraps them in a warm hug*".format(ctx.author.mention, name))
