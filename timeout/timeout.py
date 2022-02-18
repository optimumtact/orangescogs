# Standard Imports
from collections import defaultdict
import json
import logging
from typing import DefaultDict, Dict, Union, Any


# Redbot Imports
from redbot.core import commands, checks, Config
from datetime import datetime, timedelta
import discord
from discord.errors import Forbidden
import re
from collections import namedtuple

__version__ = "1.1.0"
__author__ = "oranges"

log = logging.getLogger("red.oranges_timeout")

BaseCog = getattr(commands, "Cog", object)


#(c) Will Roberts  14 April, 2014
#The regex and formatting code comes from the very useful https://github.com/wroberts/pytimeparse/blob/master/pytimeparse/timeparse.py
#released under MIT and reproduced here

class TimeFormat():
    DAYS = r'(?P<days>[\d.]+)\s*(?:d|dys?|days?)'
    MINS = r'(?P<mins>[\d.]+)\s*(?:m|(mins?)|(minutes?))'
    HOURS = r'(?P<hours>[\d.]+)\s*(?:h|hrs?|hours?)'
    TIMEFORMATS = [
    fr'{DAYS}\s*{HOURS}\s*{MINS}',
    fr'{DAYS}\s*{MINS}',
    fr'{DAYS}\s*{HOURS}',
    fr'{HOURS}\s*{MINS}',
    fr'{MINS}',
    fr'{HOURS}',
    fr'{DAYS}',
    ]

    COMPILED_TIMEFORMATS = [re.compile(r'\s*' + timefmt + r'\s*$', re.I)
                        for timefmt in TIMEFORMATS]
    def __init__(self, timedict:dict):
        self.time = timedict
    
    def __init__(self, formatstr:str):
        #So we always have the relevant keys (defaulting to zero)
        for timefmt in self.COMPILED_TIMEFORMATS:
            match = timefmt.match(formatstr)
            if match and match.group(0).strip():
                mdict = match.groupdict()
                for key in ('mins', 'days', 'hours'):
                    if key in mdict:
                        mdict[key] = int(mdict[key])
                    else:
                        mdict[key] = 0
                self.time = mdict
                return
        
        raise discord.ext.commands.BadArgument(f'{formatstr} is not a valid time format')
    
    def get_timedelta(self):
        return timedelta(self.time['days'], 0, 0, 0, self.time['mins'], self.time['hours'])

    def to_config(self) -> str:
        return json.dumps(self.time)

    @staticmethod
    def from_config(jsonstr: str):
        timedict = json.loads(jsonstr)
        return TimeFormat(f"{timedict['days']}d{timedict['hours']}h{timedict['mins']}m")
        
    def __str__(self) -> str:
        return str(self.get_timedelta())
    
class Timeout(BaseCog):
    """
    Timeout module
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=672261474290237490, force_registration=True
        )
        self.visible_config = [
            "enabled",
            "role_max"
        ]

        default_guild = {
            "enabled": True,
            "role_max": {},
        }

        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.group()
    @checks.mod_or_permissions(administrator=True)
    async def timeout(self, ctx):
        """
        Timeout module
        """
        pass

    @commands.guild_only()
    @timeout.group()
    @checks.mod_or_permissions(administrator=True)
    async def config(self, ctx):
        """
        Configure the timeout module
        """
        pass

    @config.command()
    async def current(self, ctx):
        """
        Gets the current settings for the verification system
        """
        settings = await self.config.guild(ctx.guild).all()
        embed: discord.Embed = discord.Embed(title="__Current settings:__")
        for k, v in settings.items():
            # Hide any non whitelisted config settings (safety moment)
            if k in self.visible_config:
                if v == "":
                    v = None
                embed.add_field(name=f"{k}:", value=v, inline=False)
            else:
                embed.add_field(name=f"{k}:", value="`redacted`", inline=False)
        await ctx.send(embed=embed)

    @config.command()
    async def role(self, ctx, role: discord.Role, max_time_str: TimeFormat):
        """
        Sets the maximum amount of days the role can time out users for

        TimeFormats can be in the form of (d = days, h = hours, m = minutes)
        1d3h5m
        1d3h
        1d5m
        5h3m
        5h
        3m
        """
        try:
            roles = await self.config.guild(ctx.guild).role_max()
            roleid = str(role.id)
            
            roles[roleid] = max_time_str.to_config()
            log.error(f'New roles dict {roles}')
            if max_time_str.get_timedelta() == timedelta(0):
                del roles[roleid]
                await ctx.send(f"Role {role} permissions removed")
            else:
                await ctx.send(f"Role {role} can now only set a maximum of {max_time_str} timeout")

            await self.config.guild(ctx.guild).role_max.set(roles)
            
        except (ValueError, KeyError, AttributeError) as e:    
            await ctx.send(
                "There was a problem setting the maximum timeout for this role"
            )
            raise e
    
    @config.command()
    async def enable(self, ctx):
        """
        Enable the plugin
        """
        try:
            roles = await self.config.guild(ctx.guild).enabled.set(True)
            await ctx.send(f"The module is now enabled")
            
        except (ValueError, KeyError, AttributeError):
            await ctx.send(
                "There was a problem enabling the module"
            )

    @timeout.command()
    async def remove(self, ctx, user: discord.Member):
        """
        remove any timeout on the targeted user
        """
        enabled = await self.config.guild(ctx.guild).enabled()
        if not enabled:
            await ctx.send("This module is not enabled")
            return
              
        reason = f'Timeout removed by {ctx.author}'
        payload: Dict[str, Any] = {}
        my_date: datetime = datetime.now()
        payload['communication_disabled_until'] = None
        try:
            data = await ctx.bot.http.edit_member(user.guild.id, user.id, reason=reason, **payload)
            await ctx.send(f"Timeout has been removed")
        except (Forbidden):
            await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("I do not have permission to time members out")

    @timeout.command()
    async def apply(self, ctx, user: discord.Member, days:TimeFormat):
        """
        Time out the targeted user for a given number of days (limits to role max automatically)


        TimeFormats can be in the form of (d = days, h = hours, m = minutes)
        1d3h5m
        1d3h
        1d5m
        5h3m
        5h
        3m
        """
        log.debug(f"Timeout command string {days}")
        log.debug(f"Converted to timedelta {days.get_timedelta()}")
        days = days.get_timedelta()
        enabled = await self.config.guild(ctx.guild).enabled()
        if not enabled:
            await ctx.send("This module is not enabled")
            return
        role_max_dict = await self.config.guild(ctx.guild).role_max()
        max_days = timedelta(0)
        for role in ctx.author.roles:
            roleid = str(role.id)
            if roleid in role_max_dict:
                possible_new_max = TimeFormat.from_config(role_max_dict[roleid]).get_timedelta()
                log.debug(f"found role with max days {possible_new_max}")
                max_days = max(max_days, possible_new_max)
        
        
        time_to_timeout = max(timedelta(0), min(days, max_days, timedelta(28)))
        log.debug(f"Post calculations {days}, {max_days}, {time_to_timeout}")
        if time_to_timeout == timedelta(0): 
            await ctx.send("You are not authorised to time users out")
            return
        
        
        reason = f'Requested timeout by {ctx.author} for {time_to_timeout}'
        payload: Dict[str, Any] = {}
        my_date: datetime = datetime.now() + time_to_timeout
        payload['communication_disabled_until'] = my_date.isoformat()
        try:
            data = await ctx.bot.http.edit_member(user.guild.id, user.id, reason=reason, **payload)
            await ctx.send(f"User has been timed out for {time_to_timeout}")
        except (Forbidden):
            #await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("I do not have permission to time members out")
