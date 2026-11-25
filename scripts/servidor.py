import hashlib, json, os, resource, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ARQ_IO = "/tmp/teste_io.bin"
BLOCO = os.urandom(64 * 1024)
LOCK = threading.Lock()
REQS = 0

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global REQS
        if self.path == "/stats":
            ru = resource.getrusage(resource.RUSAGE_SELF)
            body = json.dumps({
                "reqs": REQS, "nvcsw": ru.ru_nvcsw, "nivcsw": ru.ru_nivcsw,
                "cpu_user_s": round(ru.ru_utime, 3), "cpu_sys_s": round(ru.ru_stime, 3)
            }).encode()
        elif self.path == "/cpu":
            h = b"carga-so-2026"
            for _ in range(15000): h = hashlib.sha256(h).digest()
            with LOCK: REQS += 1
            body = h.hex().encode()
        elif self.path == "/io":
            with open(ARQ_IO, "wb") as f:
                f.write(BLOCO); f.flush(); os.fsync(f.fileno())
            with open(ARQ_IO, "rb") as f: _ = f.read()
            with LOCK: REQS += 1
            body = b"io-ok"
        else:
            with LOCK: REQS += 1
            body = b"ok"
        self.send_response(200); self.end_headers(); self.wfile.write(body)
    def log_message(self, *args): pass

porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
print(f"PID={os.getpid()} PORTA={porta}")
ThreadingHTTPServer(("0.0.0.0", porta), Handler).serve_forever()
