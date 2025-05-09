#!/usr/bin/env python3
import sys
import re

def parse_custom_format(text):
    """Parse the custom execution graph format into a structured representation."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Helper function to parse the content recursively
    def parse(lines, start_idx=0):
        if start_idx >= len(lines):
            return None, start_idx
        
        current_line = lines[start_idx].strip()
        
        # Check for Sequence or Parallel block
        if current_line.startswith('Sequence {') or current_line == 'Sequence {':
            block_type = 'Sequence'
            children = []
            idx = start_idx + 1
            
            # Parse the children of the sequence
            while idx < len(lines) and not lines[idx].strip() == '}':
                if lines[idx].strip() == '},':
                    idx += 1
                    break
                    
                child, idx = parse(lines, idx)
                if child:
                    children.append(child)
            
            # Skip the closing brace
            if idx < len(lines) and lines[idx].strip() == '}':
                idx += 1
                
            return {'type': block_type, 'children': children}, idx
            
        elif current_line.startswith('Parallel {') or current_line == 'Parallel {':
            block_type = 'Parallel'
            children = []
            idx = start_idx + 1
            
            # Parse the children of the parallel
            while idx < len(lines) and not lines[idx].strip() == '}':
                if lines[idx].strip() == '},':
                    idx += 1
                    break
                    
                child, idx = parse(lines, idx)
                if child:
                    children.append(child)
            
            # Skip the closing brace
            if idx < len(lines) and lines[idx].strip() == '}':
                idx += 1
                
            return {'type': block_type, 'children': children}, idx
            
        else:
            # This is a node - extract the name
            node_name = current_line.rstrip(',')
            return {'type': 'Node', 'name': node_name}, start_idx + 1
    
    # Start parsing from the beginning
    tree, _ = parse(lines)
    return tree

def convert_to_dot(tree):
    """Convert the parsed tree to DOT graph format."""
    # Helper function to extract all nodes
    def extract_nodes(node):
        if node['type'] == 'Node':
            return [node['name']]
        
        nodes = []
        for child in node['children']:
            nodes.extend(extract_nodes(child))
        return nodes
    
    # Helper function to generate edges
    def generate_edges(node):
        if node['type'] == 'Node':
            return [], [node['name']]
        
        if node['type'] == 'Sequence':
            all_edges = []
            prev_exit_nodes = None
            
            for child in node['children']:
                child_edges, exit_nodes = generate_edges(child)
                all_edges.extend(child_edges)
                
                # Connect previous exit nodes to current child's entry nodes
                if prev_exit_nodes:
                    for prev in prev_exit_nodes:
                        for curr in extract_entry_nodes(child):
                            all_edges.append((prev, curr))
                
                prev_exit_nodes = exit_nodes
            
            # Return all edges and the exit nodes
            return all_edges, prev_exit_nodes
            
        elif node['type'] == 'Parallel':
            all_edges = []
            all_exit_nodes = []
            
            for child in node['children']:
                child_edges, exit_nodes = generate_edges(child)
                all_edges.extend(child_edges)
                all_exit_nodes.extend(exit_nodes)
            
            return all_edges, all_exit_nodes
    
    # Helper function to find entry nodes (first nodes in execution)
    def extract_entry_nodes(node):
        if node['type'] == 'Node':
            return [node['name']]
        
        if node['type'] == 'Sequence':
            return extract_entry_nodes(node['children'][0]) if node['children'] else []
            
        elif node['type'] == 'Parallel':
            entry_nodes = []
            for child in node['children']:
                entry_nodes.extend(extract_entry_nodes(child))
            return entry_nodes
    
    # Get all nodes and edges
    all_nodes = extract_nodes(tree)
    all_edges, _ = generate_edges(tree)
    
    # Build DOT format
    dot_content = "digraph ExecutionGraph {\n"
    
    # Add nodes
    for node in sorted(set(all_nodes)):
        dot_content += f"  {node};\n"
    
    # Add edges (avoiding duplicates)
    added_edges = set()
    for src, dst in all_edges:
        if (src, dst) not in added_edges:
            dot_content += f"  {src} -> {dst};\n"
            added_edges.add((src, dst))
    
    dot_content += "}\n"
    return dot_content

def main():
    if len(sys.argv) != 2:
        print("Usage: python mr2dot.py <input_file>")
        sys.exit(1)
    
    try:
        with open(sys.argv[1], 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File {sys.argv[1]} not found.")
        sys.exit(1)
    
    try:
        tree = parse_custom_format(content)
        dot_content = convert_to_dot(tree)
        print(dot_content)
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
