from gevent.pool import Pool 
from gevent.server import StreamServer


from process_method_mixin import ProcessMethodMixin 

from exception import Disconnected,CommandError
from protocol_handler import Error, ProtocolHandler


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