'''This file is part of AeoLiS.
   
AeoLiS is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
   
AeoLiS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
   
You should have received a copy of the GNU General Public License
along with AeoLiS.  If not, see <http://www.gnu.org/licenses/>.
   
AeoLiS  Copyright (C) 2015 Bas Hoonhout

bas.hoonhout@deltares.nl         b.m.hoonhout@tudelft.nl
Deltares                         Delft University of Technology
Unit of Hydraulic Engineering    Faculty of Civil Engineering and Geosciences
Boussinesqweg 1                  Stevinweg 1
2629 HVDelft                     2628CN Delft
The Netherlands                  The Netherlands

'''


import numpy as np
import operator

# package modules
from utils import *


def interpolate(s, p, t):
    '''Interpolate wind velocity and direction to current time step

    Interpolates the wind time series for velocity and direction to
    the current time step. The cosine and sine of the direction angle
    are interpolated separately to prevent zero-crossing errors. The
    wind velocity is decomposed in two grid components based on the
    orientation of each individual grid cell. In case of a
    one-dimensional model only a single positive component is used.

    Parameters
    ----------
    s : dict
        Spatial grids
    p : dict
        Model configuration parameters
    t : float
        Current time

    Returns
    -------
    dict
        Spatial grids

    '''
        
    uw_t = p['wind_file'][:,0]
    uw_s = p['wind_file'][:,1]
    uw_d = p['wind_file'][:,2] / 180. * np.pi

    s['uw'][:,:] = interp_circular(t, uw_t, uw_s)
    s['udir'][:,:] = np.arctan2(np.interp(t, uw_t, np.sin(uw_d)),
                                np.interp(t, uw_t, np.cos(uw_d))) * 180. / np.pi

    s['uws'] = s['uw'] * np.cos(s['alfa'] + s['udir'] / 180. * np.pi)
    s['uwn'] = s['uw'] * np.sin(s['alfa'] + s['udir'] / 180. * np.pi)

    if p['ny'] == 0:
        s['uwn'][:,:] = 0.

    s['uw'] = np.abs(s['uw'])

    # compute saltation velocity
    s['uw'] = get_velocity_at_height(s['uw'], p['z'], p['k'], p['h'])
    s['uws'] = get_velocity_at_height(s['uws'], p['z'], p['k'], p['h'])
    s['uwn'] = get_velocity_at_height(s['uwn'], p['z'], p['k'], p['h'])

    # compute shear velocity
    s['tau'] = get_velocity_at_height(s['uw'], p['h'], p['k'])
    s['taus'] = get_velocity_at_height(s['uws'], p['h'], p['k'])
    s['taun'] = get_velocity_at_height(s['uwn'], p['h'], p['k'])

    return s


def get_velocity_at_height(u, z, z0, z1=None):
    '''Compute shear velocity from wind velocity following Prandl-Karman's Law of the Wall

    Parameters
    ----------
    u : numpy.ndarray
        Spatial wind field
    z : float
        Height above bed where ``u`` is measured
    z0 : float
        Roughness length
    z1 : float, optional
        Height above bed for which to return wind speeds.
        Returns wind shear if not given.

    Returns
    -------
    numpy.ndarray
        Array of size ``u`` with wind speeds at height ``z1``

    '''

    tau = .41 / np.log(z / z0) * u

    if z1 is None:
        return tau
    else:
        return tau * np.log(z1 / z0) / .41
