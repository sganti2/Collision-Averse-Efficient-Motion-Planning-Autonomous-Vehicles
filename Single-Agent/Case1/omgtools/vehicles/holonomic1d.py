# This file is part of OMG-tools.
#
# OMG-tools -- Optimal Motion Generation-tools
# Copyright (C) 2016 Ruben Van Parys & Tim Mercy, KU Leuven.
# All rights reserved.
#
# OMG-tools is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from .vehicle import Vehicle
from ..basics.shape import Rectangle
from ..basics.spline_extra import sample_splines
from casadi import inf
import numpy as np


class Holonomic1D(Vehicle):

    def __init__(self, width=0.7, height=0.1, options=None, bounds=None):
        bounds = bounds or {}
        Vehicle.__init__(self, n_spl=1, degree=3, shapes=Rectangle(width, height), options=options)
        self.vmin = bounds['vmin'] if 'vmin' in bounds else -0.5
        self.vmax = bounds['vmax'] if 'vmax' in bounds else 0.5
        self.amin = bounds['amin'] if 'amin' in bounds else -1.
        self.amax = bounds['amax'] if 'amax' in bounds else 1.

    def init(self):
        pass

    def define_trajectory_constraints(self, splines, horizon_time=None):
        if horizon_time is None:
            horizon_time = self.define_symbol('T')  # motion time
        x = splines[0]
        dx, ddx = x.derivative(), x.derivative(2)
        self.define_constraint(-dx + horizon_time*self.vmin, -inf, 0.)
        self.define_constraint(dx - horizon_time*self.vmax, -inf, 0.)
        self.define_constraint(-ddx + (horizon_time**2)*self.amin, -inf, 0.)
        self.define_constraint(ddx - (horizon_time**2)*self.amax, -inf, 0.)

    def get_initial_constraints(self, splines, horizon_time=None):
        if horizon_time is None:
            horizon_time = self.define_symbol('T')  # motion time
        state0 = self.define_parameter('state0')
        input0 = self.define_parameter('input0')
        x, dx = splines[0], splines[0].derivative()
        return [(x, state0[0]), (dx, horizon_time*input0[0])]

    def get_terminal_constraints(self, splines, horizon_time=None):
        position = self.define_parameter('poseT')
        x = splines[0]
        term_con = [(x, position[0])]
        term_con_der = []
        for d in range(1, self.degree+1):
            term_con_der.extend([(x.derivative(d), 0.)])
        return [term_con, term_con_der]

    def set_initial_conditions(self, state, input=None):
        if input is None:
            input = 0.
        # list all predictions that are used in set_parameters
        self.prediction['state'] = state
        self.prediction['input'] = input

    def set_terminal_conditions(self, position):
        self.poseT = position

    def get_init_spline_value(self):
        pos0 = self.prediction['state'][0]
        posT = self.poseT[0]
        # init_value = np.r_[pos0[0]*np.ones(self.degree), np.linspace(pos0[0], posT[0], len(self.basis) - 2*self.degree), posT[0]*np.ones(self.degree)]
        init_value = np.linspace(pos0, posT, len(self.basis))
        init_value = [init_value]
        return init_value

    def check_terminal_conditions(self):
        tol = self.options['stop_tol']
        if (np.linalg.norm(self.signals['state'][:, -1] - self.poseT) > tol or
                np.linalg.norm(self.signals['input'][:, -1])) > tol:
            return False
        else:
            return True

    def set_parameters(self, current_time):
        parameters = Vehicle.set_parameters(self, current_time)
        parameters[self]['state0'] = self.prediction['state']
        parameters[self]['input0'] = self.prediction['input']
        parameters[self]['poseT'] = self.poseT
        return parameters

    def define_collision_constraints(self, hyperplanes, environment, splines, horizon_time=None):
        pass

    def splines2signals(self, splines, time):
        signals = {}
        x = splines[0]
        dx, ddx = x.derivative(), x.derivative(2)
        signals['state'] = np.c_[sample_splines(x, time)].T
        signals['input'] = np.c_[sample_splines(dx, time)].T
        signals['a'] = np.c_[sample_splines(ddx, time)].T
        return signals

    def state2pose(self, state):
        return np.r_[state, np.zeros(2)]

    def ode(self, state, input):
        return input
