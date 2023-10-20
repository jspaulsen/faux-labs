from pydantic_settings import BaseSettings, SettingsConfigDict


REQUIRED_SCOPES = [
    # "channel:read:subscriptions", 
    # "channel:read:redemptions", 
    # "channel:read:predictions", 
    # "channel:read:polls", 
    # "channel:read:hype_train", 
    # "channel:read:schedule",
    "channel:moderate",
    "chat:edit",
    "chat:read",
    # "bits:read",
]


class Configuration(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    twitch_client_id: str
    twitch_client_secret: str
    twitch_username: str
    redirect_uri: str = "http://localhost:6969"
