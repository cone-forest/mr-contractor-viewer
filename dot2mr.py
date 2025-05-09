import pygraphviz as pgv
import networkx as nx
from networkx.algorithms.components import weakly_connected_components

def generate_component_structure(component_subgraph):
    """
    Generate the execution structure for a directed acyclic graph component.
    
    Each node represents a task, and edges represent dependencies between tasks.
    Tasks are grouped into sequences and parallels based on their dependencies.
    """
    try:
        layers = list(nx.topological_generations(component_subgraph))
    except nx.NetworkXUnfeasible:
        raise ValueError("Graph contains a cycle, which is not supported for execution graphs.")

    if not layers:
        return None

    # If there's only one node, return it directly
    if len(layers) == 1 and len(layers[0]) == 1:
        node_name = next(iter(layers[0]))
        return {'type': 'Node', 'name': node_name}

    # Identify nodes that form direct sequences (one-to-one paths)
    # by checking for nodes with a single successor and nodes with a single predecessor
    def find_direct_sequence_paths(graph, start_nodes):
        """Find paths where nodes form a direct sequence"""
        sequence_paths = {}
        for node in start_nodes:
            path = [node]
            current = node
            # Follow nodes that have exactly one successor and the successor has exactly one predecessor
            while True:
                successors = list(graph.successors(current))
                if len(successors) != 1:
                    break
                
                next_node = successors[0]
                predecessors = list(graph.predecessors(next_node))
                if len(predecessors) != 1:
                    break
                
                path.append(next_node)
                current = next_node
            
            if len(path) > 1:
                sequence_paths[node] = path
        return sequence_paths

    # Process each layer and build the structure
    processed_nodes = set()
    structure = []
    
    for i, layer in enumerate(layers):
        # Skip nodes we've already processed as part of sequences
        current_layer = [node for node in layer if node not in processed_nodes]
        if not current_layer:
            continue
        
        # If this is a single node in the layer, add it directly
        if len(current_layer) == 1 and i < len(layers) - 1:
            node = current_layer[0]
            # Check if this node starts a sequence
            sequence_paths = find_direct_sequence_paths(component_subgraph, [node])
            if node in sequence_paths:
                path = sequence_paths[node]
                sequence_nodes = [{'type': 'Node', 'name': n} for n in path]
                structure.append({'type': 'Sequence', 'children': sequence_nodes})
                processed_nodes.update(path)
            else:
                structure.append({'type': 'Node', 'name': node})
                processed_nodes.add(node)
        else:
            # Group nodes by their successor patterns
            successor_groups = {}
            for node in current_layer:
                # Get successors
                successors = sorted(list(component_subgraph.successors(node)))
                key = tuple(successors)
                if key not in successor_groups:
                    successor_groups[key] = []
                successor_groups[key].append(node)
            
            # Process each group separately
            parallel_children = []
            for succ_key, nodes in successor_groups.items():
                if len(nodes) == 1:
                    node = nodes[0]
                    # Check if this node starts a sequence
                    sequence_paths = find_direct_sequence_paths(component_subgraph, [node])
                    if node in sequence_paths:
                        path = sequence_paths[node]
                        sequence_nodes = [{'type': 'Node', 'name': n} for n in path]
                        parallel_children.append({'type': 'Sequence', 'children': sequence_nodes})
                        processed_nodes.update(path)
                    else:
                        parallel_children.append({'type': 'Node', 'name': node})
                        processed_nodes.add(node)
                else:
                    # Multiple nodes with the same successor pattern - can be parallel
                    parallel_children.extend([{'type': 'Node', 'name': n} for n in nodes])
                    processed_nodes.update(nodes)
            
            # If we have multiple group children, make them parallel
            if len(parallel_children) > 1:
                structure.append({'type': 'Parallel', 'children': parallel_children})
            elif len(parallel_children) == 1:
                structure.append(parallel_children[0])
    
    # Combine everything into a sequence
    if len(structure) == 1:
        return structure[0]
    else:
        return {'type': 'Sequence', 'children': structure}

def format_structure(struct, indent_level=0):
    indent = '  ' * indent_level
    if struct['type'] == 'Node':
        return f"{indent}{struct['name']}"
    elif struct['type'] in ('Sequence', 'Parallel'):
        children = [format_structure(c, indent_level + 1) for c in struct['children']]
        children_str = ',\n'.join(children)
        return f"{indent}{struct['type']} {{\n{children_str}\n{indent}}}"

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <dot_file>")
        sys.exit(1)

    filename = sys.argv[1]
    graph = pgv.AGraph(filename)
    nx_graph = nx.nx_agraph.from_agraph(graph)

    components = list(weakly_connected_components(nx_graph))

    component_structures = []
    for component in components:
        subgraph = nx_graph.subgraph(component)
        try:
            component_struct = generate_component_structure(subgraph)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        component_structures.append(component_struct)

    if len(component_structures) > 1:
        final_structure = {'type': 'Parallel', 'children': component_structures}
    elif len(component_structures) == 1:
        final_structure = component_structures[0]
    else:
        print("Empty graph")
        return

    print(format_structure(final_structure))

if __name__ == "__main__":
    main()
