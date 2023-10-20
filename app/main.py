import asyncio

from app.config import Configuration
from app.clients.twitch import TwitchClient
from app.logging import setup_logging
from app.secrets import Secrets, RefreshTokenException
from app.services.oauth import OAuthCodeService
from app.twitch_irc import TwitchIRC


def main() -> None:
    logger = setup_logging(__name__)
    secrets = Secrets()
    configuration = Configuration()

    twitch_client = TwitchClient(
        configuration.twitch_client_id,
        configuration.twitch_client_secret,
        configuration.redirect_uri,
    )

    while True:
        try:
            refresh_token = secrets.get_refresh_token()

            if not refresh_token:
                token_service = OAuthCodeService(
                    configuration.twitch_client_id,
                    configuration.redirect_uri,
                )

                logger.info("Prompting user to authorize application - this should open your browser.")
                code = token_service.prompt_generate_code()
                token = twitch_client.exchange_code_for_token(code)

                secrets.save_refresh_token(token.refresh_token)

            token_payload = twitch_client.refresh_token(refresh_token)

            asyncio.run(
                TwitchIRC(
                    configuration.twitch_username,
                    token_payload.access_token,
                ).connect()
            )
        except RefreshTokenException:
            logger.error("User refresh token has expired or is invalid.")
            secrets.delete_refresh_token()
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
