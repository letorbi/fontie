#!/usr/bin/env python3
#
# Fontie font generator copyright 2013-16 Torben Haase <https://fontie.flowyapps.com>
#

import sys
import io
import os
import tempfile
import errno
import socket
import socketserver
import http.server
import cgi

from Daemon import Daemon
from FontieException import FontieException
from FontieFont import FontieFont
from FontiePackage import FontiePackage

class FontieHttpServer(socketserver.ForkingMixIn, http.server.HTTPServer):
    pass

class FontieRequestHandler(http.server.BaseHTTPRequestHandler):
    def _fields_to_options(self, fields):
        result = []
        if isinstance(fields, list):
            for f in fields:
                if isinstance(f.file, io.BufferedRandom):
                    result.append(f.file)
                else:
                    result.append(f.value)
        else:
            if isinstance(fields.file, io.BufferedRandom):
                result.append(fields.file)
            else:
                result.append(fields.value)
        return result

    def do_POST(self):
        path = self.path[:self.path.rfind("/")]
        if path == "/font":
            self.post_font()
        elif path == "/package":
            self.post_package()
        else:
            self.send_response(404)

    def do_GET(self):
        path = self.path[:self.path.rfind("/")]
        if path == "/package":
            self.get_package()
        else:
            self.send_response(404)

    def do_DELETE(self):
        path = self.path[:self.path.rfind("/")]
        if path == "/font":
            self.delete_font()
        else:
            self.send_response(404)

    def post_font(self):
        try:
            fields = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':"POST"})
            if not 'file' in fields:
                raise FontieException(400, 'missing file')
            font = FontieFont(file=fields['file'].file)
            result = "{\"id\":\"%s\",\"name\":\"%s\"}" % (font.id, font.font.fullname)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))
        except FontieException as e:
            if e.original_exception:
                print("Exception: %s" % e.original_exception)
            print("Message: %s" % e.message)
            result = "{\"message\":\"%s\"}" % e.message
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))
            if 'font' in locals() and font:
                font.destroy(False)
        except:
            if 'font' in locals() and font:
                font.destroy(False)
            raise

    def post_package(self):
        try:
            fields = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':"POST"})
            if not 'font' in fields:
                raise FontieException(400, 'missing fonts')
            package = FontiePackage()
            for font in self._fields_to_options(fields['font']):

                print(font)
                package.add(font)
            if 'fixes' in fields:
                package.fix(self._fields_to_options(fields['fixes']))
            if fields['hinting'].value:
                package.hint(fields['hinting'].value)
            if 'ranges' in fields:
                package.subset(self._fields_to_options(fields['ranges']))
            if 'output' in fields:
                package.convert(self._fields_to_options(fields['output']))
            if 'css' in fields:
                package.css(self._fields_to_options(fields['css']))
            if 'html' in fields:
                package.html(self._fields_to_options(fields['html']))
            package.close()
            result = "{\"package\":\"%s\"}" % package.id
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))
        except FontieException as e:
            if e.original_exception:
                print("Exception: %s" % e.original_exception)
            print("Message: %s" % e.message)
            result = "{\"message\":\"%s\"}" % e.message
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))
            if 'package' in locals() and package:
                package.destroy(False)
        except:
            if 'package' in locals() and package:
                package.destroy(False)
            raise

    def get_package(self):
        try:
            # REF https://hg.python.org/cpython/file/3.5/Lib/cgi.py
            fields = cgi.FieldStorage(environ={'REQUEST_METHOD':"GET", 'QUERY_STRING':self.path[self.path.find("?")+1:]})
            if not 'id' in fields:
                raise FontieException(400, 'missing package id')
            package = FontiePackage(fields['id'].value)
            data = package.zip()
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.end_headers()
            self.wfile.write(data.getvalue())
            data.close()
            package.destroy()
        except FontieException as e:
            if e.original_exception:
                print("Exception: %s" % e.original_exception)
            print("Message: %s" % e.message)
            result = "{\"message\":\"%s\"}" % e.message
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))
            if 'package' in locals() and package:
                package.destroy(False)
        except:
            if 'package' in locals() and package:
                package.destroy(False)
            raise

    def delete_font(self):
        try:
            # REF https://hg.python.org/cpython/file/3.5/Lib/cgi.py
            fields = cgi.FieldStorage(environ={'REQUEST_METHOD':"GET", 'QUERY_STRING':self.path[self.path.find("?")+1:]})
            if not 'id' in fields:
                raise FontieException(400, 'missing font id')
            font = FontieFont(id=fields['id'].value)
            result = "{\"id\":\"%s\"}" % font.id
            font.destroy()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))
        except FontieException as e:
            if e.original_exception:
                print("Exception: %s" % e.original_exception)
            print("Message: %s" % e.message)
            result = "{\"message\":\"%s\"}" % e.message
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result.encode("utf-8"))
            if 'font' in locals() and font:
                font.destroy(False)
        except:
            if 'font' in locals() and font:
                font.destroy(False)
            raise

class FontieDaemon(Daemon):
    def run(self):
        run()

def run():
    print("Fontie is starting...")
    httpd = FontieHttpServer(("localhost", 8000), FontieRequestHandler)
    result = httpd.serve_forever()
    print("Fontie is shutting down (%d)..." % result)
    exit(result)

if len(sys.argv) < 2:
    run()
else:
    daemon = FontieDaemon("/var/run/fontie.pid")
    if sys.argv[1] == "start":
        daemon.start()
    elif sys.argv[1] == "stop":
        daemon.stop()
    elif sys.argv[1] == "restart":
        daemon.restart()
    else:
        print("expecting: fontie (start|stop|restart)")
