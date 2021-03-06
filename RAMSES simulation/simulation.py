'''

    Main simulation file for paper sent to Hawaii. Run it from a command
    prompt as

        python simulation.py

    These simulations show the effect of changing active and reactive
    power consumed or produced by DERs on the overall stability of a
    power system. A re-scaled version of Van Cutsem's four-bus system
    is used as testbed.

    Comments on this simulation:

    -

    -

'''

import pyramses
import numpy as np
import matplotlib.pyplot as plt
from dercon import *
from pyramses import simulator
simulator.new__libdir__ = \
                    'D:\Francisco Escobar\RAMSES executable'

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
case.addInit('output/init.trace')
case.addOut('output/output.trace')
case.addTrj('output/obs.trj')
# case.addCont('output/cont.trace')
# case.addDisc('output/disc.trace')

# Specify runtime observables
case.addRunObs('BV 4a2')
case.addRunObs('BV 4')

# Create simulator instance
ram = pyramses.sim()

# Initialize simulation
ram.execSim(case, 0)

# Get injector names
INJ_names = ram.getAllCompNames('INJ')
DERD_abb = ['PV', 'BATD', 'BATC']
DERD_names = [inj for inj in INJ_names if any(name in inj for name in DERD_abb)
              and not 'RL' in inj]
AC_names = [inj for inj in INJ_names if 'AC2' in inj]
WH_names = [inj for inj in INJ_names if 'WH' in inj]

# Define simulation parameters
thorizon = 100
tsample = 1

# Initialize variables
DERDsSat = False
WHsSat = False
ACsSat = False
signal = [1, 1]

# Run simulation
for tk in np.arange(0.0, thorizon + tsample, tsample):

    # Simulate until the next sampling point
    try:
        ram.contSim(tk)
    # If there is an error
    except:
        # Print the error and exit the loop
        print(ram.getLastErr())
        break

    # Store previous signal
    prev_signal = signal

    # Get measurements
    measurements = get_measurements(ram)

    # Get signal from coordinator
    signal = coordinator(tk, measurements)

    # Send signal to injectors and determine if no more requests are possible
    # (DERs are said to be saturated)
    DERDsSat = translator_DERD(tk, signal, prev_signal, DERD_names, DERDsSat,
                               ram)
    ACsSat = translator_AC(tk, signal, prev_signal, AC_names, ACsSat, ram)
    WHsSat = translator_WH(tk, signal, prev_signal, WH_names, WHsSat, ram)

# Finish simulation at thorizon
ram.endSim()

# Extract variables
ext = pyramses.extractor(case.getTrj())

# Plot power and reactive power supplied at the feeder
plt.figure()
P = ext.getBranch('T4a3-Aa').PF
Q = ext.getBranch('T4a3-Aa').QF
plt.plot(P[0], P[1])
plt.plot(Q[0], Q[1])
plt.title('P and Q supplied by MV-LV transformer (kW and kvar)')
plt.show()

# Plot reactive power of batteries and PVs
plt.figure()
for DERD in DERD_names:
    # Extract data
    data = ext.getInj(DERD).Qgen
    # Add to plot
    plt.plot(data[0], data[1])

plt.title('Q generated by DERDs')
plt.show()

# Plot active power of AC2
plt.figure()
for AC in AC_names:
    # Extract data
    data = ext.getInj(AC).Pdisp
    # Add to plot
    plt.plot(data[0], data[1])

plt.title('P consumed by ACs')
plt.show()

# Plot active power of WH
plt.figure()
for WH in WH_names:
    # Extract data
    data = ext.getInj(WH).P
    # Add to plot
    plt.plot(data[0], data[1])

plt.title('P consumed by WHs')
plt.show()
