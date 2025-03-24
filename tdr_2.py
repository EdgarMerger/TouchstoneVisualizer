#https://electronics.stackexchange.com/questions/553060/frequency-domain-s11-conversion-to-time-domain-tdr

import sys
import skrf
import matplotlib.pyplot as plt
skrf.stylely()

network = skrf.Network("Striplines/stripline_30cm.s4p")
network_dc = network.extrapolate_to_dc(kind='linear')

plt.figure()
plt.title("Time Domain Reflectometry")
network_dc.s11.plot_z_time_step(window='hamming', label="impedance")
plt.xlim((-0.5, 10))

plt.tight_layout()
plt.show()
pass