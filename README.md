# Outils et analyses de dépôts GitHub

Le présent dépôt propose un petit ensemble d'outils et d'analyses de dépôts GitHub, principalement orientés sur l'analyse des dépôts liés au langage R. Ces outils et ces analyses sont effectuées dans le cadre du projet ECOS dans les services d'Écologie Numérique des Milieux Aquatiques et de Génie Logiciel de la Faculté des Sciences de l'Université de Mons.


## Organisation du dépôt

### data/

Ce répertoire contient certaines des données qui sont utilisées dans le cadre des experiences. Ces données sont soit collectées directement depuis des sources en ligne (github, githubarchive, CRAN, ...) soit via un processus détaillé dans les notebooks du dépôts.

 - *bioconductor_description.csv* : liste des packages R disponibles sur le dépôt BioConductor. Chaque package est associé aux metadata de son fichier DESCRIPTION. Généré à partir du notebook *BioConductor.ipynb*.
 - *cran-description.csv* : liste des packages R disponibles sur le dépôt CRAN. Chaque package est également associé aux metadata de son fichier DESCRIPTION. Généré par Maelick Claes.
 - *github-description.csv* : liste des packages R disponibles sur GitHub. A nouveau, chaque package est associé aux metadata de son fichier DESCRIPTION. Les données ont été collectées en suivant la procédure expliquée dans le notebook *GitHubArchive.ipynb*.
 - *github_R_pushevents.csv* : liste des événements de type "PushEvent" liés à des packages R présents sur GitHub. Les données ont été collectées depuis GitHubArchive (voir *GitHubArchive.ipynb*) et ensuite injectée dans une base MongoDB. Cette base MongoDB a servi de source à ce fichier .csv.
 
### notebooks/

Ce répertoire contient différents notebooks visant à expliquer les étapes permettant de manipuler les données et d'en déduire quelques statistiques ou graphiques. Chaque notebook est auto-documenté et nécessite IPython Notebook pour être visualisé et exécuté. Une version HTML du notebook est également fournie. Cette version reprend l'output du notebook, même si certaines parties sont parfois manquantes (à signaler, ce sera corrigé).

A noter que la plupart de ces notebooks nécessitent des librairies externes (identifiables via les `import` faits en Python). Ces notebooks nécessitent aussi certains fichiers présents dans le répertoire `/data` et, dans certains cas, une base MongoDB telle que décrite dans *GitHubArchive.ipynb*.

### decorators.py

This module provides decorators that are intented to be used with `requests.get`, `requests.post`, etc.

#### `prepend_url(prepended_url)` 
This decorator prepend the url given to `requests.get` by the value of `prepended_url`. Should be used after every other decorator. 

```python
consumer = decorators.prepend_url('https://api.github.com/')(requests.get)
```

#### `InMemoryCacheDecorator(cache=None)`
This decorator stores every call with an in-memory data structure (i.e. a dictionary) for subsequent calls. You may provide a non-empty dictionary to pre-populated the cache. Consult stderr to see if a cached value is retrieved.

```python
consumer = decorators.InMemoryCacheDecorator()(requests.post) 
```

#### `RedisBackendCacheDecorator(**kwargs)`
This decorator acts like `InMemoryCacheDecorator` but uses a Redis datastore. It relies on the ETag value of a requests to determine if a cached value has to be retrieved or if a new request has to be done, following this simple algorithm:
 - if the request concerns an unknown url, perform the request and store the results (only if `status_code == 200`). 
 - If the request concerns a known url, which exists in Redis, then retrieve the stored ETag for this url. A `If-None-Match` header is added to the request, with the corresponding ETag. If `status_code == 304`, it returns stored value. Otherwise, it updates the cache and returns the result. 

The constructor will pass every provided keyword argument to `redis.StrictRedis` (see `redis` module documentation). 

```python
consumer = decorators.RedisBackendCacheDecorator(host='10.102.170.77', db=5)(requests.get)
```
Consult stderr to see if a cached value is used, or if the cache is updated.

#### `MultipleAPIKeysDecorator(keys)`
This decorator populate the header *Authorization* with an API key, allowing more requests by hour. You should provide a list of API keys to this decorator. If a key has a Ratelimit-remaining of 0, then the next key is used, and so on, until no more key is available (in this case, an `IndexError` is raised).

```python
consumer = decorators.MultipleAPIKeysDecorator(['YOUR_API_KEY_1', 'YOUR_API_KEY_2'])(requests.get)
```
