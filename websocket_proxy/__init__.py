import settings
from worlds.AutoWorld import World
from . import components as _components  # noqa: F401


class WSProxySettings(settings.Group):
    class TargetServer(str):
        """The server to forward WebSocket connections to"""
    class TargetPort(int):
        """The port on the target server"""
    class LocalPort(int):
        """The local port the proxy listens on"""
    class OpenURL(str):
        """URL to open in the browser when the proxy starts (leave empty to disable)"""

    target_server: TargetServer = TargetServer("archipelago.gg")
    target_port: TargetPort = TargetPort(38281)
    local_port: LocalPort = LocalPort(9999)
    open_url: OpenURL = OpenURL("")


class APWebSocketProxyWorld(World):
    """
    Utility tool that runs a local WebSocket proxy, allowing browser-based
    Archipelago clients to connect to servers that only serve plain ws://.
    """
    game = "AP WebSocket Proxy"
    topology_present = False
    item_name_to_id = {}
    location_name_to_id = {}

    settings: WSProxySettings
    settings_key = "ap_websocket_proxy"

    def generate_basic(self):
        pass
