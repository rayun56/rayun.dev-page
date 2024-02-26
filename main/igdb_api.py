import os
import requests
import datetime
import logging

from dotenv import load_dotenv
from django.utils.timezone import now

from .models import IGDBCredential


class IGDB:
    def __init__(self):
        self.access_token = None
        self.client_id = None
        cred = IGDBCredential.objects.first()  # type: IGDBCredential
        if cred and not cred.is_expired():
            logging.debug('[IGDB] Using cached IGDB credentials')
            self.access_token = cred.access_token
            self.client_id = cred.client_id
        else:
            self._get_access_token()
        self.api_url = 'https://api.igdb.com/v4'
        self.headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.access_token}'
        }

    def _get_access_token(self):
        load_dotenv()
        self.client_id = os.getenv('IGDB_CLIENT_ID')
        client_secret = os.getenv('IGDB_CLIENT_SECRET')
        auth_url = 'https://id.twitch.tv/oauth2/token'
        data = {
            'client_id': self.client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
        response = requests.post(auth_url, params=data)
        self.access_token = response.json()['access_token']
        if IGDBCredential.objects.first():
            IGDBCredential.objects.first().delete()
        IGDBCredential.objects.create(
            access_token=self.access_token,
            client_id=self.client_id,
            expires=now() + datetime.timedelta(seconds=response.json()['expires_in'])
        )

    def search_game(self, query: str):
        url = f'{self.api_url}/games'
        data = f'fields name, cover.url; search "{query}"; limit 10;'
        response = requests.post(url, headers=self.headers, data=data)
        return response.json()

    def get_game_cover(self, game_id: int) -> str:
        url = f'{self.api_url}/covers'
        data = f'fields image_id; where game = {game_id}; limit 1;'
        response = requests.post(url, headers=self.headers, data=data)
        if response.status_code == 200:
            return f"https://images.igdb.com/igdb/image/upload/t_cover_big/{response.json()[0]['image_id']}.png"
