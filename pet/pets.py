#Standard Imports
import socket
import ipaddress
import re
import logging
import random

#Discord Imports
import discord

#Redbot Imports
from redbot.core import commands, checks, Config

__version__ = "1.2.0"
__author__ = "oranges"

log = logging.getLogger("red.SS13GetNotes")

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

    @commands.command()
    async def pet(self, ctx, *, name: str):
        """
        Pet a user
        """
        message = await ctx.send("{} pets {} gently on the head".format(ctx.author.name, name))

    @commands.command()
    async def coffee(self, ctx, *, name: str):
        """
        Give a user a nice coffee
        """
        message = await ctx.send("{} serves {} a steaming hot {}".format(ctx.author.name, name, random.choice(self.coffee)))
