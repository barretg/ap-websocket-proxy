import asyncio
import websockets
import json

async def proxy(local_ws):
    async with websockets.connect("ws://ap2.aijanio.xyz:8080") as remote_ws:
        async def forward(src, dst):
            try:
                async for msg in src:
                    try:
                        parsed = json.loads(msg)
                        for packet in parsed:
                            if packet.get("cmd") == "PrintJSON":
                                text = "".join(part.get("text", "") for part in packet.get("data", []))
                                print(f"[Chat] {text}")
                    except json.JSONDecodeError:
                        pass
                    await dst.send(msg)
            except websockets.exceptions.ConnectionClosed:
                pass
        
        await asyncio.gather(
            forward(local_ws, remote_ws),
            forward(remote_ws, local_ws)
        )

async def main():
    async with websockets.serve(proxy, "localhost", 9999):
        print("Proxy running on ws://localhost:9999")
        await asyncio.Future()

asyncio.run(main())