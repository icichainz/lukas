from gevent import socket
from gevent.pool import Pool 
from gevent.server import StreamServer

from collections import namedtuple 
from io import BytesIO
from socket import error as socket_error

from process_method_mixin import ProcessMethodMixin 

from exception import Disconnected,CommandError

Error = namedtuple('Error',('message'))

class ProtocolHandler(object):

    def __init__(self) -> None:

        self.handlers = {
            '+': self.handle_simple_string,
            '-':self.handle_error,
            ':': self.handle_integer,
            '$':self.handle_string,
            '*':self.handle_array,
            '%':self.handle_dict
        }

    def handle_request(self,socket_file)->dict:
        first_byte = socket_file.read(1)
        if not first_byte:
            raise Disconnected()
        try:
            return self.handlers[first_byte](socket_file)
        except KeyError:
            raise CommandError('bad request')
        
    def handle_simple_string(self,socket_file)->any:
            return socket_file.readline().rstrip('\r\n')
        
    def handle_error(self,socket_file)->type[Error]:
            return Error(socket_file.readline().strip('\r\n'))
        
    def handle_integer(self,socket_file)->int:
        return int(socket_file.readline().strip('\r\n'))
    
    def handle_string(self,socket_file)->any:
         length = int(socket_file.readline().strip('\r\n'))
         if length == -1:
              return None
         length += 2
         return socket_file.read(length)[:-2]
    
    def handle_array(self,socket_file):
         num_elements = int(socket_file.readline().strip('\r\n'))
         return [self.handle_request(socket_file=socket_file) for _ in range(num_elements)]
    
    def handle_dict(self,socket_file):
         num_items = int(socket_file.readline().rstrip('\r\n'))
         elements = [self.handle_request(socket_file=socket_file) for _ in  range(num_items * 2 )]
         return dict(zip(elements[::2] ,elements[1::2]))
    
    def write_response(self, socket_file,data):
        buff = BytesIO()
        self._write(buff,data)
        buff.seek(0)
        socket_file.write(buff.getvalue())
        socket_file.flush()

    def _write(self,buff,data):
         
        if isinstance(data,str):
              data = data.encode('utf-8')
        
        if isinstance(data,bytes):
             buff.write('$%s\r\n%s\r\n' % (len(data),data))

        elif isinstance(data,int):
             buff.write(':%s\r\n' % data )

        elif isinstance(data,Error):
             buff.write('*%s\r\n' % Error.message)
        
        elif isinstance(data,(list,tuple)):
             buff.write('*%s\r\n' % len(data))
             for item in data:
                  self._write(buff=buff,data=item)
        
        elif isinstance(data,dict):
             buff.write('%%%s\r\n' % len(data))
             for key in data:
                  self._write(buff=buff,data=key)
                  self._write(buff=buff,data=data[key])
        
        elif data is None :
             buff.write('$-1\r\n')
        else:
             raise CommandError('unrecognized type: %s' % type(data))

class Server(ProcessMethodMixin):
    def __init__(self,
                 
                host= '127.0.0.1',
                port=31337,
                max_clients = 64
                  ) -> None:
        self._pool = Pool(max_clients)
        self.server=  StreamServer(
            (host,port),
            self.connection_handler,spawn=self._pool
        )
        self._protocol = ProtocolHandler()
        self._kv = {}
        self._commands = self.get_commands()

    def get_commands(self):
         return {
              'GET': self.get,
              'SET': self.set,
              'DELETE': self.delete,
              'FLUSH': self.flush,
              'MGET': self.mget,
              'MSET':self.mset
         }
    

    def connection_handler(self, conn,address):
            """ Convert 'conn'  a socket object to a file-object. """
            socket_file = conn.makefile('rwb')
            while True:

                try:
                    data = self._protocol.handle_request(socket_file)
                except Disconnected:
                    break
                try:
                    resp = self.get_response(data)
                except CommandError as exc:
                    resp = Error(exc.args[0])

                self.protocol.write_response(socket_file,resp)

    def get_response(self,data):
            if not isinstance(data,list):
                try:
                      data = data.split()
                except:
                     raise CommandError('Request must be list or simple string')
            if not data:
                 raise CommandError('Missing command')
            
            command = data[0].upper()

            if command not in self._commands:
                 raise CommandError('Unrecognized command: %s' % command)
            
            return self._commands[command](*data[:1])
                

    def run(self):
            print(f" The server started successfully. Listening on port {self.server.address}")
            self.server.serve_forever()


if __name__ == '__main__':
     from gevent import monkey; monkey.patch_all()
     server = Server()
     server.run()