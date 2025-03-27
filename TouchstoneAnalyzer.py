import sys
import skrf as rf
import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QPushButton, QLabel, 
    QVBoxLayout, QWidget, QCheckBox, QScrollArea, QSizePolicy, QTextEdit
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
        self.time_plot_button = QPushButton("Plot TDR (beta)", self)
        self.mode_checkbox = QCheckBox("Enable Mixed-Mode", self)
        self.check_passivity_button = QPushButton("Run Passivity Check", self)
        self.check_causality_button = QPushButton("Run Causality Check", self)
        self.check_reciprocity_button = QPushButton("Run Reciprocity Check", self)
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)

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
        self.figure, (self.ax_mag, self.ax_phase, self.ax_tdr) = plt.subplots(3, 1, figsize=(8, 8), sharex=False)

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
        layout.addWidget(self.time_plot_button)
        layout.addWidget(self.check_passivity_button)
        layout.addWidget(self.check_causality_button)
        layout.addWidget(self.check_reciprocity_button)
        layout.addWidget(self.results_display)
        layout.addWidget(self.toolbar)  # Add Matplotlib Toolbar
        layout.addWidget(self.canvas)   # Add resizable canvas

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Connections
        self.load_button.clicked.connect(self.load_files)
        self.plot_button.clicked.connect(self.plot_s_param)
        self.time_plot_button.clicked.connect(self.plot_tdr)  # New Function
        self.mode_checkbox.stateChanged.connect(self.update_param_checkboxes)
        self.check_passivity_button.clicked.connect(self.run_passivity_check)
        self.check_causality_button.clicked.connect(self.run_causality_check)
        self.check_reciprocity_button.clicked.connect(self.run_reciprocity_check)

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
        
        # Unhide phase plot since it's again needed for S-Parameters
        self.ax_phase.set_visible(True)

        self.ax_phase.set_xlabel("Frequency (GHz)")
        self.ax_phase.set_ylabel("Phase (degrees)")
        self.ax_phase.set_title("S-Parameter Phase")
        self.ax_phase.legend()
        self.ax_phase.grid()

        self.canvas.draw()


    def plot_tdr(self):
        enabled_files = [f for f, cb in self.file_checkboxes.items() if cb.isChecked()]
        if not enabled_files:
            self.label.setText("Select at least one file!")
            return

        mixed_mode_enabled = self.mode_checkbox.isChecked()

        # Clear only the TDR axis to keep S-parameter plots intact
        self.ax_tdr.clear()
        
        self.ax_tdr.set_title("Time Domain Reflectometry (TDR)")
        self.ax_tdr.set_xlabel("Time (ns)")
        self.ax_tdr.set_ylabel("Impedance (Ω)")
        self.ax_tdr.grid()

        for file_path in enabled_files:
            network = self.networks[file_path]

            if mixed_mode_enabled and network.number_of_ports == 4:
                if file_path not in self.mixed_mode_networks:
                    mixed_mode_network = rf.Network(file_path)
                    mixed_mode_network.se2gmm(p=2)  # Convert to Mixed-Mode
                    self.mixed_mode_networks[file_path] = mixed_mode_network
                else:
                    mixed_mode_network = self.mixed_mode_networks[file_path]

                selected_modes = {"S_dd11": mixed_mode_network.s11, "S_cc11": mixed_mode_network.s33}
                mixed_mode_network_dc = mixed_mode_network.extrapolate_to_dc(kind='linear')
                plt.title("Time Domain Reflectometry Mixed-Mode")
                mixed_mode_network_dc.s11.plot_z_time_step(ax = self.ax_tdr, window='hamming', label="impedance "+ file_path.split('/')[-1])
                plt.xlim((-1, 20))
            else:
                selected_modes = {"S11": network.s11}
                # Extrapolate to DC for a more realistic TDR response
                network_dc = network.extrapolate_to_dc(kind='linear')
                network_dc.s11.plot_z_time_step(ax = self.ax_tdr, window='hamming', label="impedance "+ file_path.split('/')[-1])
        
        self.canvas.draw() 

    def run_passivity_check(self):
        result = "Passivity Result:\n"
        
        for file_path, network in self.networks.items():
            if not self.file_checkboxes[file_path].isChecked():
                continue

            passivity = True  # Assume the network is passive initially

            for f_idx in range(network.f.shape[0]):  # Iterate over each frequency
                s_matrix = network.s[f_idx, :, :]  # Extract S-matrix at this frequency
                power_matrix = s_matrix @ s_matrix.conj().T  # Compute P = S * S^H
                eigenvalues = np.linalg.eigvals(power_matrix)  # Get eigenvalues

            if np.any(eigenvalues > 1):  # If any eigenvalue > 1, passivity is violated
                passivity = False
                print(f"Warning: Network is not passive at {network.f[f_idx] / 1e9:.2f} GHz")
                break  # No need to check further if passivity is already violated


            #reciprocity = np.allclose(network.s, network.s.T, atol=1e-6)
            #causality = np.all(np.diff(np.angle(network.s), axis=0) >= 0)
            
            result += f"{file_path.split('/')[-1]}:\n"
            result += f"  Passivity: {'✅ PASS' if passivity else '❌ FAIL'}\n"
            
        self.results_display.setText(result)

    def run_causality_check(self):
        result = "Causality Result:\n"
        
        for file_path, network in self.networks.items():
            if not self.file_checkboxes[file_path].isChecked():
                continue    
           
            causality = True  # Assume the network is reciprocal initially
            s_matrix = network.s
            s_time = np.fft.ifft(s_matrix, axis=0)
            causality = np.all(np.real(s_time[0]) >= 0)

            result += f"{file_path.split('/')[-1]}:\n"            
            result += f"Causality: {'✅ Pass' if causality else '❌ Fail'}\n"
            
        self.results_display.setText(result)

    @staticmethod
    def abs_diff(a, b):
        """
        Computes the absolute difference between two arrays.

        Parameters:
            a, b : array-like
                Input arrays to compare.

        Returns:
            diff : ndarray
                The computed absolute differences.
        """
        return np.abs(a - b)

    def run_reciprocity_check(self):
        result = "Reciprocity Result:\n"
        
        for file_path, network in self.networks.items():
            if not self.file_checkboxes[file_path].isChecked():
                continue    
            
            result += f"{file_path.split('/')[-1]}:\n"

            reciprocity = True  # Assume the network is reciprocal initially
            tolerance = 1e-2   # Small numerical tolerance for floating-point errors

            for f_idx in range(network.f.shape[0]):  # Iterate over all frequencies
                s_matrix = network.s[f_idx, :, :]  # Extract S-matrix at this frequency

                if not np.allclose(s_matrix, s_matrix.T, atol=tolerance):  # Check symmetry
                    reciprocity = False
                    print(f"Warning: Network is not reciprocal at {network.f[f_idx] / 1e9:.2f} GHz")
                    diff = self.abs_diff(s_matrix, s_matrix.T)
                    result += f"Warning: Network is not reciprocal at {network.f[f_idx] / 1e9:.2f} GHz\n"
                    result += f"The difference in S-Parameter Matrix is as follows:\n"
                    result += f"{diff}\n\n"

            result += f"  Reciprocity: {'✅ PASS' if reciprocity else '❌ FAIL'}\n\n"
            
        self.results_display.setText(result)

# Run the Application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = TouchstoneViewer()
    viewer.show()
    sys.exit(app.exec())
