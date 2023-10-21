from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuration(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    twitch_username: str
    twitch_oauth_token: str
    openai_api_key: str
