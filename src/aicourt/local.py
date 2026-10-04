"""Real local-model transport using Ollama's streaming chat API."""
import json
from urllib.request import Request, urlopen
from urllib.parse import urlparse


class OllamaClient:
    def __init__(self, model, endpoint='http://127.0.0.1:11434', timeout=120):
        parsed = urlparse(endpoint)
        if parsed.scheme != 'http' or parsed.hostname not in {'localhost', '127.0.0.1', '::1'}:
            raise ValueError('Local backend must use a loopback HTTP endpoint')
        if not model.strip():
            raise ValueError('Configure an installed Ollama model')
        self.model, self.endpoint, self.timeout = model, endpoint.rstrip('/'), timeout

    def stream(self, messages):
        body = json.dumps({'model': self.model, 'messages': messages, 'stream': True}).encode()
        request = Request(self.endpoint + '/api/chat', data=body,
                          headers={'Content-Type': 'application/json'}, method='POST')
        with urlopen(request, timeout=self.timeout) as response:
            for line in response:
                event = json.loads(line)
                if event.get('error'):
                    raise RuntimeError(event['error'])
                content = event.get('message', {}).get('content', '')
                if content:
                    yield content
                if event.get('done'):
                    return
        raise RuntimeError('Model stream ended without a completion event')
