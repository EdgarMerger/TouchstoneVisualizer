# Touchstone Viewer

## Overview
The **Touchstone Viewer** is a GUI-based tool for visualizing S-parameter files (.s2p, .s4p) using **scikit-rf** and **PyQt6**. It allows users to:

- Load multiple Touchstone files simultaneously.
- Enable/disable specific files for plotting.
- Toggle between standard and mixed-mode S-parameters.
- Interactively resize the Matplotlib canvas.
- Export plotted data for further analysis.
- Generate an executable version for standalone use.

## Features
✅ Load multiple S-parameter files (.s2p, .s4p).  
✅ Enable/disable specific files using checkboxes.  
✅ Convert to Mixed-Mode (se2gmm) for 4-port networks.  
✅ Log-magnitude (dB) plots with frequency in GHz.  
✅ Interactive resizing of plots.  
✅ Standalone executable via PyInstaller.  

## Installation
### Prerequisites
Ensure you have **Python 3.13.2** installed.

### Install Dependencies
Run the following command to install required packages:
```sh
pip install numpy matplotlib pyqt6 scikit-rf
```

## Usage
### Run the Application
To start the Touchstone Viewer, execute:
```sh
python touchstone_viewer.py
```

### Load S-Parameter Files
1. Click **"Open File"** and select one or more `.s2p` or `.s4p` files.
2. Use the checkboxes to enable/disable specific files.
3. If applicable, check **"Enable Mixed-Mode"** for 4-port networks.

### Plot S-Parameters
1. Select desired S-parameters using checkboxes.
2. Click **"Plot S-Parameters"** to visualize the data.
3. Resize the plot interactively using the mouse.

![GUI](images/GUI.jpg)

### Create a Standalone Executable
To build an `.exe` file:
```sh
pyinstaller --onefile --windowed --name TouchstoneAnalyzer ./TouchstoneAnalyzer.py
```
This generates an executable in the `dist/` folder.

## Troubleshooting
- **PyInstaller not recognized?** Ensure it is installed:
  ```sh
  pip install pyinstaller
  ```
- **PyQt6-related errors?** Try reinstalling:
  ```sh
  pip install --force-reinstall pyqt6
  ```
- **Plot labels cut off?** Ensure the window is resized properly.

## License
This project is licensed under the MIT License.

## Author
Developed by Edgar Merger.

For issues or feature requests, feel free to contribute!

