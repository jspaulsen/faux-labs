from pydantic import BaseModel
import requests


class TokenPayload(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    scope: list[str]


class TwitchClient:
    def __init__(self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self.session = requests.Session()
    
    def exchange_code_for_token(self, code: str) -> TokenPayload:
        response = self.session.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
            },
        )

        response.raise_for_status()
        return TokenPayload(**response.json())

    def refresh_token(self, refresh_token: str) -> TokenPayload:
        response = self.session.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )

        response.raise_for_status()
        return TokenPayload(**response.json())
