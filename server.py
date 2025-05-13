# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "starlette",
#     "uvicorn",
# ]
# ///
import os
import sys

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

import uvicorn


class CrossOriginEmbedderPolicy:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def set_coep(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append('Cross-Origin-Embedder-Policy', "credentialless")
            await send(message)

        await self.app(scope, receive, set_coep)


class CrossOriginOpenerPolicy:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def set_coop(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append('Cross-Origin-Opener-Policy', "same-origin")
            await send(message)

        await self.app(scope, receive, set_coop)


middleware = [
    Middleware(CORSMiddleware, allow_origins=['*']),
    Middleware(CrossOriginEmbedderPolicy),
    Middleware(CrossOriginOpenerPolicy),
]

routes = [
    Mount('/', app=StaticFiles(html=True, directory='.'), name="static"),
]

app = Starlette(routes=routes, middleware=middleware)


def main() -> None:
    if len(sys.argv) == 1:
        print("usage: server.py directory [port]")
        return
    os.chdir(sys.argv[1])
    port = int(sys.argv[2]) if len(sys.argv) == 3 else 5005
    uvicorn.run("server:app", host='127.0.0.1', port=port, log_level="info")


if __name__ == "__main__":
    main()