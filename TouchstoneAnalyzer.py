import sys
import skrf as rf
import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QPushButton, QLabel, 
    QVBoxLayout, QWidget, QCheckBox, QScrollArea, QSizePolicy
)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)

class TouchstoneViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Touchstone Viewer")
        self.setGeometry(100, 100, 900, 700)

        # UI Elements
        self.label = QLabel("Load Touchstone Files:", self)
        self.load_button = QPushButton("Open Files", self)
        self.plot_button = QPushButton("Plot S-Parameters", self)
        self.mode_checkbox = QCheckBox("Enable Mixed-Mode", self)

        # Scrollable area for file selection checkboxes
        self.file_container = QWidget()
        self.file_layout = QVBoxLayout(self.file_container)
        self.file_scroll_area = QScrollArea()
        self.file_scroll_area.setWidgetResizable(True)
        self.file_scroll_area.setWidget(self.file_container)

        # Scrollable area for S-Parameter checkboxes
        self.param_container = QWidget()
        self.param_layout = QVBoxLayout(self.param_container)
        self.param_scroll_area = QScrollArea()
        self.param_scroll_area.setWidgetResizable(True)
        self.param_scroll_area.setWidget(self.param_container)

        # Matplotlib Canvas & Toolbar
        self.figure, (self.ax_mag, self.ax_phase) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Make the canvas resizable
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.updateGeometry()

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.load_button)
        layout.addWidget(self.file_scroll_area)
        layout.addWidget(self.mode_checkbox)
        layout.addWidget(self.param_scroll_area)
        layout.addWidget(self.plot_button)
        layout.addWidget(self.toolbar)  # Add Matplotlib Toolbar
        layout.addWidget(self.canvas)   # Add resizable canvas

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Connections
        self.load_button.clicked.connect(self.load_files)
        self.plot_button.clicked.connect(self.plot_s_param)
        self.mode_checkbox.stateChanged.connect(self.update_param_checkboxes)

        self.networks = {}  # Store multiple networks {file_name: Network}
        self.mixed_mode_networks = {}  # Store Mixed-Mode networks
        self.file_checkboxes = {}  # Store checkboxes for files
        self.s_param_checkboxes = {}  # Store checkboxes for S-parameters

    def load_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Touchstone Files", "", "Touchstone Files (*.s2p *.s4p)")
        if not file_paths:
            return  # No files selected

        for file_path in file_paths:
            if file_path in self.networks:
                continue  # Avoid duplicate entries

            network = rf.Network(file_path)
            self.networks[file_path] = network

            # Create checkbox for file
            file_checkbox = QCheckBox(file_path.split('/')[-1])
            file_checkbox.setChecked(True)  # Enable by default
            file_checkbox.stateChanged.connect(self.update_param_checkboxes)
            self.file_layout.addWidget(file_checkbox)
            self.file_checkboxes[file_path] = file_checkbox

        self.update_param_checkboxes()  # Update available S-parameters

    def update_param_checkboxes(self):
        """ Updates the checkbox list with available S-parameters based on enabled files and mode. """
        # Clear old S-parameter checkboxes
        for checkbox in self.s_param_checkboxes.values():
            checkbox.setParent(None)
        self.s_param_checkboxes.clear()

        enabled_files = [f for f, cb in self.file_checkboxes.items() if cb.isChecked()]
        if not enabled_files:
            return

        # Collect unique S-parameters across all selected files
        first_network = self.networks[enabled_files[0]]
        num_ports = first_network.number_of_ports

        if self.mode_checkbox.isChecked() and num_ports == 4:
            params = ["S_dd11", "S_dd21", "S_cc11", "S_cc21", "S_dc11", "S_dc21"]
        else:
            params = [f"S{i+1}{j+1}" for i in range(num_ports) for j in range(num_ports)]

        for param in params:
            checkbox = QCheckBox(param)
            checkbox.setChecked(False)  # Default to unchecked
            self.param_layout.addWidget(checkbox)
            self.s_param_checkboxes[param] = checkbox

    def plot_s_param(self):
        enabled_files = [f for f, cb in self.file_checkboxes.items() if cb.isChecked()]
        selected_params = [p for p, cb in self.s_param_checkboxes.items() if cb.isChecked()]

        if not enabled_files:
            self.label.setText("Please enable at least one file!")
            return
        if not selected_params:
            self.label.setText("Please select at least one S-Parameter!")
            return

        self.ax_mag.clear()
        self.ax_phase.clear()

        for file_path in enabled_files:
            network = self.networks[file_path]
            freqs = network.f / 1e9  # Convert Hz to GHz
            label_prefix = file_path.split('/')[-1]  # File name for legend

            for param in selected_params:
                if self.mode_checkbox.isChecked() and network.number_of_ports == 4:
                    # Mixed-Mode Conversion
                    if file_path not in self.mixed_mode_networks:
                        mixed_mode_network = rf.Network(file_path)
                        mixed_mode_network.se2gmm(p=2)
                        self.mixed_mode_networks[file_path] = mixed_mode_network

                    mm_map = {
                        "S_dd11": (0, 0), "S_dd21": (1, 0),
                        "S_cc11": (2, 2), "S_cc21": (3, 2),
                        "S_dc11": (2, 0), "S_dc21": (3, 0),
                    }
                    i, j = mm_map[param]
                    s_param_mag = 20 * np.log10(abs(self.mixed_mode_networks[file_path].s[:, i, j]))
                    s_param_phase = np.angle(self.mixed_mode_networks[file_path].s[:, i, j], deg=True)
                else:
                    # Normal S-parameters
                    i, j = int(param[1]) - 1, int(param[2]) - 1
                    s_param_mag = 20 * np.log10(abs(network.s[:, i, j]))
                    s_param_phase = np.angle(network.s[:, i, j], deg=True)

                self.ax_mag.plot(freqs, s_param_mag, label=f"{label_prefix} |{param}|")
                self.ax_phase.plot(freqs, s_param_phase, label=f"{label_prefix} ∠{param}")

        # Update plots
        self.ax_mag.set_ylabel("Magnitude (dB)")
        self.ax_mag.set_title("S-Parameter Magnitude")
        self.ax_mag.legend()
        self.ax_mag.grid()

        self.ax_phase.set_xlabel("Frequency (GHz)")
        self.ax_phase.set_ylabel("Phase (degrees)")
        self.ax_phase.set_title("S-Parameter Phase")
        self.ax_phase.legend()
        self.ax_phase.grid()

        self.canvas.draw()

# Run the Application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = TouchstoneViewer()
    viewer.show()
    sys.exit(app.exec())
