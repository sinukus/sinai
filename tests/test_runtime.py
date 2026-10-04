import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread, Event
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import pytest

from aicourt.local import OllamaClient
from aicourt.memory import LocalMemory
from aicourt.server import TravelSession, make_server


def test_file_memory_persists_without_database(tmp_path):
    path = tmp_path / 'memory.json'
    LocalMemory(path).put('country', 'JP')
    memory = LocalMemory(path)
    assert memory.get('country') == 'JP'
    assert memory.get('missing', 'fallback') == 'fallback'
    memory.append('recent', 'one', limit=2)
    memory.append('recent', 'two', limit=2)
    assert memory.append('recent', 'three', limit=2) == ['two', 'three']
    snapshot = memory.snapshot()
    snapshot['country'] = 'XX'
    assert memory.get('country') == 'JP'
    assert memory.forget('country') is True
    assert memory.get('country') is None
    assert memory.forget('country') is False
    legacy = tmp_path / 'old.db'
    legacy.write_bytes(b'untouched')
    with pytest.raises(ValueError):
        LocalMemory(legacy)
    assert legacy.read_bytes() == b'untouched'


def test_real_http_transport_streams_before_completion():
    release = Event()
    class ModelServer(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert self.path == '/api/chat' and body['stream'] is True
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"message":{"content":"First"},"done":false}\n')
            self.wfile.flush()
            release.wait(3)
            self.wfile.write(b'{"message":{"content":" second"},"done":true}\n')
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), ModelServer)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        stream = OllamaClient('fixture', f'http://127.0.0.1:{server.server_port}').stream([{'role':'user','content':'hello'}])
        assert next(stream) == 'First'
        release.set()
        assert list(stream) == [' second']
    finally:
        release.set()
        server.shutdown()
        server.server_close()


def test_browser_gateway_destination_answer_and_error(tmp_path):
    class Client:
        def stream(self, messages):
            assert 'TRAVEL TEMPLATE' in messages[-1]['content']
            yield 'Local '
            yield 'answer'
    session = TravelSession(tmp_path, Client())
    server = make_server(session, 0)
    Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}'
    def send(text, origin=None):
        headers={'Content-Type':'application/json'}
        if origin: headers['Origin']=origin
        with urlopen(Request(url+'/chat',data=json.dumps({'text':text}).encode(),headers=headers)) as r:
            return [json.loads(line) for line in r]
    try:
        with urlopen(url) as response:
            assert b'Travel helper' in response.read()
        assert send('I am going to Japan')[0]['type'] == 'destination'
        events = send('How does this lock work?')
        assert ''.join(e.get('text','') for e in events) == 'Local answer'
        assert events[-1]['type'] == 'done'
        assert LocalMemory(tmp_path/'session.json').get('country') == 'JP'
        with pytest.raises(HTTPError) as error:
            send('hello', 'https://unrelated.example')
        assert error.value.code == 403
    finally:
        server.shutdown()
        server.server_close()


def test_model_failure_is_not_saved_as_answer(tmp_path):
    class Failed:
        def stream(self, messages):
            yield 'Partial'
            raise OSError('model unavailable')
    session = TravelSession(tmp_path, Failed())
    list(session.respond('I am going to Vietnam'))
    with pytest.raises(OSError):
        list(session.respond('Question'))
    assert session.memory.get('history') == []
