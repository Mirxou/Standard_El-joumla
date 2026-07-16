class Graph:
    def __init__(self):
        self._adj = {}

    def add_node(self, n):
        if n not in self._adj:
            self._adj[n] = set()

    def add_edge(self, u, v):
        self.add_node(u)
        self.add_node(v)
        self._adj[u].add(v)
        self._adj[v].add(u)

    def number_of_nodes(self):
        return len(self._adj)

    def number_of_edges(self):
        return sum(len(neighbors) for neighbors in self._adj.values()) // 2

    def degree(self):
        return {n: len(neighbors) for n, neighbors in self._adj.items()}

    def __iter__(self):
        return iter(self._adj)


def density(G):
    n = G.number_of_nodes()
    m = G.number_of_edges()
    if n < 2:
        return 0.0
    return (2.0 * m) / (n * (n - 1))


def number_connected_components(G):
    visited = set()
    count = 0
    for node in list(G._adj.keys()):
        if node not in visited:
            count += 1
            stack = [node]
            visited.add(node)
            while stack:
                cur = stack.pop()
                for nb in G._adj.get(cur, set()):
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
    return count


def degree_centrality(G):
    n = G.number_of_nodes()
    deg = G.degree()
    if n <= 1:
        return {node: 0.0 for node in G._adj}
    return {node: d / (n - 1) for node, d in deg.items()}
