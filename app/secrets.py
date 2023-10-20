import keyring
import pydantic


class RefreshToken(pydantic.BaseModel):
    refresh_token: str
    expires_in: int
    scope: list[str]
    token_type: str


class SecretException(Exception):
    pass


class RefreshTokenException(SecretException):
    pass


class Secrets:
    SERVICE_NAME: str = "Twitch"
    REFRESH_TOKEN_KEY: str = "refresh_token"

    def get(self, key: str) -> str | None:
        return keyring.get_password(self.SERVICE_NAME, key)

    def set(self, key: str, value: str) -> None:
        keyring.set_password(self.SERVICE_NAME, key, value)
    
    def delete(self, key: str) -> None:
        keyring.delete_password(self.SERVICE_NAME, key)

    def get_refresh_token(self) -> str | None:
        return self.get(self.REFRESH_TOKEN_KEY)
    
    def save_refresh_token(self, value: str) -> None:
        self.set("refresh_token", value)

    def delete_refresh_token(self) -> None:
        self.delete(self.REFRESH_TOKEN_KEY)
    
