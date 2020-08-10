"""
Models that map to database tables in tgstation database schema
TODO: investigate SQL alchemy for this?
"""
from collections import namedtuple

DiscordLink = namedtuple('DiscordLink', 'id, ckey, discord_id, timestamp, one_time_token')
