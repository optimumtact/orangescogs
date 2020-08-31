"""
Models that map to database tables in tgstation database schema
TODO: investigate SQL alchemy for this?
"""
from collections import namedtuple

BaseLink = namedtuple('DiscordLink', 'id, ckey, discord_id, timestamp, one_time_token, valid')

class DiscordLink(BaseLink):

    @classmethod
    def from_db_record(cls, record):
        #Unpack it
        return cls(**record)
    
    @property
    def validity(self):
        if self.valid > 0:
            return True
        return False
