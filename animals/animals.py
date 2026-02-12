import logging
import random
import time

import aiohttp
import discord
from redbot.core import Config, checks, commands

__version__ = "1.2.1"
__author__ = "oranges"

BaseCog = getattr(commands, "Cog", object)
log = logging.getLogger("red.oranges_animals")


class Animals(BaseCog):
    def __init__(self, bot):
        self.config = Config.get_conf(
            self, identifier=672261474290237490, force_registration=True
        )
        self.config.register_global(unsplash_key=None)
        self.backoff_until = 0  # Unix timestamp when backoff ends for unsplash api
        self.BACKOFF_SECONDS = 3600  # 1 hour for Unsplash free plan
        self.CACHE_SIZE = 30

        self.sealpulls = [
            "https://file.house/OS90VzacHOCnsZ7XAD9CaA==.gif",
            "https://file.house/H7pnRl6fvsT3oPB7xEkWCA==.gif",
            "https://file.house/-pVo206bX8WbYcKPRoxXUg==.gif",
            "https://file.house/Zg6ZK2ALEKViGVmqVXQlkQ==.gif",
            "https://file.house/GvnqN7AGAw2YT5C4kK3C1w==.gif",
            "https://file.house/T1BeR40guGFFGaWbkvLN-Q==.gif",
            "https://file.house/ZX5CnqPSP1-stcJ40Xd7Mw==.gif",
            "https://file.house/UMeOrP7uExosG2DcHNR_BA==.gif",
            "https://file.house/r9IGIzSr-ojtD_K-og6Cow==.gif",
            "https://file.house/1PuM8EyT9FKWZSlO5L06cg==.gif",
            "https://file.house/REzV-fDkcTujTW1smgR8hQ==.jpg",
        ]

        # Cache: { animal_type: [list_of_urls] }
        self.image_cache = {}

    @commands.command(aliases=["bunny"])
    async def rabbit(self, ctx):
        await self.send_unsplash_image_to_chat("rabbit", ctx)

    @commands.command(aliases=["meow", "pussy"])
    async def cat(self, ctx):
        if random.random() > 0.95:
            await ctx.send(f"Dogs are better, L + bozo")
            await self.send_unsplash_image_to_chat("dog", ctx)
        else:
            await self.send_unsplash_image_to_chat("cat", ctx)

    @commands.command(aliases=["puppy", "thebestpet"])
    async def dog(self, ctx):
        await self.send_unsplash_image_to_chat("dog", ctx)
    
    @commands.command(aliases=["fuzzybumble", "bumblebee"])
    async def bee(self, ctx):
        await self.send_unsplash_image_to_chat("bee", ctx)

    @commands.command(aliases=["wetowl"])
    async def owl(self, ctx):
        await self.send_unsplash_image_to_chat("owl", ctx)

    @commands.command(aliases=["tortise", "turt"])
    async def turtle(self, ctx):
        await self.send_unsplash_image_to_chat("turtle", ctx)

    @commands.command(aliases=["foxy"])
    async def fox(self, ctx):
        if random.random() > 0.99:
            await ctx.send("# RARE FOX PULL")
            await ctx.send("https://file.house/bSMe1dV0J94DdRdFKawovg==.gif")
        else:
            await self.send_unsplash_image_to_chat("fox", ctx)

    @commands.command(aliases=["seal"])
    async def sealed(self, ctx, *, name: str = None):
        """
        the best animal
        """
        if random.randrange(0, 100) < 1:
            await ctx.send("# RARE SEAL PULL")
            await ctx.send("https://file.house/g8LWLYw9iMqeFIceJCttIQ==.gif")
        await ctx.send(
            "{}".format(
                random.choice(self.sealpulls),
            )
        )

    @commands.command()
    @checks.mod_or_permissions(administrator=True)
    async def unsplash(self, ctx, *, unsplash: str):
        """
        Fetch a random unsplash image.
        """
        unsplash = unsplash.strip().lower()
        await self.send_unsplash_image_to_chat(unsplash, ctx)

    @commands.command()
    @checks.is_owner()
    async def setunsplash(self, ctx, key: str):
        """
        Set the Unsplash API key for this cog (owner only).
        """
        await self.config.unsplash_key.set(key.strip())
        await ctx.send("✅ Unsplash API key has been updated.")

    async def send_unsplash_image_to_chat(self, searchquery, ctx, blacklist: list = []):
        image_url = await self.get_unsplash_image(searchquery, blacklist)
        if image_url:
            await ctx.send(image_url)
        else:
            await ctx.send(f"❌ Couldn't fetch images for '{searchquery}' right now.")

    async def fetch_images(self, animal: str, blacklist: list = []):
        """Fetch a fresh random batch of images for the given animal from Unsplash."""
        api_key = await self.config.unsplash_key()
        if not api_key:
            log.info("No api key defined")
            return []
        # If we're in backoff, don't hit the API
        if time.time() < self.backoff_until:
            log.info("Backup limit hit")
            return []
        url = "https://api.unsplash.com/photos/random"
        params = {"query": animal, "count": self.CACHE_SIZE}
        headers = {"Authorization": f"Client-ID {api_key}"}
        log.info("Unsplash API call being made")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as resp:
                log.info("Unsplash API status: %s", resp.status)
                log.debug("Response headers: %s", dict(resp.headers))

                # Grab the text first for debugging
                text_body = await resp.text()
                if len(text_body) > 800:
                    log.debug(
                        "Response body (truncated to 800 chars): %s...", text_body[:800]
                    )
                else:
                    log.debug("Response body: %s", text_body)
                # Check for hard rate-limit errors
                if resp.status == 403 or resp.status == 429:
                    log.info("Api 403 or 429 error, entering backoff")
                    self.backoff_until = time.time() + self.BACKOFF_SECONDS
                    return []

                # Parse rate-limit headers if present
                remaining = resp.headers.get("X-Ratelimit-Remaining")
                if remaining is not None:
                    try:
                        if int(remaining) <= 0:
                            log.info("Rate limit exceeded, entering backoff")
                            self.backoff_until = time.time() + self.BACKOFF_SECONDS
                            return []
                    except ValueError:
                        pass  # Ignore bad header format
                if resp.status != 200:
                    return []
                data = await resp.json()
                if isinstance(data, dict):
                    data = [data]

                photos = []
                for img in data:
                    if "urls" in img:
                        if self._is_blacklisted(img, blacklist):
                            log.debug(
                                f"Image blacklisted: {img.get('description', 'No description')}"
                            )
                            continue
                        photos.append(img["urls"]["full"])
                        log.debug(
                            "Image added to cache: %s",
                            img.get("description", "No description"),
                        )
                return photos

    async def get_unsplash_image(self, searchquery: str, blacklist: list = []):
        """Return a cached image for the given animal, refilling cache if needed."""
        # Initialize cache list if not present
        if searchquery not in self.image_cache:
            self.image_cache[searchquery] = []

        # If cache is empty, refill it
        if not self.image_cache[searchquery]:
            fresh_images = await self.fetch_images(searchquery, blacklist)
            if not fresh_images:
                return None
            # Shuffle to avoid predictable order
            random.shuffle(fresh_images)
            self.image_cache[searchquery].extend(fresh_images)

        # Pop one image from the cache
        return self.image_cache[searchquery].pop()

    def _is_blacklisted(self, photo, blacklist):
        """Check if the photo matches any unwanted keywords."""
        text_fields = [
            photo.get("description") or "",
            photo.get("alt_description") or "",
        ]
        # Some responses include a 'tags' array with title fields
        tags = photo.get("tags", [])
        if isinstance(tags, list):
            for t in tags:
                if isinstance(t, dict) and "title" in t:
                    text_fields.append(t["title"])
                elif isinstance(t, str):
                    text_fields.append(t)

        combined_text = " ".join(text_fields).lower()
        return any(bad.lower() in combined_text for bad in blacklist)
