'''

    Implementation file for coordinator and DER- and load-specific
    translators.

    Should be imported in the simulation file as

        from dercon import *

    The module's name 'dercon' stands for 'DER controllers'.

'''

def get_measurements(ram):
    ''' Receives simulation instance and other parameters and returns
        measurements that will then be used by coordinator. '''

    return 1

def coordinator(tk, measurements):
    ''' Receives current time and (possibly several) measurements.
        Outputs a list whose first element is a signal for P and
        whose second element is a signal for Q. These signals are
        then used by DERs and flexible loads in order to support
        the TN. '''

    # Determine signal value based on logic
    if 1 < tk:
        signal_P = 2
        signal_Q = 2
    else:
        signal_P = 1
        signal_Q = 1
    if 6 < tk:
        signal_P = 3
        signal_Q = 3
    if 11 < tk:
        signal_P = 4
        signal_Q = 4
    if 16 < tk:
        signal_P = 5
        signal_Q = 5

    # Wrap signals in a list
    signal = [signal_P, signal_Q]

    return signal

def translator_DERD(tk, signal, signal_prev, injectors, sat, ram):
    ''' Translates signal sent by coordinator into parameters ts and rho,
        used in the algorithm for controlling Q. The function sends the
        parameter changes directly to the injectors, and it only returns
        a boolean that tells if no parameters can be changed (sat). '''

    ''' When signal is 5, then move V1, V2, V3, V4 to the left and to the right
        so that they definitely listen to the coordinator. '''

    # Unpack signal (only Q matters)
    signal_Q = signal[1]
    signal_Q_prev = signal_prev[1]

    # Define parameters used in logic
    Tsmax = 25
    Tsmin = 5
    signal_Tsmin = 1
    signal_Tsmax = 2
    rhomin = 0
    rhomax = 0.2
    signal_rhomin = 1
    signal_rhomax = 3

    # If signal changed and asks for ancillary services
    if signal_Q != signal_Q_prev and (signal_Q < -1 or 1 < signal_Q):

        # Determine ts by interpolation
        if abs(signal_Q) < signal_Tsmin:
            ts = Tsmax
        elif signal_Tsmin < abs(signal_Q) and abs(signal_Q) < signal_Tsmax:
            ts = (Tsmin-Tsmax)*(abs(signal_Q) - signal_Tsmax) \
                 /(signal_Tsmax - signal_Tsmin) + Tsmin
        else:
            ts = Tsmin

        # Determine rho by interpolation as well
        if abs(signal_Q) < signal_rhomin:
            rho = rhomin
        elif signal_rhomin < abs(signal_Q) and abs(signal_Q) > signal_rhomax:
            rho = (rhomax-rhomin)*(abs(signal_Q) - signal_rhomax) \
                  /(signal_rhomax - signal_rhomin) + rhomax
        else:
            rho = rhomax

        # Determine direction of changes based on sign of signal
        if signal_Q < -1:
            coor = -1
        elif 1 < signal_Q:
            coor = 1

        # Make sure to de-saturate requests to DERs if required
        if abs(signal_Q) < signal_Tsmax or abs(signal_Q) < signal_rhomax:
            sat = False

        # If requests to DERs are not saturated
        if not sat:
            # For each injector
            for inj in injectors:
                # Send changes
                prefix = 'CHGPRM INJ ' + inj + ' '
                suffix = ' SETP 0.'
                ram.addDisturb(tk+0.01, prefix + 'tmuestreo ' + str(ts) + suffix)
                ram.addDisturb(tk+0.01, prefix + 'p ' + str(rho) + suffix)
                ram.addDisturb(tk+0.01, prefix + 'Coor ' + str(coor) + suffix)

        # Makes sure that DERs saturate
        if signal_Tsmax < abs(signal_Q) or signal_rhomax < abs(signal_Q):
            sat = True

    return sat

def translator_WH(tk, signal, signal_prev, injectors, sat, ram):
    ''' Translates signal sent by coordinator into parameters D2a
        and signal used in the duty-cycle control. The function sends the
        parameter changes directly to the injectors, and it only returns
        a boolean that tells if no parameters can be changed (sat). '''

    # Unpack signal (only P matters)
    signal_P = signal[0]
    signal_P_prev = signal_prev[0]

    # Define parameters used in logic (tolerance used to avoid equality
    # comparisons)
    signal_Dmax = 3
    signal_Dmin = 5
    Dmax = 0.8
    Dmin = 0.6
    tol = 1e-3

    # If signal changed and asks for ancillary services
    if signal_P != signal_P_prev and 1 < abs(signal_P):

        # Determine signal sent to WH (signal_WH)
        if signal_P < 3 - tol:
            signal_WH = 1
        elif 3 - tol < signal_P < 5 - tol:
            signal_WH = 2
        elif 5 - tol < signal_P:
            signal_WH = 5

        # Determine duty cycle
        if 3 - tol < signal_P < 3 + tol:
            D2a = Dmax
        elif 4 - tol < signal_P < 4 + tol:
            D2a = Dmin

        # Make sure to de-saturate requests to WHs if required
        if abs(signal_P) < signal_Dmin:
            sat = False

        # If requests to WHs are not saturated
        if not sat:
            # For each injector
            for inj in injectors:
                # Send changes
                prefix = 'CHGPRM INJ ' + inj + ' '
                suffix = ' SETP 0.'
                ram.addDisturb(tk+0.01,
                               prefix + 'signal ' + str(signal_WH) + suffix)
                # If signal is three or four
                if signal_WH == 2:
                    # Also send duty cycle
                    ram.addDisturb(tk+0.01, prefix + 'D2a ' + str(D2a) + suffix)

        # Make sure that WHs saturate
        if signal_Dmin < signal_P:
            sat = True

    return sat

def translator_AC(tk, signal, signal_prev, injectors, sat, ram):
    ''' Translates signal sent by coordinator into parameter ffrac
    and signal used in the duty-cycle control. The function sends the
    parameter changes directly to the injectors, and it only returns
    a boolean that tells if no parameters can be changed (sat). '''

    # Unpack signal (only P matters)
    signal_P = signal[0]
    signal_P_prev = signal_prev[0]

    # Define parameters used in logic (tolerance used to avoid equality
    # comparisons)
    signal_Dmax = 3
    signal_Dmin = 5
    tol = 1e-3

    # If signal changed and asks for ancillary services
    if signal_P != signal_P_prev:

        # Determine signal sent to AC (signal_AC). If signal_AC is 1 or 3, ffrac
        # is not required
        if 1 - tol < signal_P < 1 + tol:
                    signal_AC = 1
        if 2 - tol < signal_P < 2 + tol:
                    signal_AC = 2
                    ffrac = 0.25
        if 3 - tol < signal_P < 3 + tol:
                    signal_AC = 2
                    ffrac = 0.50
        if 4 - tol < signal_P < 4 + tol:
                    signal_AC = 2
                    ffrac = 0.75
        if 5 - tol < signal_P < 5 + tol:
                    signal_AC = 3

        # Make sure to de-saturate requests to ACs if required
        if abs(signal_P) < signal_Dmin:
            sat = False

        # If requests to ACs are not saturated
        if not sat:
            # For each injector
            for inj in injectors:
                # First change signal to 1
                prefix = 'CHGPRM INJ ' + inj + ' '
                suffix = ' SETP 0.'
                ram.addDisturb(tk+0.005,
                               prefix + 'signal 1.0' + suffix)
            # For each injector
            for inj in injectors:
                # Send changes
                prefix = 'CHGPRM INJ ' + inj + ' '
                suffix = ' SETP 0.'
                ram.addDisturb(tk+0.01,
                               prefix + 'signal ' + str(signal_AC) + suffix)
                # If signal is two
                if  2 - tol < signal_AC < 2 + tol:
                    # Send also change in ffrac
                    ram.addDisturb(tk+0.01,
                                   prefix + 'ffrac ' + str(ffrac) + suffix)

        # Make sure that WHs saturate
        if signal_Dmin < signal_P:
            sat = True

    return sat
