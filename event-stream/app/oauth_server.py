import logging
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from urllib.parse import urlparse, parse_qs


logger = logging.getLogger(__name__)


class OAuthCodeServerHandler(BaseHTTPRequestHandler):
    """
    Handler for the OAuth code server.
    """
    def do_GET(self) -> None:
        url = urlparse(self.path)

        # If the path is not /, return a 404
        if url.path != "/":
            self.send_response(404)
            self.end_headers()
            return
        
        query = parse_qs(
            urlparse(
                self.path
            ).query
        )

        # Get the code and error from the query parameters
        code = query.get("code")
        error = query.get("error")
        error_description = query.get("error_description")

        body = {
            "error": error,
            "error_description": error_description,
        } if error else {
            "status": "success",
        }

        self.send_response(200)
        self.send_header("Content-type", "application/json")

        # Send a response to the client
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))

        # Set the code and error on the server
        self.server.code = code
        self.server.error = error
        self.server.error_description = error_description
        

class OAuthCodeServer(HTTPServer):
    """
    Server which stands up temporarily to receive the OAuth code from Twitch.
    """
    def __init__(self) -> None:
        self.code = None
        self.error = False
        self.error_description = None

        super().__init__(("localhost", 6969), OAuthCodeServerHandler)
    
    def _threaded_listen(self) -> None:
        self.handle_request()
        
        # close any open sockets
        self.server_close()

    def listen(self) -> threading.Thread:
        """
        Listen on port 6969 for the OAuth code.
        """
        thread = threading.Thread(target=self.handle_request)
        thread.start()

        return thread
