'''

    File for extracting observables.

'''

import pyramses
import numpy as np
import matplotlib.pyplot as plt
from pyramses import simulator
simulator.new__libdir__ = \
                    'C:\\Users\\Francisco\\Desktop\\URAMSES\\Release_intel_w64'

# Create case
case = pyramses.cfg()

# Specify input files
case.addData('input/syst.dat')
case.addData('input/volt.dat')
case.addData('input/settings.dat')
case.addData('../System resizing/output/mvlodis/mv.dat')
case.addData('../System resizing/output/mvlodis_lv/lv.dat')
case.addObs('input/obs.dat')
case.addDst('input/disturbance.dst')

# Specify output files
case.addOut('output/output-temp.trace')
case.addTrj('output/obs-temp.trj')

# Create simulator instance
ram = pyramses.sim()

# Initialize simulation
ram.execSim(case, 0.05)

# Get injector names
INJ_names = ram.getAllCompNames('INJ')
DERD_abb = ['PV', 'BATD', 'BATC']
DERD_names = [inj for inj in INJ_names if any(name in inj for name in DERD_abb)
              and not 'RL' in inj]
AC_names = [inj for inj in INJ_names if 'AC2' in inj]
WH_names = [inj for inj in INJ_names if 'WH' in inj]

# Finish simulation at t=0
ram.endSim()

# Extract variables
ext = pyramses.extractor('output/obs-temp.trj')

# Plot reactive power of batteries and PVs
plt.figure()
for DERD in DERD_names:
    # Extract data
    data = ext.getInj(DERD).trandom
    # Add to plot
    plt.plot(data[0], data[1])

plt.title('Random offset time')
plt.show()
