# Standard Imports
import random

# Discord Imports
import discord

# Redbot Imports
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
        self.temps = ["n iced", " steaming hot", " disappointingly lukewarm"]

        self.quotes = [
            "My vision is augmented.",
            "Well, since that makes you my new boss, take a long look at Manderley's dead body. Consider that my resignation; I don't have time to write a letter.",
            "When due process fails us, we really do live in a world of terror.",
            "You mechs may have copper wiring to reroute your fear of pain, but I've got nerves of steel.",
            "I never had time to take the Oath of Service to the Coalition. How about this one? I swear not to rest until UNATCO is free of you and the other crooked bureaucrats who have perverted its mission.",
            "Call me nostalgic, but the nightlife seems to have lost its old charm.",
            "Some gang-banger, maybe you should think about going back to school.",
            "Bravery is not a function of firepower.",
            "Human beings may not be perfect, but a computer program with language synthesis is hardly the answer to the world's problems.",
            "Every war is the result of a difference of opinion. Maybe the biggest questions can only be answered by the greatest of conflicts."
            "What good's an honest soldier if he can be ordered to behave like a terrorist?",
            "You've got ten seconds to beat it before I add you to the list of NSF casualties.",
            "What a shame.",
            "A forgotten virtue like honesty is worth at least twenty credits.",
            "I'm not big into books.",
            "I'm not going to stand here and listen to you badmouth the greatest democracy the world has ever known.",
            "Maybe you should get a job",
            "Number one: that's terror",
            "I can't spare any arms right now. Please retreat to a safe location.",
            "A BOMB?!",
            "What a shame.",
            "Do you have a single fact to back that up?",
            "You might as well tell me the rest. If I'm gonna kill you, you're already dead.",
            "Sticks and stones...",
            "The crossbow. Sometimes you've got to make a silent takedown.",
        ]

        self.push_attempts = ["pushes", "violently shoves", "playfully pushes", "tries and fails to push", "falls over trying to push"]

    @commands.command()
    async def pet(self, ctx, *, name: str):
        """
        Pet a user
        """
        await ctx.send(
            "*{} pets {} gently on the head*".format(ctx.author.mention, name)
        )

    @commands.command(aliases=["tailpull"])
    async def pull(self, ctx, *, name: str):
        """
        Tail pulling
        """
        await ctx.send("*pulls {}'s tail*".format(name))

    @commands.command()
    async def bite(self, ctx, *, name: str):
        """
        Nom
        """
        await ctx.send(
            "*{} bites {}'s tail softly, nom*".format(ctx.author.mention, name)
        )

    @commands.command()
    async def tailbite(self, ctx, *, name: str):
        """
        Nom
        """
        await ctx.send(
            "*{} bites {}'s tail ferociously and tears it off completely*".format(
                ctx.author.mention, name
            )
        )

    @commands.command(aliases=["taildestroy"])
    async def destroy(self, ctx, *, name: str):
        """
        Ouch
        """
        await ctx.send(
            "*{} picks up {} and spins them like a whirlwind, their tail is ripped off and they fly away in an arc*".format(
                ctx.author.mention, name
            )
        )

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
        await ctx.send(
            "*{} serves {} a{} {}*".format(
                ctx.author.mention,
                name,
                random.choice(self.temps),
                random.choice(self.coffee),
            )
        )

    @commands.command()
    async def throw(self, ctx, *, name: str):
        """
        Throw a coffee at someone
        """
        await ctx.send(
            "*{} makes a{} {} and then picks it up and fucking hurls it at {}'s face*".format(
                ctx.author.mention,
                random.choice(self.temps),
                random.choice(self.coffee),
                name,
            )
        )

    @commands.command()
    async def sticky(self, ctx, *, name: str):
        """
        Give a user a smugly superior sense of self worth
        """
        await ctx.send(
            "*{} serves {} a{} {} with {} milk. How ethical! Is that a hint of smug superiority on the face of {}?*".format(
                ctx.author.mention,
                name,
                random.choice(self.temps),
                random.choice(self.coffee),
                random.choice(self.ethical_alternatives),
                name,
            )
        )

    @commands.command()
    async def ruffle(self, ctx, *, name: str):
        """
        Ruffle their hair
        """
        await ctx.send(
            "*{} ruffles {}'s hair gently, mussing it up a little*".format(
                ctx.author.mention, name
            )
        )

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
        await ctx.send(
            "*{} gathers {} up in their arms and wraps them in a warm hug*".format(
                ctx.author.mention, name
            )
        )

    @commands.command()
    async def fine(self, ctx, *, name: str):
        """
        You so, fucking FINE
        """
        await ctx.send(
            "{} you are fined one credit for violation of the textual morality statutes".format(
                name
            )
        )

    @commands.command()
    async def denton(self, ctx, *, name: str = None):
        """
        JC, A BOMB
        """
        if name:
            message = f"{name}: {random.choice(self.quotes)}"
        else:
            message = f"{random.choice(self.quotes)}"

        await ctx.send(message)

    @commands.command(aliases=["entwine"])
    async def tailentwine(self, ctx, *, name: str):
        """
        Cat!
        """
        await ctx.send(
            "*{} wraps their tail around {}'s tail*".format(
                ctx.author.mention, name
            )
        )
    @commands.command(aliases=["push"])
    async def push(self, ctx, *, name: str):
        """
        *pushes u*
        """
        await ctx.send(
            "*{} {} {} over!*".format(
                ctx.author.mention, random.choice(self.push_attempts), name
            )
        )
