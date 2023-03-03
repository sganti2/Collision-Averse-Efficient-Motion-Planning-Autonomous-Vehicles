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
from ..basics.shape import Sphere
from ..basics.spline_extra import sample_splines
from casadi import inf
import numpy as np

# Vehicle model:
# ddx = (F/m)*cos(phi)*sin(theta)
# ddy = -(F/m)*sin(theta)
# ddz = (F/m)*cos(phi)*cos(theta) - g
# dphi = omega_phi
# dtheta = omega_theta

# Vehicle inputs
# u1 = F/m
# u2 = omega_phi
# u3 = omega_theta

# Output trajectory
# y1 = x
# y2 = y
# y3 = z


class SimpleQuadrotor3D(Vehicle):

    def __init__(self, radius=0.2, options=None, bounds=None):
        bounds = bounds or {}
        Vehicle.__init__(
            self, n_spl=3, degree=4, shapes=Sphere(radius), options=options)

        self.u1min = bounds['u1min'] if 'u1min' in bounds else 2.
        self.u1max = bounds['u1max'] if 'u1max' in bounds else 15.
        self.u2min = bounds['u2min'] if 'u2min' in bounds else -2.
        self.u2max = bounds['u2max'] if 'u2max' in bounds else 2.
        self.u3min = bounds['u3min'] if 'u3min' in bounds else -2.
        self.u3max = bounds['u3max'] if 'u3max' in bounds else 2.
        self.phimin = bounds['phimin'] if 'phimin' in bounds else -np.pi/6
        self.phimax = bounds['phimax'] if 'phimax' in bounds else np.pi/6
        self.thetamin = bounds['thetamin'] if 'thetamin' in bounds else -np.pi/6
        self.thetamax = bounds['thetamax'] if 'thetamax' in bounds else np.pi/6
        self.g = 9.81
        self.radius = radius

    def set_default_options(self):
        Vehicle.set_default_options(self)
        self.options['stop_tol'] = 5.e-1

    def init(self):
        # time horizon
        self.T = self.define_symbol('T')

    def define_trajectory_constraints(self, splines, horizon_time=None):
        if horizon_time is None:
            horizon_time = self.define_symbol('T')  # motion time
        x, y, z = splines
        ddx, ddy, ddz = x.derivative(2), y.derivative(2), z.derivative(2)
        dddx, dddy, dddz = x.derivative(3), y.derivative(3), z.derivative(3)
        g_tf = self.g*(self.T**2)
        # constraints on u1
        self.define_constraint(-(ddx**2 + ddy**2 + (ddz + g_tf)**2) + (self.T**4)*self.u1min**2, -inf, 0.)
        self.define_constraint((ddx**2 + ddy**2 + (ddz + g_tf)**2) - (self.T**4)*self.u1max**2, -inf, 0.)
        # constraints on u2
        self.define_constraint(-dddy*(ddz+g_tf) + dddz*ddy - ((ddz+g_tf)**2)*(self.T)*(self.u2max), -inf, 0.)
        self.define_constraint(dddy*(ddz+g_tf) - dddz*ddy + ((ddz+g_tf)**2)*(self.T)*(self.u2min), -inf, 0.)
        # constraints on u3
        self.define_constraint(dddx*(ddz+g_tf) - dddz*ddx - ((ddz+g_tf)**2)*(self.T)*(self.u3max), -inf, 0.)
        self.define_constraint(-dddx*(ddz+g_tf) + dddz*ddx + ((ddz+g_tf)**2)*(self.T)*(self.u3min), -inf, 0.)
        # constraints on phi
        self.define_constraint(-ddy - (ddz+g_tf)*(self.phimax), -inf, 0.)
        self.define_constraint(ddy + (ddz+g_tf)*(self.phimin), -inf, 0.)
        # constraints on theta
        self.define_constraint(ddx - (ddz+g_tf)*(self.thetamax), -inf, 0.)
        self.define_constraint(-ddx + (ddz+g_tf)*(self.thetamin), -inf, 0.)

    def get_initial_constraints(self, splines, horizon_time=None):
        if horizon_time is None:
            horizon_time = self.define_symbol('T')  # motion time
        spl0 = self.define_parameter('spl0', 3)
        dspl0 = self.define_parameter('dspl0', 3)
        ddspl0 = self.define_parameter('ddspl0', 3)
        x, y, z = splines
        dx, dy, dz = x.derivative(), y.derivative(), z.derivative()
        ddx, ddy, ddz = x.derivative(2), y.derivative(2), z.derivative(2)
        return [(x, spl0[0]), (y, spl0[1]), (z, spl0[2]),
                (dx, self.T*dspl0[0]), (dy, self.T*dspl0[1]), (dz, self.T*dspl0[2]),
                (ddx, (self.T**2)*ddspl0[0]), (ddy, (self.T**2)*ddspl0[1]), (ddz, (self.T**2)*ddspl0[2])]

    def get_terminal_constraints(self, splines, horizon_time=None):
        if horizon_time is None:
            horizon_time = self.define_symbol('T')  # motion time
        position = self.define_parameter('positionT', 3)
        x, y, z = splines
        term_con = [(x, position[0]), (y, position[1]), (z, position[2])]
        term_con_der = []
        for d in range(1, self.degree+1):
            term_con_der.extend([(x.derivative(d), 0.), (y.derivative(d), 0.), (z.derivative(d), 0.)])
        return [term_con, term_con_der]

    def set_initial_conditions(self, state, input=None):
        if input is None:
            input = np.array([self.g, 0., 0.])
        self.prediction['state'] = state
        self.prediction['input'] = input

    def set_terminal_conditions(self, position):
        self.positionT = position

    def get_init_spline_value(self):
        init_value = np.zeros((len(self.basis), 3))
        pos0 = self.prediction['state'][:3]
        posT = self.positionT
        for k in range(3):
            init_value[:, k] = np.linspace(pos0[k], posT[k], len(self.basis))
            # init_value[:, k] = np.r_[pos0[k]*np.ones(self.degree), np.linspace(
            #     pos0[k], posT[k], len(self.basis) - 2*self.degree), posT[k]*np.ones(self.degree)]
        init_value = [init_value]
        return init_value

    def check_terminal_conditions(self):
        tol = self.options['stop_tol']
        if (np.linalg.norm(self.signals['pose'][:3, -1] - self.positionT) > tol or
                np.linalg.norm(self.signals['dspl'][:, -1])) > tol:
            return False
        else:
            return True

    def set_parameters(self, current_time):
        parameters = Vehicle.set_parameters(self, current_time)
        parameters[self]['spl0'] = self.prediction['state'][:3]
        f0 = self.prediction['input'][0]
        phi0 = self.prediction['state'][6]
        theta0 = self.prediction['state'][7]
        ddx0 = f0*np.cos(phi0)*np.sin(theta0)
        ddy0 = -f0*np.sin(phi0)
        ddz0 = f0*np.cos(phi0)*np.cos(theta0)-self.g
        parameters[self]['ddspl0'] = [ddx0, ddy0, ddz0]
        parameters[self]['dspl0'] = self.prediction['state'][3:6]
        parameters[self]['positionT'] = self.positionT
        return parameters

    def define_collision_constraints(self, hyperplanes, room, splines, horizon_time=None):
        if horizon_time is None:
            horizon_time = self.define_symbol('T')  # motion time
        x, y, z = splines[0], splines[1], splines[2]
        self.define_collision_constraints_3d(hyperplanes, room, [x, y, z], horizon_time)

    def splines2signals(self, splines, time):
        signals = {}
        x, y, z = splines[0], splines[1], splines[2]
        dx, dy, dz = x.derivative(), y.derivative(), z.derivative()
        ddx, ddy, ddz = x.derivative(2), y.derivative(2), z.derivative(2)
        dddx, dddy, dddz = x.derivative(3), y.derivative(3), z.derivative(3)

        x_s, y_s, z_s = sample_splines([x, y, z], time)
        dx_s, dy_s, dz_s = sample_splines([dx, dy, dz], time)
        ddx_s, ddy_s, ddz_s = sample_splines([ddx, ddy, ddz], time)
        dddx_s, dddy_s, dddz_s = sample_splines([dddx, dddy, dddz], time)
        phi = np.arctan2(-ddy_s, np.sqrt(ddx_s**2 + (ddz_s + self.g)**2))
        theta = np.arctan2(ddx_s, ddz_s + self.g)

        u1 = np.sqrt(ddx_s**2 + ddy_s**2 + (ddz_s + self.g)**2)
        u2 = (-dddy_s*(ddx_s**2 + (ddz_s + self.g)**2) + ddy_s*(ddx_s*dddx_s + dddz_s*(ddz_s + self.g))) / \
             ((ddx_s**2 + ddy_s**2 + (ddz_s + self.g)**2)*np.sqrt(ddx_s**2 + (ddz_s + self.g)**2))
        u3 = ((ddz_s + self.g)*dddx_s - ddx_s*dddz_s) / (((ddz_s + self.g)**2) + ddx_s**2)

        signals['state'] = np.c_[x_s, y_s, z_s, dx_s, dy_s, dz_s, phi, theta].T
        signals['input'] = np.c_[u1, u2, u3].T
        signals['dspl'] = np.c_[dx_s, dy_s, dz_s].T
        signals['ddspl'] = np.c_[ddx_s, ddy_s, ddz_s].T
        signals['dddspl'] = np.c_[dddx_s, dddy_s, dddz_s].T

        return signals

    def state2pose(self, state):
        return np.r_[state[0], state[1], state[2], state[6], state[7], 0.]

    def ode(self, state, input):
        phi = state[6]
        theta = state[7]
        u1, u2, u3 = input[0], input[1], input[2]
        return np.r_[state[3:6], u1*np.sin(theta)*np.cos(phi), -u1*np.sin(phi), -self.g + u1*np.cos(phi)*np.cos(theta), u2, u3].T

    def draw(self, t=-1):
        phi, theta = self.signals['pose'][3, t], self.signals['pose'][4, t]
        cth, sth = np.cos(theta), np.sin(theta)
        cphi, sphi = np.cos(phi), np.sin(phi)
        rot = np.array([[cth, sphi*sth, cphi*sth],
                        [0, cphi, -sphi],
                        [-sth, sphi*cth, cphi*cth]])

        r = self.radius
        h, rw = 0.2*r, (1./3.)*r
        s = np.linspace(0, 1-1./48, 48)

        # frame
        plt_xy = [r-rw, r-rw, -r+rw, -r+rw]
        plt_z = [h, 0, 0, h]
        points = np.vstack((plt_xy, np.zeros(len(plt_xy)), plt_z))
        points = rot.dot(points) + np.c_[self.signals['pose'][:3, t]]
        lines = [points]

        points = np.vstack((np.zeros(len(plt_xy)), plt_xy, plt_z))
        points = rot.dot(points) + np.c_[self.signals['pose'][:3, t]]
        lines += [points]

        # rotors
        circle_h = np.vstack((rw*np.cos(s*2*np.pi), rw*np.sin(s*2*np.pi), np.zeros(len(s)), ))
        for i, j in zip([r-rw, 0, -r+rw, 0], [0, r-rw, 0, -r+rw]):
            points = rot.dot(circle_h + np.vstack((i, j, h))) + np.c_[self.signals['pose'][:3, t]]
            lines += [points]

        return [], lines
