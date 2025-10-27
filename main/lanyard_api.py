import logging

import aiohttp
import requests
import datetime

from django.utils.timezone import now
from django.utils.timesince import timesince

from .models import IGDBGame
from .igdb_api import IGDB


def format_timedelta(td):
    # Format a timedelta to H:MM:SS or M:SS
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes}:{seconds:02}"



class DiscordUser:
    def __init__(self, user_info: dict):
        self.user_info = user_info
        self.id = None
        self.username = None
        self.avatar = None
        self.display_name = None
        self.parse()

    def parse(self):
        self.id = self.user_info['id']
        self.username = self.user_info['username']
        self.avatar = f"https://cdn.discordapp.com/avatars/{self.id}/{self.user_info['avatar']}.webp"
        self.display_name = self.user_info['display_name']


class RichPresenceActivity:
    def __init__(self, activity_info: dict):
        self.activity_info = activity_info
        self.id = None
        self.name = None
        self.state = None
        self.details = None
        self.application_id = None
        self.large_image = None
        self.small_image = None
        self.large_alt = None
        self.small_alt = None
        self.created_at = None
        self.time_since = None
        self.type = None
        self.parse()

    def parse(self):
        self.type = self.activity_info['type']
        self.id = self.activity_info['id']
        self.name = self.activity_info['name']
        self.state = self.activity_info['state'] if 'state' in self.activity_info.keys() else ''
        if 'timestamps' in self.activity_info.keys() and 'start' in self.activity_info['timestamps'].keys():
            self.created_at = datetime.datetime.fromtimestamp(
                self.activity_info['timestamps']['start'] / 1000, tz=now().tzinfo
            )
        else:
            self.created_at = datetime.datetime.fromtimestamp(self.activity_info['created_at'] / 1000, tz=now().tzinfo)
        # get time since
        self.time_since = timesince(self.created_at, now())

        # Get url and alt text for images
        if 'assets' in self.activity_info.keys():
            self.large_image = self.get_image_link(self.activity_info['assets'].get('large_image'))
            self.small_image = self.get_image_link(self.activity_info['assets'].get('small_image'))
            self.large_alt = self.activity_info['assets'].get('large_text', self.state)
            self.small_alt = self.activity_info['assets'].get('small_text', self.state)

        if self.type == 0:  # Playing...
            self.details = self.activity_info['details'] if 'details' in self.activity_info.keys() else ''
            self.application_id = self.activity_info['application_id'] if 'application_id' in self.activity_info.keys() else ''

            if not self.large_image:
                # First check if the game has been cached
                game = IGDBGame.objects.filter(name=self.name).first()
                if game:
                    logging.debug(f"[Lanyard] Game {self.name} found in cache")
                    if game.needs_update():
                        logging.debug(f"[Lanyard] Game {self.name} needs update, getting image from IGDB")
                        igdb = IGDB()
                        cover = igdb.get_game_cover(game.igdb_id)
                        game.cover = cover
                        game.save()
                    self.large_image = game.cover
                    self.small_image = None
                else:
                    # Find game image by name
                    logging.debug(f"[Lanyard] Game {self.name} not found in cache")
                    igdb = IGDB()
                    # Filter out all non-alphanumeric characters and replace the rest with spaces
                    sanitized_name = ''.join(e if e.isalnum() else ' ' for e in self.name)
                    game_info = igdb.search_game(sanitized_name)
                    if game_info:
                        self.large_image = igdb.get_game_cover(game_info[0]['id'])
                        self.small_image = None
                        # Cache game
                        if game:
                            game.cover = self.large_image
                            game.save()
                        else:
                            IGDBGame.objects.create(
                                name=self.name,
                                cover=self.large_image,
                                igdb_id=game_info[0]['id']
                            )

        elif self.type == 2:  # Listening to...
            # Get all music-specific info
            self.title = self.activity_info.get('details')
            self.artist = self.activity_info.get('state')
            self.album = self.large_alt if self.large_alt else ''  # Sometimes album is in large_alt

        elif self.type == 3:  # Watching...
            self.details = self.activity_info.get('details', '')

        if self.type == 2 or self.type == 3:
            # Calculate the progress if timestamps are available
            if 'timestamps' in self.activity_info.keys():
                start = self.activity_info['timestamps'].get('start')
                end = self.activity_info['timestamps'].get('end')
                if start and end:
                    current = now() - datetime.datetime.fromtimestamp(start / 1000, tz=now().tzinfo)
                    total = (
                            datetime.datetime.fromtimestamp(end / 1000, tz=now().tzinfo) -
                            datetime.datetime.fromtimestamp(start / 1000, tz=now().tzinfo)
                    )
                    self.str_progress = f"{format_timedelta(current)} / {format_timedelta(total)}"
                    self.progress = current.total_seconds() / total.total_seconds() * 100
                else:
                    self.str_progress = None


    def get_image_link(self, image_id: str):
        if not image_id:
            return None
        if image_id.startswith("mp:external"):
            link = f"https://images-ext-1.discordapp.net/external/{image_id[image_id.index('/') + 1:]}"
        else:
            link = f"https://cdn.discordapp.com/app-assets/{self.application_id}/{image_id}.png"
        return link


class DiscordPresence:
    def __init__(self, presence_info: dict):
        self.presence_info = presence_info['data']
        self.user = None
        self.activities = []
        self.parse()

    def parse(self):
        self.user = DiscordUser(self.presence_info['discord_user'])
        for activity in self.presence_info['activities']:
            self.activities.append(RichPresenceActivity(activity))


class Lanyard:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.url = f"https://api.lanyard.rest/v1/users/{self.user_id}"

    async def get_info(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                if response.status == 200:
                    return DiscordPresence(await response.json())
                else:
                    return None


    async def get_dict(self):
        info = await self.get_info()
        if info is not None:
            return {
                'user': {
                    'username': info.user.username,
                    'avatar': info.user.avatar,
                    'display_name': info.user.display_name
                },
                'activities': info.activities
            }
        else:
            return {
                'user': None,
                'activities': []
            }
