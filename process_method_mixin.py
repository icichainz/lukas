
class ProcessMethodMixin:
    """ Provide diferrents methodes implementation."""
    def get(self,key):
        return self._kv 
    
    def set(self,key,value):
        self._kv[key] = value 
        return 1
    
    def delete(self,key):
        if key in self._kv :
            del self._kv[key]
            return 1
        return 0
    
    def flush(self):
        kvlen = len(self._kv)
        self._kv.clear()
        return kvlen
    
    def mget(self,*keys):
        return [self._kv.get(_) for _ in keys]
    
    def mset(self,*items):
        data = zip(items[::2],items[1::2])
        for key, value in data:
            self._kv[key] = value 
        return len(data)
    