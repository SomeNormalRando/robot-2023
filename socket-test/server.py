from socketserver import TCPServer, BaseRequestHandler

class RequestHandler(BaseRequestHandler):
    def handle():
        # processes incoming requests
        pass

TCPServer(address, RequestHandler, True)
