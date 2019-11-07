import asyncio
import aiohttp

def init(url, loop=None):
    if not loop:
        loop = asyncio.get_event_loop()
    http = aiohttp.ClientSession(loop=loop)
    atexit.register(loop.run_until_complete, http.close())
    return Server(http, loop)

class Server(object):
    def __init__(self, http, loop):
        self._http = http
        self._loop = loop

    def get_url(self, path):
        return self._url + path

    async def _post(self, path, *args, **kwargs):
        return await self._http.post(self.get_url(path), *args, **kwargs)
    async def _get(self, path, *args, **kwargs):
        return await self._http.get(self.get_url(path), *args, **kwargs)
    async def register(self, name):
        res = await self._post('/register', data={'name': name})
        return res.text
    async def login(self, id):
        await self._post('/login', data={'id': id})
    async def get_stream(self, id):
        id = str(id)
        print(id)
        print(self.get_url('/get_stream/'+id))
        async with await self._get('/get_stream/' + id) as resp:
            print(await resp.text())
            data = json.loads(await resp.text())
            for entry in data:
                yield pyced.Event(
                    json.loads(entry['body']),
                    {'stream': id, 'version': entry['version']},
                    entry['name'])

    async def consume(self, callback):
        async with self._http.ws_connect(self.get_url('/ws')) as ws:
            async for msg in ws:
                print(msg)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    event = pyced.Event(
                        data['body'],
                        data['headers'],
                        data['routing_key'])
                    await callback(event)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break

    def consume_sync(self, callback):
        self._loop.run_until_complete(self.consume(callback))

    async def add_event(self, event):
        headers = {
            'X-ES-Version': str(event.headers['version'])
        }
        path = '/{}/{}'. format(event.headers['stream'], event.name)
        res = await self._post(path, json=event.data, headers=headers)
        return str(res.text)

    async def subscribe(self, pattern):
        await self._post('/subscribe', data={'pattern': pattern+'.#'})
