#!/usr/bin/env python3
import sys
import tempfile
import os
import subprocess
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QLabel, QSplitter, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

# Import custom script functions
try:
    from dot2mr import format_structure, generate_component_structure
    from mr2dot import parse_custom_format as parse_mr, convert_to_dot
    from dot_to_mermaid import dot_to_mermaid, mermaid_to_dot
except ImportError as e:
    print(f"Error importing conversion modules: {e}")
    print("Make sure dot2mr.py, mr2dot.py, and dot_to_mermaid.py are in the same directory as this script.")
    sys.exit(1)

class GraphConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graph Format Converter")
        self.setGeometry(100, 100, 1200, 800)

        # Create the main widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Create a main vertical layout
        main_layout = QVBoxLayout(self.main_widget)

        # Create a splitter for the top and bottom parts
        self.v_splitter = QSplitter(Qt.Vertical)

        # Create splitters for the upper and lower parts
        self.upper_splitter = QSplitter(Qt.Horizontal)
        self.lower_splitter = QSplitter(Qt.Horizontal)

        # Add the upper and lower splitters to the vertical splitter
        self.v_splitter.addWidget(self.upper_splitter)
        self.v_splitter.addWidget(self.lower_splitter)

        # Add widgets to the upper splitter (custom format and DOT format)
        self.custom_format_widget = QWidget()
        self.custom_format_layout = QVBoxLayout(self.custom_format_widget)
        self.custom_format_label = QLabel("Custom Format")
        self.custom_format_layout.addWidget(self.custom_format_label)

        self.dot_format_widget = QWidget()
        self.dot_format_layout = QVBoxLayout(self.dot_format_widget)
        self.dot_format_label = QLabel("GraphViz DOT Format")
        self.dot_format_layout.addWidget(self.dot_format_label)

        self.upper_splitter.addWidget(self.custom_format_widget)
        self.upper_splitter.addWidget(self.dot_format_widget)

        # Add widgets to the lower splitter (Mermaid Format and Rendered Graph)
        self.mermaid_widget = QWidget()
        self.mermaid_layout = QVBoxLayout(self.mermaid_widget)
        self.mermaid_label = QLabel("Mermaid Format")
        self.mermaid_layout.addWidget(self.mermaid_label)

        self.graph_widget = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_widget)
        self.graph_label = QLabel("Rendered Graph")
        self.graph_layout.addWidget(self.graph_label)

        self.lower_splitter.addWidget(self.mermaid_widget)
        self.lower_splitter.addWidget(self.graph_widget)

        # Add the splitter to the main layout
        main_layout.addWidget(self.v_splitter)

        # Set equal sizes for all sections
        self.upper_splitter.setSizes([600, 600])
        self.lower_splitter.setSizes([600, 600])
        self.v_splitter.setSizes([400, 400])

        # Initialize instance variables
        self.last_updated = "custom"  # Default to custom format at startup
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.sync_editors)

        # Flag to track if we're updating the editor content programmatically
        self.is_updating = False

        # Temp file for graph rendering
        self.temp_dir = tempfile.mkdtemp()
        self.dot_file_path = os.path.join(self.temp_dir, "graph.dot")
        self.image_file_path = os.path.join(self.temp_dir, "graph.png")

        # Setup the application
        self.setup_ui()

    def setup_ui(self):
        # Add text editors to the upper sections
        self.custom_text = QPlainTextEdit()
        self.custom_text.setPlainText("""Sequence {
  q1,
  Parallel {
    Sequence {
      q2,
      q4,
    },
    q3,
  },
  q5,
}""")
        self.custom_text.setFont(QFont("Monospace", 10))
        self.custom_text.textChanged.connect(lambda: self.text_changed("custom"))
        self.custom_format_layout.addWidget(self.custom_text)

        self.dot_text = QPlainTextEdit()
        self.dot_text.setFont(QFont("Monospace", 10))
        self.dot_text.textChanged.connect(lambda: self.text_changed("dot"))
        self.dot_format_layout.addWidget(self.dot_text)

        # Set up the Mermaid format section
        self.mermaid_text = QPlainTextEdit()
        self.mermaid_text.setFont(QFont("Monospace", 10))
        self.mermaid_text.textChanged.connect(lambda: self.text_changed("mermaid"))
        self.mermaid_layout.addWidget(self.mermaid_text)

        # Set up the graph visualization section
        self.graph_scroll = QScrollArea()
        self.graph_scroll.setWidgetResizable(True)

        self.graph_content = QLabel("Initializing graph display...")
        self.graph_content.setAlignment(Qt.AlignCenter)
        self.graph_scroll.setWidget(self.graph_content)

        self.graph_layout.addWidget(self.graph_scroll)

        # Initial conversion from custom to DOT
        self.sync_editors()

    def text_changed(self, source):
        """Called when text changes in either editor"""
        # Don't trigger update if we're programmatically updating the editors
        if self.is_updating:
            return

        self.last_updated = source
        # Wait 1 second before syncing to avoid constant updates while typing
        self.update_timer.start(1000)

    def sync_editors(self):
        """Sync the content between the editors"""
        if self.is_updating:
            return

        self.is_updating = True
        try:
            # Handle conversion based on which editor was last updated
            if self.last_updated == "custom":
                # Convert custom format to DOT
                custom_text = self.custom_text.toPlainText()
                if not custom_text.strip():
                    self.dot_text.setPlainText("")
                    self.mermaid_text.setPlainText("")
                    self.clear_graph()
                    self.is_updating = False
                    return

                try:
                    # Parse and convert to DOT
                    tree = parse_mr(custom_text)
                    dot_content = convert_to_dot(tree)
                    
                    # Update DOT text
                    self.dot_text.setPlainText(dot_content)
                    
                    # Convert DOT to Mermaid
                    mermaid_content = dot_to_mermaid(dot_content)
                    self.mermaid_text.setPlainText(mermaid_content)
                    
                    # Render the graph
                    self.render_graph(dot_content)
                except Exception as e:
                    self.show_error(f"Error converting custom format: {str(e)}")
                    traceback.print_exc()

            elif self.last_updated == "dot":
                # Convert DOT to custom format and Mermaid
                dot_text = self.dot_text.toPlainText()
                if not dot_text.strip():
                    self.custom_text.setPlainText("")
                    self.mermaid_text.setPlainText("")
                    self.clear_graph()
                    self.is_updating = False
                    return

                try:
                    # Write DOT content to temp file for processing
                    with open(self.dot_file_path, 'w') as f:
                        f.write(dot_text)
                    
                    # Convert DOT to Mermaid
                    try:
                        mermaid_content = dot_to_mermaid(dot_text)
                        self.mermaid_text.setPlainText(mermaid_content)
                    except Exception as e:
                        self.show_error(f"Error converting DOT to Mermaid: {str(e)}")
                    
                    # Convert DOT to custom format
                    try:
                        # Import the graph with pygraphviz
                        import pygraphviz as pgv
                        import networkx as nx

                        graph = pgv.AGraph(self.dot_file_path)
                        nx_graph = nx.nx_agraph.from_agraph(graph)

                        # Process the graph using the imported functions
                        components = list(nx.algorithms.components.weakly_connected_components(nx_graph))

                        component_structures = []
                        for component in components:
                            subgraph = nx_graph.subgraph(component)
                            component_struct = generate_component_structure(subgraph)
                            component_structures.append(component_struct)

                        if len(component_structures) > 1:
                            final_structure = {'type': 'Parallel', 'children': component_structures}
                        elif len(component_structures) == 1:
                            final_structure = component_structures[0]
                        else:
                            final_structure = None

                        if final_structure:
                            custom_content = format_structure(final_structure)
                            self.custom_text.setPlainText(custom_content)

                    except ImportError:
                        self.show_error("Failed to import pygraphviz or networkx. "
                                        "Please install with: pip install pygraphviz networkx")
                    except Exception as e:
                        self.show_error(f"Error converting DOT to custom format: {str(e)}")
                        traceback.print_exc()
                    
                    # Always render the graph if DOT format seems valid
                    self.render_graph(dot_text)
                    
                except Exception as e:
                    self.show_error(f"Error processing DOT format: {str(e)}")
                    traceback.print_exc()
                    
            elif self.last_updated == "mermaid":
                # Convert Mermaid to DOT, then to custom format
                mermaid_text = self.mermaid_text.toPlainText()
                if not mermaid_text.strip():
                    self.custom_text.setPlainText("")
                    self.dot_text.setPlainText("")
                    self.clear_graph()
                    self.is_updating = False
                    return
                
                try:
                    # Convert Mermaid to DOT
                    dot_content = mermaid_to_dot(mermaid_text)
                    self.dot_text.setPlainText(dot_content)
                    
                    # Write DOT content to temp file for custom format conversion
                    with open(self.dot_file_path, 'w') as f:
                        f.write(dot_content)
                    
                    # Convert DOT to custom format
                    try:
                        import pygraphviz as pgv
                        import networkx as nx

                        graph = pgv.AGraph(self.dot_file_path)
                        nx_graph = nx.nx_agraph.from_agraph(graph)

                        components = list(nx.algorithms.components.weakly_connected_components(nx_graph))

                        component_structures = []
                        for component in components:
                            subgraph = nx_graph.subgraph(component)
                            component_struct = generate_component_structure(subgraph)
                            component_structures.append(component_struct)

                        if len(component_structures) > 1:
                            final_structure = {'type': 'Parallel', 'children': component_structures}
                        elif len(component_structures) == 1:
                            final_structure = component_structures[0]
                        else:
                            final_structure = None

                        if final_structure:
                            custom_content = format_structure(final_structure)
                            self.custom_text.setPlainText(custom_content)

                    except Exception as e:
                        self.show_error(f"Error converting Mermaid to custom format: {str(e)}")
                        traceback.print_exc()
                    
                    # Render the graph
                    self.render_graph(dot_content)
                    
                except Exception as e:
                    self.show_error(f"Error converting Mermaid format: {str(e)}")
                    traceback.print_exc()

        except Exception as e:
            self.show_error(f"Error syncing editors: {str(e)}")
            traceback.print_exc()

        finally:
            self.is_updating = False

    def render_graph(self, dot_content):
        """Render the DOT graph to an image"""
        try:
            # Write DOT content to the temporary file
            with open(self.dot_file_path, 'w') as f:
                f.write(dot_content)

            # Use Graphviz to render the image
            try:
                result = subprocess.run(
                    ["dot", "-Tpng", "-o", self.image_file_path, self.dot_file_path],
                    check=False,
                    capture_output=True
                )

                if result.returncode != 0:
                    error_msg = result.stderr.decode() if result.stderr else "Unknown error"
                    self.graph_content.setText(f"Error rendering graph:\n{error_msg}")
                    return

                # Load and display the image
                pixmap = QPixmap(self.image_file_path)
                if not pixmap.isNull():
                    self.graph_content.setPixmap(pixmap)
                else:
                    self.graph_content.setText("Failed to load rendered graph image")

            except FileNotFoundError:
                self.graph_content.setText("Graphviz 'dot' command not found.\n"
                                          "Please install Graphviz and make sure it's in your PATH.")
            except Exception as e:
                self.graph_content.setText(f"Error running Graphviz: {str(e)}")

        except Exception as e:
            self.graph_content.setText(f"Error preparing graph render: {str(e)}")

    def clear_graph(self):
        """Clear the graph display"""
        self.graph_content.clear()
        self.graph_content.setText("No graph to display")

    def show_error(self, message):
        """Display an error message in the status bar"""
        self.statusBar().showMessage(message, 5000)
        print(f"ERROR: {message}")

    def closeEvent(self, event):
        """Clean up resources when the application closes"""
        # Remove the temporary directory and its contents
        try:
            for file in os.listdir(self.temp_dir):
                try:
                    os.remove(os.path.join(self.temp_dir, file))
                except:
                    pass
            os.rmdir(self.temp_dir)
        except:
            pass
        super().closeEvent(event)

def main():
    # Check if graphviz is installed
    try:
        subprocess.run(["dot", "-V"], check=True, capture_output=True)
    except FileNotFoundError:
        print("Graphviz 'dot' command not found.")
        print("Please install Graphviz and make sure it's in your PATH.")
        print("On Linux: sudo apt-get install graphviz")
        print("On macOS: brew install graphviz")
        print("On Windows: Download from https://graphviz.org/download/")
        sys.exit(1)
    except Exception as e:
        print(f"Error checking for Graphviz: {e}")
        print("Continuing anyway, but graph rendering may not work.")

    app = QApplication(sys.argv)
    window = GraphConverterApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
