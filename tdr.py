import skrf as rf
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import windows

# Load Touchstone file (Replace 'your_file.s4p' with your actual filename)
ntwk = rf.Network("Striplines/stripline_30cm.s4p")

# Extract frequency vector (in Hz)
freq = ntwk.f

# Extract S11 (reflection coefficient of port 1)
S11 = ntwk.s[:, 0, 0]  # First port's reflection coefficient

# plot frequency and time-domain s-parameters
#figure(figsize=(8,4))
#subplot(121)
ntwk.plot_s_db(m=0, n=0, color='r' )
ntwk.plot_s_db_time(m=0, n=0, color='r' )
#title('Frequency Domain')

#subplot(122)
#S11.plot_s_db_time()
#s22_gated.plot_s_db_time()
#title('Time Domain')
#tight_layout()

plt.show()

# Apply a window function (Hanning or Kaiser) to reduce FFT artifacts
window = windows.kaiser(len(S11), beta=6)  # Kaiser window
S11_windowed = S11 * window

# Zero-padding for better time resolution
N = 2**14  # Power of 2 for efficient FFT
S11_padded = np.zeros(N, dtype=complex)
S11_padded[:len(S11)] = S11_windowed

# Compute IFFT to get TDR response
tdr_response = np.fft.ifft(S11_padded)
tdr_response = np.abs(tdr_response)  # Take magnitude for analysis

# Compute time vector
df = freq[1] - freq[0]  # Frequency step
time = np.fft.fftfreq(N, d=df) * 1e9  # Convert to nanoseconds (ns)

# Compute impedance profile assuming Z0 = 50 Ohms
Z0 = 50
tdr_impedance = Z0 * (1 + np.abs(tdr_response)) / (1 - np.abs(tdr_response))

# Plot TDR response
plt.figure(figsize=(8, 5))
plt.plot(time[:N//2], tdr_impedance[:N//2], label="Impedance Profile")
plt.xlabel("Time (ns)")
plt.ylabel("Impedance (Ohms)")
plt.title("TDR Impedance Profile (Open Ports 2, 3, 4)")
plt.grid()
plt.legend()
plt.show()
