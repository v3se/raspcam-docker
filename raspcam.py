import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server

with open('./html/index.html', 'r') as f:
    PAGE = str(f.read())


class StreamingOutput(object):
    # start_recording will call the write method which handles detecting and buffering new frames
    # After new frame has been buffered, the buffered bytes will be added to frame variable and then all threads will be notified
    def __init__(self):
        self.frame = None
        self.img = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    # Inherits the class server.BaseHTTPRequestHandler
    # Overwrites the method do_GET in that class
    def do_GET(self):  # Redirects requests coming to / to /index.html
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':  # Adds content from PAGE
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            # Guessing that this writes the content to memory or deliver it straight to client?
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':  # index.html refers to this which triggers a new request from client
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            # special content type for HTTP streaming. Replaces the "element" with new one after seeing the boundary string
            self.send_header(
                'Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()  # sets the thread to wait until notified by StreamingOutput
                        frame = output.frame  # frame data
                    # Sets the boundary string for multipart response
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    # Wtf is wfile. Response stream apparently
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


with picamera.PiCamera(resolution='1640x1232', framerate=24) as camera:
    output = StreamingOutput()
    # Assuming that this is ran in a separate thread
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()  # Starts a HTTP server
    finally:
        camera.stop_recording()  # Cleanup
        camera.close()
