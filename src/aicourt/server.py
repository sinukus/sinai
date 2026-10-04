"""Loopback travel UI and pushed NDJSON responses. No polling or mock fallback."""
import argparse
import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import RLock
from importlib.resources import files

from .local import OllamaClient, LocalFirstRouter
from .memory import LocalMemory
from .travel import TravelHelper


class TravelSession:
    def __init__(self, root, client):
        self.helper = TravelHelper(Path(root) / 'destinations')
        self.memory = LocalMemory(Path(root) / 'session.json')
        self.client = client if isinstance(client, LocalFirstRouter) else LocalFirstRouter(local=client)
        self.lock = RLock()

    def respond(self, text):
        with self.lock:
            try:
                pack = self.helper.resolve(text)
            except ValueError:
                pack = None
            if pack is not None:
                state = asyncio.run(self.helper.prepare(text))
                self.memory.put('country', pack['code'])
                self.memory.put('history', [])
                yield {'type': 'destination', 'state': state}
                yield {'type': 'done'}
                return
            country = self.memory.get('country')
            if not country:
                raise ValueError('Start with “I am going to Japan” or another installed country')
            prompt = self.helper.build_prompt(country, text)
            history = self.memory.get('history') or []
            messages = [*history[-12:], {'role': 'user', 'content': prompt}]
            answer = ''
            for delta in self.client.stream(messages, require_local=True):
                answer += delta
                yield {'type': 'delta', 'text': delta}
            self.memory.put('history', [*history[-10:], {'role': 'user', 'content': text},
                                       {'role': 'assistant', 'content': answer}])
            yield {'type': 'done'}


def make_server(session, port=8765):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/':
                self.send_error(404)
                return
            body = files('aicourt').joinpath('web.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != '/chat':
                self.send_error(404)
                return
            # Reject cross-site requests to this local service.
            host = self.headers.get('Host', '')
            origin = self.headers.get('Origin')
            if host not in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'} or (origin and origin != 'http://' + host):
                self.send_error(403)
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 65536:
                    raise ValueError('Invalid request size')
                data = json.loads(self.rfile.read(size))
                text = data['text']
                if not isinstance(text, str) or not text.strip():
                    raise ValueError('Text is required')
            except (ValueError, KeyError, TypeError):
                self.send_error(400)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-ndjson; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            try:
                for event in session.respond(text):
                    self.wfile.write((json.dumps(event, ensure_ascii=False) + '\n').encode())
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception as exc:
                event = {'type': 'error', 'text': str(exc)}
                try:
                    self.wfile.write((json.dumps(event) + '\n').encode())
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass

        def log_message(self, *args):
            pass
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, help='Name of an already installed Ollama model')
    parser.add_argument('--data', default='./local-travel')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = make_server(TravelSession(args.data, OllamaClient(args.model)), args.port)
    print(f'Travel helper: http://127.0.0.1:{server.server_port} (local model: {args.model})')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
