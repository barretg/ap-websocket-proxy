from worlds.LauncherComponents import Component, components, Type, launch_subprocess


def launch_ws_proxy(*args):
    from .proxy import main
    launch_subprocess(main, name="AP WebSocket Proxy")


components.append(
    Component(
        "AP WebSocket Proxy",
        func=launch_ws_proxy,
        component_type=Type.TOOL,
    )
)
