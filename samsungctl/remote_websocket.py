import base64
import json
import logging
import socket
import time

from . import exceptions


URL_FORMAT = "ws://{}:{}/api/v2/channels/samsung.remote.control?name={}"


class RemoteWebsocket():
    """Object for remote control connection."""

    def __init__(self, config):
        import websocket

        if not config["port"]:
            config["port"] = 8001

        if config["timeout"] == 0:
            config["timeout"] = None

        url = URL_FORMAT.format(config["host"], config["port"],
                                self._serialize_string(config["name"]))

        self.connection = websocket.create_connection(url, config["timeout"])

        self._read_response()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        """Close the connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logging.debug("Connection closed.")

    def control(self, key):
        """Send a control command."""
        if not self.connection:
            raise exceptions.ConnectionClosed()

        payload = json.dumps({
            "method": "ms.remote.control",
            "params": {
                "Cmd": "Click",
                "DataOfCmd": key,
                "Option": "false",
                "TypeOfRemote": "SendRemoteKey"
            }
        })

        logging.info("Sending control command: %s", key)
        self.connection.send(payload)
        time.sleep(self._key_interval)

    _key_interval = 0.5

    def launch(self, appId, method="DEEP_LINK"):
        """Launch an app command."""
        if not self.connection:
            raise exceptions.ConnectionClosed()

        payload = json.dumps({
            "method": "ms.channel.emit",
            "params": {
                "event": "ed.apps.launch",
                "to": "host",
                "data": {
                    "appId": "11101200001",
                    "action_type": method
                }
            }
        })

        logging.info("Sending launch command: %s", appId)
        self.connection.send(payload)
        time.sleep(self._key_interval)

    _key_interval = 0.5

    def get_installed_apps(self):
        """Get all installed apps command."""
        if not self.connection:
            raise exceptions.ConnectionClosed()

        payload = json.dumps({
            "method": "ms.channel.emit",
            "params": {
                "event": "ed.installedApp.get",
                "to": "host"
            }
        })

        logging.info("Sending get_installed_apps command")
        self.connection.send(payload)
        time.sleep(self._key_interval)

    _key_interval = 0.5

    def _read_response(self):
        response = self.connection.recv()
        response = json.loads(response)

        if response["event"] != "ms.channel.connect":
            self.close()
            raise exceptions.UnhandledResponse(response)

        logging.debug("Access granted.")

    @staticmethod
    def _serialize_string(string):
        if isinstance(string, str):
            string = str.encode(string)

        return base64.b64encode(string).decode("utf-8")
