# Graph Format Converter

A simple GUI application for converting between GraphViz DOT format, Mermaid format, and a custom sequence/parallel execution graph format.

## Features

- Three-way conversion between custom format, GraphViz DOT format, and Mermaid format
- Real-time rendering of the graph
- Automatic synchronization between editors
- Error handling with helpful messages

## Requirements

- Python 3.6+
- PyQt5
- Pygraphviz
- NetworkX
- Graphviz (the command-line tool)

## Installation

1. Install the required Python packages:

```bash
pip install PyQt5 networkx pygraphviz
```

2. Install Graphviz:

- **Linux**: `sudo apt-get install graphviz`
- **macOS**: `brew install graphviz`
- **Windows**: Download from [Graphviz website](https://graphviz.org/download/)

## Usage

1. Run the GUI application:

```bash
python gui.py
```

2. The window is divided into four sections:
   - Top-left: Custom format editor
   - Top-right: GraphViz DOT format editor
   - Bottom-left: Mermaid format editor
   - Bottom-right: Rendered graph

3. Edit any of the three formats, and the others will automatically update after a 1-second pause.

## Supported Formats

### Custom Format Syntax

The custom format represents execution graphs with tasks and dependencies:

```
Sequence {
  task1,
  Parallel {
    task2,
    task3,
  },
  task4,
}
```

- `Sequence`: Tasks that must run in order
- `Parallel`: Tasks that can run concurrently
- Each task is represented by its name

### Mermaid Format

[Mermaid](https://mermaid-js.github.io/) is a Markdown-like syntax for creating diagrams:

```
flowchart TD
    A[A] --> B[B]
    A --> C[C]
    B --> D[D]
    C --> D
```

- `flowchart TD`: Top-down flowchart
- Arrow syntax (`-->`) defines dependencies between tasks
- Square brackets `[Task]` can be used for node labels

## Examples

### Linear Graph

Custom format:
```
Sequence {
  q0,
  q1,
  q2,
  q3,
}
```

DOT format:
```
digraph ExecutionGraph {
  q0;
  q1;
  q2;
  q3;
  q0 -> q1;
  q1 -> q2;
  q2 -> q3;
}
```

Mermaid format:
```
flowchart TD
    q0[q0] --> q1[q1]
    q1 --> q2[q2]
    q2 --> q3[q3]
```

### Parallel Branches

Custom format:
```
Sequence {
  q0,
  Parallel {
    q1,
    q2,
  },
  q3,
}
```

DOT format:
```
digraph ExecutionGraph {
  q0;
  q1;
  q2;
  q3;
  q0 -> q1;
  q0 -> q2;
  q1 -> q3;
  q2 -> q3;
}
```

Mermaid format:
```
flowchart TD
    q0[q0] --> q1[q1]
    q0 --> q2[q2]
    q1 --> q3[q3]
    q2 --> q3
```

## Troubleshooting

- If you encounter errors with graph rendering, make sure Graphviz is properly installed and available in your PATH
- For import errors, ensure that all required Python files (`dot2mr.py`, `mr2dot.py`, and `dot_to_mermaid.py`) are in the same directory as `gui.py`
- Check the console output for detailed error messages

## License

This project is open source and available under the MIT License. 