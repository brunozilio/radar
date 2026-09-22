
import numpy as np

def rainfall_runoff(state, calib_parameters, P, PET, area, dt):
    '''
    --------------------------------------------------------------------------
    A simple water balance and routing model. 
    
    *Surface runoff generation is based on the ARNO model (Todini, 1996)
    *Surface runoff propagation uses cascading 'n' linear reservoirs    
    
    Original FORTRAN / Matlab code: Rodrigo Paiva and Walter Collischonn, 4/2016
    Python adaptations: Vinícius A. Siqueira, 6/2025
    --------------------------------------------------------------------------

    Parameters:
    
    state: numpy array 
        Array vector with the following state variables:
  
        state(i)

        0 = Current soil storage - W (mm)

        1 = Current groundwater storage - Vbas (mm)

        2:2+n = Current storage in each cascading linear reservoirs Vsup(n) (mm)

        3+n = Streamflow (m³/s)
    
    calib_parameters: dictionary 
        Must include the following calibrated parameters:       
       
        Wm =    Maximum soil water capacity (mm)
        
        b  =    Parameter of the ARNO model
        
        kbas =  Aquifer percolation rate (mm/day) 
        
        n =     Number of cascading linear reservoirs 
        
        k =     Recession coefficient for surface (cascading) reservoirs (hours)

        CB =    Recession coefficient for groundwater reservoir (days)

        Ws =    Soil moisture fraction limit to start reducing ET (-)
       
    P: float
        Precipitation for current time step (mm)    
    
    PET: float 
        Potential evapotranspiration for current time step (mm)
    
    dt: float
        Simulation time_step (in seconds)   
    
    area: float 
        Catchment drainage area (km²)

    --------------------------------------------------------------------------
    Returns: 
        
    '''
    #--------------------------------------------------------------------------
    #   Description of local variables:
    # ET = Actual evapotranspiration (mm)
    # Qsup = Propagated surface runoff (mm/dt)
    # Qbas = Groundwater flow (mm/dt)
    # Dbas = Percolation (mm/dt)
    # Dsup = Surface runoff (mm/dt)
    #--------------------------------------------------------------------------
      
    # Get parameters:
    Wm = calib_parameters['Wm']
    b = calib_parameters['b']
    kbas = calib_parameters['kbas']
    n = calib_parameters['n']
    k = calib_parameters['k']
    CB = calib_parameters['CB']
    Ws = calib_parameters['Ws']

    CB = CB * 86400./dt # From days to dt.
    k = k * 3600./dt # From hours to dt.
    kbas = kbas * dt/(86400.) # to mm/dt
    
    # Initializing state variables:
    W = state[0]
    Vbas = state[1]
    Vsup = state[2:2+n]
    Q = state[-1]
    
    # Computing actual evapotranspiration:
    ET = PET * min(1.0, W/(Wm*Ws))
    
    # Computing surface runoff using the ARNO model (Todini, 1996):
    xx = (1 - W/Wm)**(1/(b+1)) - P/((b+1)*Wm)
    if xx <= 0:
        Dsup = P - (Wm-W)
    else:
        Dsup = P - (Wm-W) + Wm * xx**(b+1)
    
    # Avoid negative values
    Dsup = max(Dsup, 0.0)
    
    # Computing percolation to groundwater:
    Dbas = kbas * W/Wm
    
    # Computing soil water balance:
    W = W + P - ET - Dsup - Dbas 
    
    # Ensure that water does not exceed maximum capacity 
    if W > Wm:
        excess = W - Wm
        Dsup = Dsup + excess
        W = Wm  
    elif W < 0:
        W = 0.0        
    
    # Computing baseflow:
    Vbas = Vbas + Dbas
    Qbas = Vbas / CB
    
    # Updates the groundwater volume:
    Vbas = Vbas - Qbas
    
    # Computes surface runoff 
    Qsup = Dsup

    # Propagates runoff in a cascading of linear reservoirs:
    for i in range(0,n):
        Vsup[i] = Vsup[i] + Qsup
        Qsup = Vsup[i] / k
        Vsup[i] = Vsup[i] - Qsup
    
    # Computing total streamflow in m³/s: 
    Q = (Qsup + Qbas) * area * (1000.)/dt
    
    # Save updated state variables
    updated_state = np.zeros(state.size)
    updated_state[0] = W
    updated_state[1] = Vbas
    updated_state[2:2+n] = Vsup
    updated_state[-1] = Q
    
    return updated_state


def run_model(initial_state, p_series, pet_series, calib_parameters, model_setup):
    '''
    --------------------------------------------------------------------------
    Perform model computations at each time step 
    --------------------------------------------------------------------------

    Parameters:
    
        initial_state: numpy array
            A vector containing the initial hydrological conditions (
        
        p_series: numpy array
            A vector with precipitation time series
        
        pet_series: numpy array
            A vector with potential evapotranspiration time series
                        
        calib_parameters: dictionary
            Dictionary that contains values of calibrated parameters     
        
        model_setup: dictionary
            Dictionary that contains values for model setup

    --------------------------------------------------------------------------
    Returns:

        states: numpy array
            A matrix containing the hydrological states for each time step (rows) and variable (columns)
     
    '''
    dt = model_setup['dt']
    area = model_setup['area']

    # total number of time steps:
    nt = p_series.size

    # Initializing state vector
    states = np.zeros((nt, initial_state.size))

    # Loop through time steps
    for t in range(0, nt):

        if t==0:
          curr_state = initial_state
        else:
          curr_state = states[t-1,:]

        # Computes catchment states for the next time step
        states[t,:] = rainfall_runoff(curr_state, calib_parameters,
                                            p_series[t], pet_series[t],
                                            area, dt)
    return states


def generate_ic(q_specific, n_casc_reservoirs, Wm, CB, area):
    '''
    Function to generate (arbitrary) initial conditions 

    --------------------------------------------------------------------------
    Parameters:
    
    q_specific:: float
        Average specific catchment discharge (L/s.km²)     
        
    n_casc_reservoirs: int
       Number of cascading reservoirs for surface runoff
        
    Wm: float
       Maximum water storage capacity
        
    CB: float
       Recession coefficient for groundwater reservoir (days)    
        
    area: float
       Catchment area (km²)

    --------------------------------------------------------------------------
    Returns:
    
    in_state: numpy array
        A vector containing the initial hydrological conditions    
    
    '''
    # 50 % of maximum water storage capacity
    w_start = 0.5 * Wm   
    # Initial flow is the catchment specific discharge
    q_start = (area * q_specific / 1000.)
    # Initialize reservoir volumes
    vbas_start = q_start * CB * 0.0864     
    vsup_start = np.zeros(n_casc_reservoirs)    

    # Concatenate variables -> array vector
    in_state = np.array([w_start, vbas_start])
    in_state = np.insert(in_state, in_state.size, vsup_start)
    in_state = np.insert(in_state, in_state.size, q_start)

    return in_state


