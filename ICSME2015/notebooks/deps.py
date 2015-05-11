#!/usr/bin/python

import pandas

R_packages = ('R MASS Matrix base boot class cluster codetools compiler datasets foreign grDevices ' +
        'graphics grid lattice methods mgcv nlme nnet parallel rpart ' +
        'spatial splines stats stats4 survival tcltk tools translations utils').split(' ')


def create_graph_for(data, date, using=['Imports', 'Depends'], ignore_R=True):
    """
    Initialize a graph structure through a dictionary. The graph is built using the 
    data in `data` for the given date. The dependencies are made upon the items in 
    `using`. If ignore_R is set to True, then every package that is bundled with 
    R will be ignored in the graph (not in the edges!). 

    The resulting structure is a dict associating a dict of sources to every package
    name. The dict of sources associates the meta data of the package in this source
    with its source name. 
    """
    data = data.sort('Date').query('Date <= "{date}"'.format(date=date)).drop_duplicates(('Package', 'Source'), take_last=True).fillna('')
    packages = {}
    for idx, row in data.iterrows():
        if ignore_R and row['Package'] in R_packages:
            continue
        package = packages.setdefault(row['Package'], {})
        source = {
            'Package': row['Package'], 
            'Version': row['Version'], 
            'Date': row['Date'],
            'Metadata': row,
            'Dependencies': set()
        }
        for use in using: 
            for item in row[use].split(' '):
                if len(item.strip()) > 0:
                    source['Dependencies'].add(item)

        package[row['Source']] = source
    return packages


def available(graph, package, sources):
    if len(sources) == 0:
        return False
    package_sources = graph.get(package, {}).iterkeys()
    return not set(package_sources).isdisjoint(set(sources))


def installable(graph, from_source, sources, ignored_packages=R_packages):
    """
    CURRENTLY NOT WORKING!!!!!!!
    Return the packages from `from_source` in graph that are installable using the sources of 
    `sources`. `ignored_packages` contains a list of packages that are 
    considered to be available and that will be ignored during the check of 
    the dependencies. 
    """

    memory = {}

    def is_installable(name):
        # Already checked?
        if name in memory:
            return memory[name]

        # Avoid cycles
        memory[name] = False

        # Allowed package?
        if name in ignored_packages:
            memory[name] = True
            return True
        
        # Unknown package?
        if name not in graph:
            memory[name] = False
            return False

        # For every source that is allowed
        for source in filter(lambda s: s in sources, graph[name].iterkeys()):
            # Get dependencies
            dependencies = graph[name][source]['Dependencies']

            # No dependency, installable!
            if len(dependencies) == 0:
                memory[name] = True
                return True

            # The dependencies must be available AND installable
            # Check availability first as it is cheaper
            if all((available(graph, dep, sources) for dep in dependencies)):
                # Check installability
                if all((is_installable(dep) for dep in dependencies)):
                    # Ok, return True
                    memory[name] = True
                    return True

        memory[name] = False
        return False

    results = []

    for name in graph.iterkeys():
        if from_source in graph[name].iterkeys():
            installable = True
            for dependency in graph[name][from_source]['Dependencies']:
                if not is_installable(dependency):
                    installable = False
                    break
            if installable:
                results.append(name)
    return results        

