#Standard Imports
import asyncio
import aiomysql
import socket
import ipaddress
import re
import logging

#Discord Imports
import discord

#Redbot Imports
from redbot.core import commands, checks, Config
from redbot.core.utils.chat_formatting import pagify, box, humanize_list, warning
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from tgcommon.models import tgschema
from aiomysql.sa import create_engine


__version__ = "1.0.0"
__author__ = "oranges"

log = logging.getLogger("red.oranges_tgdb")

BaseCog = getattr(commands, "Cog", object)

class TGDB(BaseCog):
    """
    Connector that will integrate with any database using the latest tg schema, provides utility functionality
    """
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=672261474290237490, force_registration=True)
        ## Stores all our configured database pools (if you use this bot for multiple servers)
        ## They're indexed by a config key
        self.database_pools = dict()
        self.visible_config = ["mysql_host", "mysql_port", "mysql_user", "mysql_db", "mysql_prefix",
        "min_living_minutes", "verified_role"]

        default_guild = {
            "mysql_host": "127.0.0.1",
            "mysql_port": 3306,
            "mysql_user": "ss13",
            "mysql_password": "password",
            "mysql_db": "database",
            "mysql_prefix": "",
            "min_living_minutes": 60,
            "verified_role": None,
        }

        self.config.register_guild(**default_guild)
        self.pool = None

    @commands.guild_only()
    @commands.group()
    @checks.admin_or_permissions(administrator=True)
    async def tgdb_config(self,ctx):
        """
        SS13 Configure the MySQL database connection settings
        """
        pass

    @commands.guild_only()
    @commands.group()
    @checks.is_owner()
    async def tgdb(self,ctx):
        """
        SS13 Configure the MySQL database connection settings
        """
        pass

    @tgdb.command()
    async def reconnect(self, ctx):
        """
        Recreate the pool (for when it dies)
        """
        await self.reconnect_to_db_with_guild_context_config(ctx)
        await ctx.send(f"Database Connected")

    @tgdb_config.command()
    @checks.is_owner()
    async def host(self, ctx, db_host: str):
        """
        Sets the MySQL host, defaults to localhost (127.0.0.1)
        """
        try:
            await self.config.guild(ctx.guild).mysql_host.set(db_host)
            await ctx.send(f"Database host set to: `{db_host}`")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the database's ip/hostname. Please check your entry and try again!")


    @tgdb_config.command()
    @checks.is_owner()
    async def port(self, ctx, db_port: int):
        """
        Sets the MySQL port, defaults to 3306
        """
        try:
            if 1024 <= db_port <= 65535: # We don't want to allow reserved ports to be set
                await self.config.guild(ctx.guild).mysql_port.set(db_port)
                await ctx.send(f"Database port set to: `{db_port}`")
            else:
                await ctx.send(f"{db_port} is not a valid port!")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting your port. Please check to ensure you're attempting to use a port from 1024 to 65535")


    @tgdb_config.command(aliases=['name', 'user'])
    @checks.is_owner()
    async def username(self, ctx, user: str):
        """
        Sets the user that will be used with the MySQL database. Defaults to SS13

        It's recommended to ensure that this user cannot write to the database
        """
        try:
            await self.config.guild(ctx.guild).mysql_user.set(user)
            await ctx.send(f"User set to: `{user}`")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the username for your database.")


    @tgdb_config.command()
    @checks.is_owner()
    async def password(self, ctx, passwd: str):
        """
        Sets the password for connecting to the database

        This will be stored locally, it is recommended to ensure that your user cannot write to the database
        """
        try:
            await self.config.guild(ctx.guild).mysql_password.set(passwd)
            await ctx.send("Your password has been set.")
            try:
                await ctx.message.delete()
            except(discord.DiscordException):
                await ctx.send("I do not have the required permissions to delete messages, please remove/edit the password manually.")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the password for your database.")


    @tgdb_config.command(aliases=["db"])
    @checks.is_owner()
    async def database(self, ctx, db: str):
        """
        Sets the database to login to, defaults to feedback
        """
        try:
            await self.config.guild(ctx.guild).mysql_db.set(db)
            await ctx.send(f"Database set to: `{db}`")
        except (ValueError, KeyError, AttributeError):
            await ctx.send ("There was a problem setting your notes database.")


    @tgdb_config.command()
    @checks.is_owner()
    async def prefix(self, ctx, prefix: str = None):
        """
        Sets the database prefix (if applicable)

        Leave blank to remove this option
        """
        try:
            if prefix is None:
                await self.config.guild(ctx.guild).mysql_prefix.set("")
                await ctx.send(f"Database prefix removed!")
            else:
                await self.config.guild(ctx.guild).mysql_prefix.set(prefix)
                await ctx.send(f"Database prefix set to: `{prefix}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting your database prefix")


    @checks.mod_or_permissions(administrator=True)
    @tgdb_config.command()
    async def current(self, ctx):
        """
        Gets the current settings for the notes database
        """
        settings = await self.config.guild(ctx.guild).all()
        embed=discord.Embed(title="__Current settings:__")
        for k, v in settings.items():
            # Ensures that the database password is not sent
            # Whitelist for extra safety
            if k in self.visible_config:
                if v == "":
                    v = None
                embed.add_field(name=f"{k}:",value=v,inline=False)
            else:
                embed.add_field(name=f"{k}:",value="`redacted`",inline=False)
        await ctx.send(embed=embed)

    @checks.mod_or_permissions(administrator=True)
    @commands.command()
    async def test(self, ctx):
        """
        Gets the current settings for the notes database
        """
        cur = await self.pool.acquire()
        res = await cur.execute(tgschema.discord_links.select())
        for row in (await res.fetchall()):
            print(row.id, row.one_time_token)

    async def update_discord_link(self, ctx, one_time_token: str, user_discord_snowflake: str):
        """
        Given a one time token, and a discord user snowflake, insert the snowflake for the matching record in the discord links table
        """
        prefix = await self.config.guild(ctx.guild).mysql_prefix()
        query = f"UPDATE {prefix}discord_links SET discord_id = %s, valid = TRUE WHERE one_time_token = %s AND timestamp >= Now() - INTERVAL 4 HOUR AND discord_id IS NULL"
        parameters = [user_discord_snowflake, one_time_token]
        query = await self.query_database(ctx, query, parameters)

    async def lookup_ckey_by_token(self, ctx, one_time_token: str):
        """
        Given a one time token, search the {prefix}discord_links table for that one time token and return the ckey it's connected to
        checks that the timestamp of the one time token has not exceeded 4 hours (hence expired) or there is no discord_id associated
        to that one time key already (it has been used), or it is has not been set to invalid
        """
        prefix = await self.config.guild(ctx.guild).mysql_prefix()
        query = f"SELECT ckey FROM {prefix}discord_links WHERE one_time_token = %s AND timestamp >= Now() - INTERVAL 4 HOUR AND discord_id IS NULL ORDER BY timestamp DESC LIMIT 1";
        parameters = [one_time_token]
        results = await self.query_database(ctx, query, parameters)
        if len(results):
            return results[0]["ckey"]

    async def discord_link_for_discord_id(self, ctx, discord_id):
        """
        Given a valid discord id, return the latest record linked to that user
        """
        prefix = await self.config.guild(ctx.guild).mysql_prefix()
        query = f"SELECT * FROM {prefix}discord_links WHERE discord_id = %s AND ckey IS NOT NULL ORDER BY timestamp DESC LIMIT 1";
        parameters = [discord_id]
        results = await self.query_database(ctx, query, parameters)
        if len(results):
            return DiscordLink.from_db_record(results[0])

        return None

    async def discord_link_for_ckey(self, ctx, ckey):
        """
        Given a valid ckey, return the latest record linked to that user
        """
        prefix = await self.config.guild(ctx.guild).mysql_prefix()
        query = f"SELECT * FROM {prefix}discord_links WHERE ckey = %s AND discord_id IS NOT NULL ORDER BY timestamp DESC LIMIT 1";
        parameters = [ckey]
        results = await self.query_database(ctx, query, parameters)
        if len(results):
            return DiscordLink.from_db_record(results[0])

        return None

    async def clear_all_valid_discord_links_for_ckey(self, ctx, ckey):
        """
        Set the valid field to false for all links for the given ckey
        """
        prefix = await self.config.guild(ctx.guild).mysql_prefix()
        query = f"UPDATE {prefix}discord_links SET valid = FALSE WHERE ckey = %s AND valid = TRUE";
        parameters = [ckey]
        results = await self.query_database(ctx, query, parameters)

    async def clear_all_valid_discord_links_for_discord_id(self, ctx, discord_id):
        """
        Set the valid field to false for all links for the given discord id
        """
        prefix = await self.config.guild(ctx.guild).mysql_prefix()
        query = f"UPDATE {prefix}discord_links SET valid = FALSE WHERE discord_id = %s AND valid = TRUE";
        parameters = [discord_id]
        results = await self.query_database(ctx, query, parameters)

    async def all_discord_links_for_ckey(self, ctx, ckey):
        """
        Given a valid ckey, return a list of all the valid records in the discord_links table for this user as discord link records
        ordered by timestamp descending
        """
        prefix = await self.config.guild(ctx.guild).mysql_prefix()
        query = f"SELECT * FROM {prefix}discord_links WHERE ckey = %s AND discord_id IS NOT NULL ORDER BY TIMESTAMP desc";
        parameters = [ckey]
        discord_links = list()
        results = await self.query_database(ctx, query, parameters)
        for result in results:
            discord_links.append(DiscordLink.from_db_record(result))
        return discord_links

    async def get_player_by_ckey(self, ctx, ckey: str):
        """
        Given a ckey, look up the player and return some useful information we use to calculate if we can verify this user or not, (do they have
        an appropriate amount of living time)
        """
        prefix = await self.config.guild(ctx.guild).mysql_prefix()
        query = f"SELECT ckey, firstseen, lastseen, computerid, ip, accountjoindate FROM {prefix}player WHERE ckey=%s"
        query = await self.query_database(ctx, query, [ckey])
        results = {}
        try:
            query = query[0] # Checks to see if a player was found, if the list is empty nothing was found so we return the empty dict.
        except IndexError:
            return None

        results['ip'] = ipaddress.IPv4Address(query['ip']) #IP's are stored as a 32 bit integer, converting it for readability
        results['cid'] = query['computerid']
        results['ckey'] = query['ckey']
        results['first'] = query['firstseen']
        results['last'] = query['lastseen']
        results['join'] = query['accountjoindate']

        #Obtain role time statistics
        query = f"SELECT job, minutes FROM {prefix}role_time WHERE ckey=%s AND (job='Ghost' OR job='Living')"
        try:
            query = await self.query_database(ctx, query, [ckey])
        except aiomysql.Error:
            query = None
        if query:
            for job in query:
                if job['job'] == "Living":
                    results['living_time'] = job['minutes']
                else:
                    results['ghost_time'] = job['minutes']

            if 'living_time' not in results.keys():
                results['living_time'] = 0
            if 'ghost_time' not in results.keys():
                results['ghost_time'] = 0

        else:
            results['living_time'] = 0
            results['ghost_time'] = 0

            results['total_time'] = results['living_time'] + results['ghost_time']

        return results

    async def reconnect_to_db_with_guild_context_config(self, ctx):
        db = await self.config.guild(ctx.guild).mysql_db()
        db_host = socket.gethostbyname(await self.config.guild(ctx.guild).mysql_host())
        db_port = await self.config.guild(ctx.guild).mysql_port()
        db_user = await self.config.guild(ctx.guild).mysql_user()
        db_pass = await self.config.guild(ctx.guild).mysql_password()
        await self.reconnect_to_db(db, db_host, db_port, db_user, db_pass)

    async def reconnect_to_db(self, db, db_host, db_port, db_user, db_pass):
        '''
        Open a connection to the database and save the pool in use
        '''
        # Database options loaded from the config
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

        # Establish a connection with the database and pull the relevant data, recycle them every 300 seconds
        self.pool = await aiomysql.sa.create_engine(host=db_host,port=db_port,db=db,user=db_user,password=db_pass, connect_timeout=5, pool_recycle=300)

    async def query_database(self, ctx, query: str, parameters: list):
        '''
        Use our active pool to pass in the given query
        '''
        if not self.pool:
            await self.reconnect_to_db_with_guild_context_config(ctx)
            raise TGUnrecoverableError("The database was not connected,  a reconnect was attempted")

        try:
            log.debug(f"Executing query {query}, with parameters {parameters}")
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, parameters)
                    rows = cur.fetchall()
                    # WRITE TO STORAGE LOL
                    await conn.commit()
                    return rows.result()

        except:
            raise

