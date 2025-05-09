#!/usr/bin/env python3
import re

def dot_to_mermaid(dot_content):
    """
    Convert GraphViz DOT format to Mermaid flowchart format.
    """
    # Initialize the mermaid content with flowchart directive
    mermaid_content = "flowchart TD\n"
    
    # Regular expressions to match nodes and edges in DOT
    node_pattern = re.compile(r'\s*([a-zA-Z0-9_]+)\s*;')
    edge_pattern = re.compile(r'\s*([a-zA-Z0-9_]+)\s*->\s*([a-zA-Z0-9_]+)\s*;')
    
    # Process each line
    lines = dot_content.splitlines()
    for line in lines:
        line = line.strip()
        
        # Skip digraph line and braces
        if line.startswith('digraph') or line == '{' or line == '}':
            continue
        
        # Check for edge
        edge_match = edge_pattern.match(line)
        if edge_match:
            from_node, to_node = edge_match.groups()
            mermaid_content += f"    {from_node} --> {to_node}\n"
            continue
        
        # Check for node
        node_match = node_pattern.match(line)
        if node_match:
            node = node_match.group(1)
            mermaid_content += f"    {node}[{node}]\n"
    
    return mermaid_content

def mermaid_to_dot(mermaid_content):
    """
    Convert Mermaid flowchart format to GraphViz DOT format.
    This is a basic implementation that only handles simple flowcharts.
    """
    # Initialize DOT content
    dot_content = "digraph ExecutionGraph {\n"
    
    # Regular expressions to match nodes and edges in Mermaid
    node_pattern = re.compile(r'\s*([a-zA-Z0-9_]+)\s*\[\s*([^\]]+)\s*\]')
    simple_node_pattern = re.compile(r'\s*([a-zA-Z0-9_]+)\s*$')
    edge_pattern = re.compile(r'\s*([a-zA-Z0-9_]+)\s*-->\s*([a-zA-Z0-9_]+)')
    
    # Track nodes and edges to avoid duplicates
    nodes = set()
    edges = set()
    
    # Process each line
    lines = mermaid_content.splitlines()
    for line in lines:
        line = line.strip()
        
        # Skip flowchart declaration line
        if line.startswith('flowchart'):
            continue
        
        # Check for edge
        edge_match = edge_pattern.search(line)
        if edge_match:
            from_node, to_node = edge_match.groups()
            nodes.add(from_node)
            nodes.add(to_node)
            edges.add((from_node, to_node))
            continue
        
        # Check for node with label
        node_match = node_pattern.match(line)
        if node_match:
            node_id, node_label = node_match.groups()
            nodes.add(node_id)
            continue
            
        # Check for simple node
        simple_node_match = simple_node_pattern.match(line)
        if simple_node_match:
            node_id = simple_node_match.group(1)
            nodes.add(node_id)
    
    # Add nodes to DOT content
    for node in sorted(nodes):
        dot_content += f"  {node};\n"
    
    # Add edges to DOT content
    for from_node, to_node in sorted(edges):
        dot_content += f"  {from_node} -> {to_node};\n"
    
    dot_content += "}\n"
    return dot_content

if __name__ == "__main__":
    # Test conversion
    dot_example = """
    digraph ExecutionGraph {
      q0;
      q1;
      q2;
      q3;
      q0 -> q1;
      q1 -> q2;
      q2 -> q3;
    }
    """
    
    mermaid = dot_to_mermaid(dot_example)
    print("DOT to Mermaid conversion:")
    print(mermaid)
    
    print("\nMermaid to DOT conversion:")
    print(mermaid_to_dot(mermaid)) 