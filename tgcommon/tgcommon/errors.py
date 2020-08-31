#Discord Imports
import discord

#Redbot Imports
from redbot.core import commands, checks, Config

#Subtype the commands checkfailure
class TGRecoverableError(commands.CheckFailure):
    pass

class TGUnrecoverableError(commands.CheckFailure):
    pass
