from collections import deque

# Resiliency metric
# Taken from https://codereview.stackexchange.com/questions/184392/computing-resilience-of-the-network-presented-as-an-undirected-graph-in-python
def resilience(graph, attack_order):
    """Given an undirected graph represented as a mapping from nodes to
    an iterable of their neighbours, and an iterable of nodes, generate
    integers such that the the k-th result is the size of the largest
    connected component after the removal of the first k-1 nodes.

    """
    # Take a copy of the graph so that we can destructively modify it.
    graph = {node: set(neighbours) for node, neighbours in graph.items()}

    canonical, components = connected_components(graph, set(graph))
    largest = lambda: max(map(len, components.values()), default=0)
    yield largest()
    for node in attack_order:
        # Find connected component containing node.
        component = components.pop(canonical.pop(node))

        # Remove node from graph.
        for neighbor in graph[node]:
            graph[neighbor].remove(node)
        graph.pop(node)
        component.remove(node)

        # Component may have been split by removal of node, so search
        # it for new connected components and update data structures
        # accordingly.
        canon, comp = connected_components(graph, component)
        canonical.update(canon)
        components.update(comp)
        yield largest()
        
    def connected_components(graph, nodes):
        """Given an undirected graph represented as a mapping from nodes to
        the set of their neighbours, and a set of nodes, find the
        connected components in the graph containing those nodes.

        Returns:
        - mapping from nodes to the canonical node of the connected
        component they belong to
        - mapping from canonical nodes to connected components

        """
        canonical = {}
        components = {}
        while nodes:
            node = nodes.pop()
            component = bfs_visited(graph, node)
            components[node] = component
            nodes.difference_update(component)
            for n in component:
                canonical[n] = node
        return canonical, components

    def bfs_visited(graph, node):
        """undirected graph {Vertex: {neighbors}}
        Returns the set of all nodes visited by the algrorithm"""
        queue = deque()
        queue.append(node)
        visited = set([node])
        while queue:
            current_node = queue.popleft()
            for neighbor in graph[current_node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return visited
    
    
if __name__ == '__main__':
    print('hello world')
    import osmnx as ox
    from pprint import pprint
    from loader import carall_from_polygon, bike_infra_from_polygon

    rochester = ox.geocode_to_gdf('rochester, ny').geometry[0]
    # carall = carall_from_polygon(rochester, add_pois=True)
    bike_infra = bike_infra_from_polygon(rochester)
    pprint(bike_infra)
    
    
