import socket
import sys
import traceback
import os
from io import StringIO


def return_py_script(path):
    """
    Exec a python script, determine the type of either html or text and output to client
    """
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    exec(open(path).read())
    sys.stdout = old_stdout
    content = mystdout.getvalue()
    if "<http>" in content:
        mime_type = b"text/html"
    else:
        mime_type = b"text/plain"
    content = content.encode()
    return content, mime_type


def return_directory(path):
    """
    If the requested path is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.
    """
    files = os.listdir(path)
    content = ""
    for file in files:
        content = content + f"{file}\n"
    content = content.encode()
    mime_type = b"text/plain"
    return content, mime_type


def return_file(path):
    """
    If the path is a file, it should return the contents of that file
    and its correct mimetype.


    Ex:
        response_path('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        response_path('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        response_path('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")
    """
    file_ext = path.split(".")[1]
    if file_ext != "py":
        with open(path, "rb") as file:
            content = file.read()
        if file_ext == "txt":
            mime_type = b"text/plain"
        elif file_ext == "html" or file_ext == "htm":
            mime_type = b"text/html"
        elif file_ext == "png":
            mime_type = b"image/png"
        elif file_ext == "jpg":
            mime_type = b"image/jpeg"
    else:
        content, mime_type = return_py_script(path)
    return content, mime_type


def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->

        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """
    response_ok_string = f'HTTP/1.1 200 OK\r\nContent-Type:{mimetype.decode()}\r\n\r\n'
    response_ok_string = response_ok_string.encode() + body
    return response_ok_string


def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""

    return b"HTTP/1.1 405 Method Not Allowed\r\n"


def response_not_found():
    """Returns a 404 Not Found response"""

    return b"HTTP/1.1 404 Not Found\r\n"


def parse_request(request):
    """
    Given the content of an HTTP request, returns the path of that request.

    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.
    """

    method, path, version = request.split("\r\n")[0].split(" ")
    if method != "GET":
        raise NotImplementedError
    return path


def response_path(path):
    """
    This method should return appropriate content and a mime type.

    If the requested path is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the path is a file, it should return the contents of that file
    and its correct mimetype.

    If the path does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        response_path('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        response_path('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        response_path('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        response_path('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """
    path = "webroot" + path
    path = os.path.abspath(path)
    content = b"not implemented"
    mime_type = b"not implemented"
    if os.path.isdir(path):
        return return_directory(path)
    elif os.path.isfile(path):
        return return_file(path)
    else:
        raise NameError
    return content, mime_type


def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)

                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')

                    if '\r\n\r\n' in request:
                        break

                print("Request received:\n{}\n\n".format(request))
                path = parse_request(request)
                content, mime_type = response_path(path)
                response = response_ok(body=content, mimetype=mime_type)
                conn.sendall(response)
            except NotImplementedError:
                response = response_method_not_allowed()
                conn.sendall(response)
            except NameError:
                response = response_not_found()
                conn.sendall(response)
            except:
                traceback.print_exc()
            finally:
                conn.close()

    except KeyboardInterrupt:
        sock.close()
        sys.exit(1)
    except:
        traceback.print_exc()


if __name__ == '__main__':
    server()
    sys.exit(0)
