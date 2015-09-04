#!/usr/bin/python

"""
Several decorators to help using the API of GitHub. 

See README.md for usage.
"""
from __future__ import print_function


import pickle, redis
import functools, sys



def prepend_url(prepended_url):
    """
    A simple decorator that prepend something to the first parameter
    of the decorated function. 
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped_f(url, *args, **kwargs):
            return f(prepended_url+url, *args, **kwargs)
        return wrapped_f
    return decorator


class InMemoryCacheDecorator(object):
    """
    A naive in-memory cache decorator to handle requests.get, requests.post, etc.
    It expects that every call to the decorated function has a 'url' argument, 
    that will be used as a key for the cache.

    Cache every request, including those resulting in something else than a 
    status_code 200.   
    """

    def __init__(self, cache=None):
        """ 
        Initialize a decorator for an in-memory cache. You may
        provide a cache argument which is a pre-populated dictionary.
        """
        self.cache = cache or {}

    def __call__(self, f):
        @functools.wraps(f)
        def wrapped_f(url, *args, **kwargs):
            try:
                r = self.cache[url]
                print('from cache: '+url, file=sys.stderr)
                return r
            except KeyError as e: 
                r = f(url, *args, **kwargs)
                self.cache[url] = r
                return r
        return wrapped_f


class RedisBackendCacheDecorator(object):
    """
    A cache decorator that uses a Redis backend to persist the cached requests.
    Expect that every call to the decorated function has a 'url' argument, 
    which will be used as a key for the cache. 

    This cache decorator also relies on ETag value (see GitHub API 
    documentation) to refresh the data if it changed since the last call.

    Use pickle to serialize the results under the hood.

    Do not cache request that ends with status_code != 200.
    """

    def __init__(self, **kwargs):
        """
        Initialize a Redis Backend Cache Decorator. You may provide keyword
        arguments that will be passed to the Redis connection construction
        (see redis module documentation), like 'host', 'db', 'password', ...
        """
        self.store = redis.StrictRedis(**kwargs)
        # Ensure that connection will be tested before actually 
        # decorating the function
        self.store.get('x')

    def __call__(self, f):
        @functools.wraps(f)
        def wrapped_f(url, *args, **kwargs):
            update_cache = False
            # Is this URL in cache? Get stored ETag
            cached_etag = self.store.get(url+'.etag')
            if cached_etag: 
                # Make a request to see if it has changed
                headers = kwargs.get('headers', {})
                headers['If-None-Match'] = cached_etag
                kwargs['headers'] = headers
                r = f(url, *args, **kwargs)
                # If it has changed, perform the request
                if r.headers['status'] != '304 Not Modified':
                    print('update cache: '+url, file=sys.stderr)
                    update_cache = True
                else:
                    # Return cached value
                    print('from cache: '+url, file=sys.stderr)
                    return pickle.loads(self.store.get(url+'.response'))
            else:
                # Make the request
                r = f(url, *args, **kwargs)
                update_cache = True
            if update_cache: 
                self.store.set(url+'.etag', r.headers['ETag'])
                self.store.set(url+'.response', pickle.dumps(r))
            return r
        return wrapped_f



class MultipleAPIKeysDecorator(object):
    """
    Add an API key to perform the requests. If a key has a 
    Ratelimit-Remaining of 0, switch to the next key. 
    Raise IndexError if no more keys are available.
    """

    def __init__(self, keys):
        self.keys = keys
        self.current_key = 0

    def __call__(self, f):
        @functools.wraps(f)
        def wrapped_f(url, *args, **kwargs):
            while True:
                headers = kwargs.get('headers', {})
                try:
                    headers['Authorization'] = 'token '+self.keys[self.current_key]
                except IndexError as e:
                    raise IndexError('No more API key can be used')
                kwargs['headers'] = headers
                r = f(url, *args, **kwargs)
                if r.status_code == 403 and r.headers['X-RateLimit-Remaining'] == '0':
                    self.current_key += 1
                else:
                    return r
        return wrapped_f
