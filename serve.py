import os, http.server, socketserver

class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()

        range_header = self.headers.get('Range')
        if not range_header:
            return super().send_head()

        try:
            file_size = os.path.getsize(path)
            range_spec = range_header.replace('bytes=', '')
            parts = range_spec.split('-')
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            ctype = self.guess_type(path)
            f = open(path, 'rb')
            f.seek(start)

            self.send_response(206)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.send_header('Content-Length', str(length))
            self.send_header('Accept-Ranges', 'bytes')
            self.end_headers()
            return f
        except Exception:
            return super().send_head()

    def do_GET(self):
        f = self.send_head()
        if f:
            try:
                range_header = self.headers.get('Range')
                if range_header:
                    file_size = os.fstat(f.fileno()).st_size
                    parts = range_header.replace('bytes=', '').split('-')
                    start = int(parts[0]) if parts[0] else 0
                    end = int(parts[1]) if parts[1] else file_size - 1
                    end = min(end, file_size - 1)
                    length = end - start + 1
                    self.wfile.write(f.read(length))
                else:
                    self.copyfile(f, self.wfile)
            finally:
                f.close()

port = int(os.environ.get('PORT', '8801'))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with socketserver.TCPServer(('', port), RangeHTTPRequestHandler) as httpd:
    print(f'Serving on port {port} with Range support')
    httpd.serve_forever()
