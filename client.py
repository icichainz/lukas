from gevent import socket
from gevent.pool import Pool 
from gevent.server import StreamServer

from collections import namedtuple 
from io import BytesIO
from socket import error as socket_error

from process_method_mixin import ProcessMethodMixin
from server import Error, ProtocolHandler 

from exception import Disconnected,CommandError


class Client(object):

    def __init__(self,host='127.0.0.1' ,port=31337) -> None:
        self._protocol = ProtocolHandler()
        self._socket = socket.socket(
            socket.AF_INET ,
            socket.SOCK_STREAM
        )
        self._socket.connect(
            (host ,port)
        )
        self._fh = self._socket.makefile('rwb')

    def execute(self,*args):
        self._protocol.write_response(self._fh,args)
        resp = self._protocol.handle_request(
            self._fh)
        if isinstance(resp,Error):
            raise CommandError(resp.message)
        
        return resp
    
    def get(self,key):
        return self.execute('GET',key)
    
    def set(self,key,value):
        return self.execute('SET',key,value)
    
    def delete(self,key):
        return self.execute('DELETE',key)
    
    def flush(self):
        return self.execute('FLUSH')
    
    def mget(self,*keys):
        return self.execute('MGET',*keys)
    
    def mset(self,*items):
        return self.execute('MSET',*items)
     