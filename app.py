"""
Fake Home Assistant Server
===========================
A minimal fake Home Assistant server that tricks the Companion app
into thinking it's connected to a real instance.

This is for FUN/EDUCATION — proving we can speak the HA protocol.
The wake word still won't DO anything (no real Assist pipeline),
but the app should connect and show the UI.

Protocol implemented:
- GET /api/ → basic API info
- GET /api/config → server config
- GET /api/discovery_info → discovery info
- GET /api/websocket → WebSocket with auth flow
- Auth: accepts any token (we're fake, we're chill)
"""

import asyncio
import json
import logging
from aiohttp import web, WSMsgType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fake-ha")

FAKE_VERSION = "2026.10.0"
FAKE_TOKEN = "goddess_fake_token_12345"


async def api_root(request):
    """GET /api/ - Basic API info"""
    return web.json_response({
        "message": "API running."
    })


async def api_config(request):
    """GET /api/config - Server configuration"""
    return web.json_response({
        "location_name": "Goddess Home",
        "latitude": 0.0,
        "longitude": 0.0,
        "elevation": 0,
        "unit_system": {"length": "km", "mass": "kg", "temperature": "°C", "volume": "L"},
        "time_zone": "America/New_York",
        "components": ["fake_goddess"],
        "config_dir": "/fake/config",
        "whitelist_external_dirs": [],
        "version": FAKE_VERSION,
        "config_source": "storage",
        "recovery_mode": False,
        "state": "RUNNING",
        "external_url": None,
        "internal_url": None,
        "currency": "USD",
        "country": "US",
        "language": "en",
    })


async def api_discovery_info(request):
    """GET /api/discovery_info - Discovery information"""
    return web.json_response({
        "uuid": "fake-goddess-uuid-1234",
        "version": FAKE_VERSION,
    })


async def api_states(request):
    """GET /api/states - List of entity states (empty for fake)"""
    return web.json_response([
        {
            "entity_id": "light.goddess_lamp",
            "state": "on",
            "attributes": {
                "friendly_name": "Goddess Lamp",
                "supported_features": 0,
            },
            "last_changed": "2026-10-17T15:00:00+00:00",
            "last_updated": "2026-10-17T15:00:00+00:00",
        }
    ])


async def websocket_handler(request):
    """WebSocket /api/websocket - Main HA protocol"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    logger.info("WebSocket client connected")

    # Step 1: Send auth_required
    await ws.send_json({
        "type": "auth_required",
        "ha_version": FAKE_VERSION
    })

    authenticated = False

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                msg_type = data.get("type")

                if msg_type == "auth" and not authenticated:
                    # Step 2: Client sends auth, we accept anything
                    token = data.get("access_token", "")
                    logger.info(f"Auth attempt with token: {token[:10]}...")
                    authenticated = True
                    await ws.send_json({
                        "type": "auth_ok",
                        "ha_version": FAKE_VERSION
                    })
                    logger.info("Client authenticated (fake!)")

                elif authenticated:
                    # Step 3: Handle commands
                    cmd_id = data.get("id")
                    cmd_type = data.get("type")

                    if cmd_type == "get_states":
                        await ws.send_json({
                            "id": cmd_id,
                            "type": "result",
                            "success": True,
                            "result": []
                        })
                    elif cmd_type == "get_config":
                        await ws.send_json({
                            "id": cmd_id,
                            "type": "result",
                            "success": True,
                            "result": {
                                "latitude": 0.0,
                                "longitude": 0.0,
                                "elevation": 0,
                                "unit_system": {"length": "km", "mass": "kg", "temperature": "°C", "volume": "L"},
                                "location_name": "Goddess Home",
                                "time_zone": "America/New_York",
                                "components": ["fake_goddess"],
                                "config_dir": "/fake/config",
                                "whitelist_external_dirs": [],
                                "version": FAKE_VERSION,
                                "config_source": "storage",
                                "recovery_mode": False,
                                "state": "RUNNING",
                                "external_url": None,
                                "internal_url": None,
                            }
                        })
                    elif cmd_type == "subscribe_events":
                        await ws.send_json({
                            "id": cmd_id,
                            "type": "result",
                            "success": True,
                            "result": None
                        })
                    else:
                        # Generic success for unknown commands
                        await ws.send_json({
                            "id": cmd_id,
                            "type": "result",
                            "success": True,
                            "result": None
                        })
                else:
                    # Not authenticated yet
                    await ws.send_json({
                        "type": "auth_invalid",
                        "message": "Not authenticated"
                    })

            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
            except Exception as e:
                logger.error(f"Error handling message: {e}")

        elif msg.type == WSMsgType.ERROR:
            logger.error(f"WebSocket error: {ws.exception()}")

    logger.info("WebSocket client disconnected")
    return ws


async def frontend_index(request):
    """GET / - Serve a minimal fake frontend"""
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Goddess Home Assistant (FAKE)</title></head>
    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
        <h1>🏠 Goddess Home Assistant</h1>
        <p><strong>This is a FAKE server</strong> built by your Goddess! 🎀</p>
        <p>The Companion app thinks this is real. Isn't that cool?</p>
        <p><em>Wake words won't do anything — there's no real Assist pipeline here.</em></p>
        <p>But the protocol handshake works, and that's the fun part! ✨</p>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")


def create_app():
    app = web.Application()

    # REST API
    app.router.add_get("/api/", api_root)
    app.router.add_get("/api/config", api_config)
    app.router.add_get("/api/discovery_info", api_discovery_info)
    app.router.add_get("/api/states", api_states)

    # WebSocket API
    app.router.add_get("/api/websocket", websocket_handler)

    # Fake frontend
    app.router.add_get("/", frontend_index)

    return app


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8123))
    app = create_app()
    print("=" * 50)
    print("  FAKE HOME ASSISTANT SERVER")
    print("=" * 50)
    print(f"  Version: {FAKE_VERSION}")
    print(f"  Listening on port {port}")
    print(f"  Accepts ANY auth token (we're fake!)")
    print("=" * 50)
    web.run_app(app, host="0.0.0.0", port=port)
