#!/usr/bin/env python3
# coding: utf-8
# Copyright 2020 Abram Hindle, Gengyuan Huang, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse


LOG_REQUEST = False

def helper_parseURL(url):
    # this helper function will parse given url
    # assume correct url
    # return a tuple: (scheme, host, port, body)
    # body is the url without host scheme and port, all other infomation is in body
    # written for CMPUT404 assignment2, thus, only support http

    # get scheme
    url_string = url
    url_splited = url_string.split('://')
    scheme = url_splited.pop(0) if len(url_splited) != 1 else None
    url_string = "://".join(url_splited)

    # get host and port
    url_splited = url_string.split('/')
    host = url_splited.pop(0)
    host_splited = host.split(":")
    host, port = host_splited if len(host_splited ) == 2 else (host, None)
    port = port if port == None else int(port)          # convert port to int if not none
    url_string = '/'.join(url_splited)

    # get body
    body = "/" + url_string

    return scheme, host, port, body

def helper_genHeader(rtype, body, host, extra=None):
    # this function generate a header string for reqests
    # extra is a list of strings, will be appended at the end of the header
    # type = "GET" or "POST"
    header = [
        "{} {} HTTP/1.1".format(rtype, body),
        "Host: {}".format(host),
        "Accept-Charset: UTF-8",
        "Accept: */*",
        "Connection: close"
    ]

    header = header + extra if extra != None else header

    return "\r\n".join(header) + "\r\n\r\n"

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body
    
    def __repr__(self):
        # this method is used for pretty printing
        # it shows code and body to user, when call print()
        string = [
            "Status Code:\n>>>{}".format(self.code),
            "Response Body:\n>>>{}".format(self.body)
        ]
            

        return "\n".join(string)

class HTTPClient(object):
    #def get_host_port(self,url):

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None


    def get_code(self, data):
        # assume correct format
        # return status code of the response in data
        # data is a string
        status_line = data.split("\r\n")[0]
        status_code = status_line.split(" ")[1]

        return int(status_code)

    def get_headers(self,data):
        # get header part of the response
        header = data.split("\r\n\r\n")[0]
        return header

    def get_body(self, data):
        body = data.split("\r\n\r\n")[1]
        return body

    def sendall(self, data):
        if LOG_REQUEST:
            print("Send Request:\n" + data)
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        # assume correct format for url and args

        # create socket and connect
        _, host, port, body = helper_parseURL(url)      # ignore scheme for simplicity of this assignment, use http
        port_connect = 80 if port == None else port     # default assign port to 80

        # connect
        self.connect(host, port_connect)

        # request string
        if args != None:
            # weird case, where you want to send data by a GET request. 
            # Since this function has a arg parameter, I have this code seg here just in case
            content_body = urllib.parse.urlencode(args)
            content_body_length = len(content_body)
            content_headers = [
                "Content-type: application/x-www-form-urlencoded",
                "Content-Length: {}".format(content_body_length)
            ]
            header = helper_genHeader("GET", body, host if port == None else host+':'+str(port), extra=content_headers)
            self.sendall(header + content_body)
        else:
            header = helper_genHeader("GET", body, host if port == None else host+':'+str(port))
            self.sendall(header)

        # get response
        response = self.recvall(self.socket)
        self.close()

        # create and return response object
        return HTTPResponse(self.get_code(response), self.get_body(response))

    def POST(self, url, args=None):
        # assume correct format for url and args

        # create socket and connect
        _, host, port, body = helper_parseURL(url)      # ignore scheme for simplicity of this assignment, use http
        port_connect = 80 if port == None else port     # default assign port to 80

        # connect
        self.connect(host, port_connect)

        # request string
        if args != None: 
            # Send POST data
            content_body = urllib.parse.urlencode(args)
            content_body_length = len(content_body)
            content_headers = [
                "Content-type: application/x-www-form-urlencoded",
                "Content-Length: {}".format(content_body_length)
            ]
            header = helper_genHeader("POST", body, host if port == None else host+':'+str(port), extra=content_headers)
            self.sendall(header + content_body)
        else:
            # no data
            # Send POST data as empty
            content_body = ''
            content_body_length = 0
            content_headers = [
                "Content-type: application/x-www-form-urlencoded",
                "Content-Length: {}".format(content_body_length)
            ]
            header = helper_genHeader("POST", body, host if port == None else host+':'+str(port), extra=content_headers)
            self.sendall(header + content_body)

        # get response
        response = self.recvall(self.socket)
        self.close()

        # create and return response object
        return HTTPResponse(self.get_code(response), self.get_body(response))

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))