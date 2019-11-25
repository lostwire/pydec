import logging
import functools

import aiohttp.web

logger = logging.getLogger(__name__)

def init(**args):
    return Server(aiohttp.web.Application(), args)

async def json_output(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return aiohttp.web.json_response(f(*args, **kwargs))
    return wrapper

class Server(object):
    def __init__(self, app, args):
        self._app = app
        self._args = args

    def register(self, path, handler):
        self._app.router.add_get(path, functools.partial(json_output, handler))
        logger.info("Registering handler for %s", path)

    def run(self):
        logger.info("Starting server")
        aiohttp.web.run_app(self._app, **self._args)
