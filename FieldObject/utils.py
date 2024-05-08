from collections import defaultdict

def has_loop(graph, node, visited, recursion_stack):
    visited[node] = True
    recursion_stack[node] = True

    for neighbor in graph[node]:
        if not visited[neighbor]:
            if has_loop(graph, neighbor, visited, recursion_stack):
                return True
        elif recursion_stack[neighbor]:
            return True

    recursion_stack[node] = False
    return False

def check_loop(seq, new_path):
    """
    :Params:
        - seq: List[str] (Represent the path ["A", "B", "C", "D"])
        - new_path: List[str] (Represent the new link ["B", "A"])
    """
    graph = defaultdict(list)

    # Represent the sequence as a graph
    for i in range(len(seq) - 1):
        graph[seq[i]].append(seq[i + 1])
    # {"A": ["B", "C", "D"], "B": ["C", "D"], "C": ["D"]}
    
    # Add the new link to the graph
    graph[new_path[0]].append(new_path[1])
    # {"A": ["B", "C", "D"], "B": ["C", "D", "A"], "C": ["D"]}

    visited = {node: False for node in seq}
    recursion_stack = {node: False for node in seq}

    # Check for loops using DFS
    for node in seq:
        if not visited[node]:
            if has_loop(graph, node, visited, recursion_stack):
                return True

    return False