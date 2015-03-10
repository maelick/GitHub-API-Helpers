# Outils et analyses de dépôts GitHub

Le présent dépôt propose un petit ensemble d'outils et d'analyses de dépôts GitHub, principalement orientés sur l'analyse des dépôts liés au langage R. 

Les outils sont repris ci-dessous et consistent essentiellement en de petits décorateurs visant à simplifier l'accès à l'API de GitHub. 
Les autres outils sont documentés dans les notebooks IPython présents sur le dépôt. 

## decorators.py

This module provides decorators that are intented to be used with `requests.get`, `requests.post`, etc.

##### `prepend_url(prepended_url)` 
This decorator prepend the url given to `requests.get` by the value of `prepended_url`. Should be used after every other decorator. 

```python
consumer = decorators.prepend_url('https://api.github.com/')(requests.get)
```

##### `InMemoryCacheDecorator(cache=None)`
This decorator stores every call with an in-memory data structure (i.e. a dictionary) for subsequent calls. You may provide a non-empty dictionary to pre-populated the cache. Consult stderr to see if a cached value is retrieved.

```python
consumer = decorators.InMemoryCacheDecorator()(requests.post) 
```

##### `RedisBackendCacheDecorator(**kwargs)`
This decorator acts like `InMemoryCacheDecorator` but uses a Redis datastore. It relies on the ETag value of a requests to determine if a cached value has to be retrieved or if a new request has to be done, following this simple algorithm:
 - if the request concerns an unknown url, perform the request and store the results (only if `status_code == 200`). 
 - If the request concerns a known url, which exists in Redis, then retrieve the stored ETag for this url. A `If-None-Match` header is added to the request, with the corresponding ETag. If `status_code == 304`, it returns stored value. Otherwise, it updates the cache and returns the result. 

The constructor will pass every provided keyword argument to `redis.StrictRedis` (see `redis` module documentation). 

```python
consumer = decorators.RedisBackendCacheDecorator(host='10.102.170.77', db=5)(requests.get)
```
Consult stderr to see if a cached value is used, or if the cache is updated.

##### `MultipleAPIKeysDecorator(keys)`
This decorator populate the header *Authorization* with an API key, allowing more requests by hour. You should provide a list of API keys to this decorator. If a key has a Ratelimit-remaining of 0, then the next key is used, and so on, until no more key is available (in this case, an `IndexError` is raised).

```python
consumer = decorators.MultipleAPIKeysDecorator(['YOUR_API_KEY_1', 'YOUR_API_KEY_2'])(requests.get)
```
