import logging
import requests
import datetime

from django.utils.timezone import now
from django.utils.timesince import timesince

from .models import IGDBGame
from .igdb_api import IGDB


def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
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
        self.created_at = None
        self.time_since = None
        self.type = None
        self.is_foobar = False
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
        if self.type == 0:
            self.details = self.activity_info['details'] if 'details' in self.activity_info.keys() else ''
            self.application_id = self.activity_info['application_id']
            # Get url for images
            if 'assets' in self.activity_info.keys():
                self.large_image = self.get_image_link(self.activity_info['assets']['large_image']) \
                    if 'large_image' in self.activity_info['assets'].keys() else None
                self.small_image = self.get_image_link(self.activity_info['assets']['small_image']) \
                    if 'small_image' in self.activity_info['assets'].keys() else None
            else:
                # First check if the game has been cached
                game = IGDBGame.objects.filter(name=self.name).first()
                if game and not game.needs_update():
                    logging.debug(f"[Lanyard] Game {self.name} found in cache")
                    self.large_image = game.cover
                    self.small_image = None
                else:
                    # Find game image by name
                    logging.debug(f"[Lanyard] Game {self.name} not found in cache")
                    igdb = IGDB()
                    game_info = igdb.search_game(self.name)
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
        # check if foobar
        self.foobar()

    def foobar(self):
        if self.name == "foobar2000":
            self.is_foobar = True
            self.artist = self.details
            self.title = self.state[:self.state.rindex("{") - 1]
            self.length = self.state[self.state.rindex("{") + 1:self.state.rindex("}")]
            if 'timestamps' in self.activity_info.keys():
                self.str_progress = f"{format_timedelta(now() - self.created_at)} / {self.length}"
                self.progress = ((now() - self.created_at).total_seconds() /
                                 datetime.timedelta(
                                     minutes=int(self.length.split(":")[0]),
                                     seconds=int(self.length.split(":")[1])).total_seconds() * 100)
            else:
                self.str_progress = "Paused"
                self.progress = 100

    def get_image_link(self, image_id: str):
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

    def get_info(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            return DiscordPresence(response.json())
        else:
            return None

    def get_dict(self):
        info = self.get_info()
        if info is not None:
            return {
                'user': {
                    'username': info.user.username,
                    'avatar': info.user.avatar,
                    'display_name': info.user.display_name
                },
                'activities': info.activities
            }
