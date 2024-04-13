# -*- coding: utf-8 -*-

'''
a = Params()
a['asdf'] = '123'
a.k = '333'
print(a.asdf)
print(a['asdf'])
print(a.k)
print(a['k'])
'''
class Params(dict):
    
    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, k, v):
        self[k] = v
