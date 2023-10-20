import webbrowser
from app.config import REQUIRED_SCOPES
from app.oauth_server import OAuthCodeServer


class OAuthCodeService:
    def __init__(
        self,
        client_id: str,
        redirect_uri: str,
        scopes: list[str] | None = None
    ) -> None:
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scopes = scopes or REQUIRED_SCOPES

    def craft_prompt_url(self, scopes: list[str]) -> str:
        return f"https://id.twitch.tv/oauth2/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&scope={'+'.join(scopes)}"
    
    def prompt_generate_code(self) -> str:
        """
        Generates a user token by prompting the user to authorize the application.
        """
        code_server = OAuthCodeServer()
        
        # Start listening on the code server
        thread = code_server.listen()

        # Craft the oauth URL and open it in the user's browser
        oauth_url = self.craft_prompt_url(self.scopes)
        webbrowser.open(oauth_url)

        # Wait for the code server to receive the code
        thread.join()

        # If the code server received an error, raise an exception
        if code_server.error:
            raise Exception(code_server.error_description)
        
        # Exchange the code and return a token
        return code_server.code
