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
from ..problems.point2point import FreeTPoint2point, FixedTPoint2point
from ..basics.shape import Square, Circle
from ..basics.spline_extra import sample_splines
from ..basics.spline_extra import evalspline, running_integral, concat_splines
from ..basics.spline import BSplineBasis
from casadi import inf, SX, MX
import numpy as np

# Elaboration of the vehicle model:
# dx = V*cos(theta)
# dy = V*sin(theta)
# dtheta = dtheta

# Use tangent half angle substitution: tg_ha = tan(theta/2)
# sin(theta) = (2*tg_ha)/(1+tg_ha**2)
# cos(theta) = (1-tg_ha**2)/(1+tg_ha**2)
# This gives:
# dx = V/(1+tg_ha**2)*(1-tg_ha**2)
# dy = V/(1+tg_ha**2)*(2*tg_ha)
# Substitute: v_til = V/(1+tg_ha**2)

# dx = v_til*(1-tg_ha**2)
# dy = v_til*(2*tg_ha)
# Spline variables of the problem: v_til and tg_ha


class Dubins(Vehicle):

    def __init__(self, shapes=Circle(0.1), options=None, bounds=None):
        bounds = bounds or {}
        if options is not None and 'degree' in options:
            degree = options['degree']
        else:
            degree = 3
        Vehicle.__init__(
            self, n_spl=2, degree=degree, shapes=shapes, options=options)
        self.vmax = bounds['vmax'] if 'vmax' in bounds else 0.5
        self.amax = bounds['amax'] if 'amax' in bounds else 1.
        # self.amin = bounds['amin'] if 'amin' in bounds else -1.
        self.wmin = bounds['wmin'] if 'wmin' in bounds else -np.pi/6. # in rad/s
        self.wmax = bounds['wmax'] if 'wmax' in bounds else np.pi/6.

    def set_default_options(self):
        Vehicle.set_default_options(self)
        self.options.update({'stop_tol': 1.e-2})
        self.options.update({'substitution' : False})
        self.options.update({'exact_substitution' : False})

    def init(self):
        self.t = self.define_symbol('t')  # current time of first knot
        self.pos0 = self.define_parameter('pos0', 2)  # current position

    def define_trajectory_constraints(self, splines, horizon_time=None):
        if horizon_time is None:
            horizon_time = self.define_symbol('T')  # motion time
        v_til, tg_ha = splines
        dv_til, dtg_ha = v_til.derivative(), tg_ha.derivative()
        # velocity constraint
        self.define_constraint(
            v_til*(1+tg_ha**2) - self.vmax, -inf, 0.)
        # self.define_constraint(-v_til*(1+tg_ha**2) - self.vmax, -inf, 0)  # backward velocity

        self.define_constraint(-v_til, -inf, 0)  # only forward driving, positive v_tilde

        # acceleration constraint
        # self.define_constraint(
        #     dv_til*(1+tg_ha**2) + 2*v_til*tg_ha*dtg_ha - horizon_time*self.amax, -inf, 0.)
        # self.define_constraint(
        #     -dv_til*(1+tg_ha**2) - 2*v_til*tg_ha*dtg_ha + horizon_time*self.amin, -inf, 0.)


        if self.options['substitution']:
            # substitute velocity and introduce equality constraints
            dx = v_til*(1-tg_ha**2)
            dy = v_til*(2*tg_ha)
            if self.options['exact_substitution']:
                self.dx = self.define_spline_variable('dx', 1, 1, basis=dx.basis)[0]
                self.dy = self.define_spline_variable('dy', 1, 1, basis=dy.basis)[0]
                self.x = self.integrate_once(self.dx, self.pos0[0], self.t, horizon_time)
                self.y = self.integrate_once(self.dy, self.pos0[1], self.t, horizon_time)
                self.define_constraint(self.dx - dx, 0, 0)
                self.define_constraint(self.dy - dy, 0, 0)
            else:
                degree = 3
                knots = np.r_[np.zeros(degree), np.linspace(0., 1., 10+1), np.ones(degree)]
                basis = BSplineBasis(knots, degree)
                self.dx = self.define_spline_variable('dx', 1, 1, basis=basis)[0]
                self.dy = self.define_spline_variable('dy', 1, 1, basis=basis)[0]
                self.x = self.integrate_once(self.dx, self.pos0[0], self.t, horizon_time)
                self.y = self.integrate_once(self.dy, self.pos0[1], self.t, horizon_time)
                x = self.integrate_once(dx, self.pos0[0], self.t, horizon_time)
                y = self.integrate_once(dy, self.pos0[1], self.t, horizon_time)
                eps = 1e-3
                self.define_constraint(self.x - x, -eps, eps)
                self.define_constraint(self.y - y, -eps, eps)

        # Alternative:
        # dx = v_til*(1-tg_ha**2)
        # dy = v_til*(2*tg_ha)
        # ddx, ddy = dx.derivative(), dy.derivative()
        # self.define_constraint(
        #     (dx**2+dy**2) - (horizon_time**2)*self.vmax**2, -inf, 0.)
        # self.define_constraint(
        #     (ddx**2+ddy**2) - (horizon_time**4)*self.amax**2, -inf, 0.)

        # add constraints on change in orientation
        self.define_constraint(2*dtg_ha - (1+tg_ha**2)*horizon_time*self.wmax, -inf, 0.)
        self.define_constraint(-2*dtg_ha + (1+tg_ha**2)*horizon_time*self.wmin, -inf, 0.)


    def get_fleet_center(self, splines, rel_pos, substitute=True):
        horizon_time = self.define_symbol('T')
        t = self.define_symbol('t')
        pos0 = self.define_parameter('pos0', 2)
        v_til, tg_ha = splines
        dv_til, dtg_ha = v_til.derivative(), tg_ha.derivative()
        if self.options['substitution']:
            x, y = self.x, self.y
        else:
            dx = v_til*(1-tg_ha**2)
            dy = v_til*(2*tg_ha)
            x = self.integrate_once(dx, pos0[0], t, horizon_time)
            y = self.integrate_once(dy, pos0[1], t, horizon_time)
        eps = 1.e-2
        center = self.define_spline_variable('formation_center', self.n_dim)
        # self.define_constraint((x-center[0])*(1+tg_ha**2) + rel_pos[0]*2*tg_ha + rel_pos[1]*(1-tg_ha**2), -eps, eps)
        # self.define_constraint((y-center[1])*(1+tg_ha**2) + rel_pos[1]*2*tg_ha - rel_pos[0]*(1-tg_ha**2), -eps, eps)
        self.define_constraint((x-center[0])*(1+tg_ha**2) - rel_pos[1]*2*tg_ha + rel_pos[0]*(1-tg_ha**2), -eps, eps)
        self.define_constraint((y-center[1])*(1+tg_ha**2) + rel_pos[0]*2*tg_ha + rel_pos[1]*(1-tg_ha**2), -eps, eps)
        for d in range(1, self.degree+1):
            for c in center:
                self.define_constraint(c.derivative(d)(1.), 0., 0.)
        return center
        # center = []
        # if substitute:
        #     center_tf = [x*(1+tg_ha**2) + rel_pos[0]*2*tg_ha + rel_pos[1]*(1-tg_ha**2), y*(1+tg_ha**2) + rel_pos[1]*2*tg_ha - rel_pos[0]*(1-tg_ha**2)]
        #     center = self.define_substitute('fleet_center', center_tf)
        #     center.append(tg_ha)
        #     return center
        # else:
        #     if splines[0] is (MX, SX):
        #         center_tf = [x*(1+tg_ha**2) + rel_pos[0]*2*tg_ha + rel_pos[1]*(1-tg_ha**2), y*(1+tg_ha**2) + rel_pos[1]*2*tg_ha - rel_pos[0]*(1-tg_ha**2)]
        #         center_tf.append(tg_ha)
        #         return center_tf

    def get_initial_constraints(self, splines, horizon_time=None):
        if horizon_time is None:
            horizon_time = self.define_symbol('T')  # motion time
        # these make sure you get continuity along different iterations
        # inputs are function of v_til, tg_ha and dtg_ha so impose constraints on these
        v_til0 = self.define_parameter('v_til0', 1)
        # dv_til0 = self.define_parameter('dv_til0', 1)
        tg_ha0 = self.define_parameter('tg_ha0', 1)
        dtg_ha0 = self.define_parameter('dtg_ha0', 1)
        v_til, tg_ha = splines
        dv_til = v_til.derivative()
        dtg_ha = tg_ha.derivative()
        return [(v_til, v_til0), (tg_ha, tg_ha0),
                (dtg_ha, horizon_time*dtg_ha0)]

    def get_terminal_constraints(self, splines, horizon_time=None):
        if horizon_time is None:
            horizon_time = self.define_symbol('T')  # motion time
        posT = self.define_parameter('posT', 2)
        tg_haT = self.define_parameter('tg_haT', 1)
        v_til, tg_ha = splines
        dv_til = v_til.derivative()
        if self.options['substitution']:
            x, y = self.x, self.y
        else:
            dx = v_til*(1-tg_ha**2)
            dy = v_til*(2*tg_ha)
            x = self.integrate_once(dx, self.pos0[0], self.t, horizon_time)
            y = self.integrate_once(dy, self.pos0[1], self.t, horizon_time)
        term_con = [(x, posT[0]), (y, posT[1]), (tg_ha, tg_haT)]
        term_con_der = [(v_til, 0.), (tg_ha.derivative(), 0.)]
        return [term_con, term_con_der]

    def set_initial_conditions(self, state, input=None):
        if input is None:
            input = np.zeros(2)
        self.prediction['state'] = state
        self.prediction['input'] = input
        self.pose0 = state

    def set_terminal_conditions(self, pose):
        self.poseT = pose

    def get_init_spline_value(self):
        # generate initial guess for spline variables
        init_value = np.zeros((len(self.basis), 2))
        v_til0 = np.zeros(len(self.basis))
        tg_ha0 = np.tan(self.prediction['state'][2]/2.)
        tg_haT = np.tan(self.poseT[2]/2.)
        init_value[:, 0] = v_til0
        init_value[:, 1] = np.linspace(tg_ha0, tg_haT, len(self.basis))
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
        # for the optimization problem
        # convert theta to tg_ha here
        parameters = Vehicle.set_parameters(self, current_time)
        parameters[self]['tg_ha0'] = np.tan(self.prediction['state'][2]/2.)
        parameters[self]['v_til0'] = self.prediction['input'][0]/(1+parameters[self]['tg_ha0']**2)
        parameters[self]['dtg_ha0'] = 0.5*self.prediction['input'][1]*(1+parameters[self]['tg_ha0']**2)  # dtg_ha
        # if 'acc' in self.prediction:
        #     parameters[self]['dv_til0'] = (self.prediction['acc'][0]-2*parameters[self]['v_til0']*parameters[self]['tg_ha0']*parameters[self]['dtg_ha0'])/(1+parameters[self]['tg_ha0']**2)
        # else:
        #     parameters[self]['dv_til0'] = (0-2*parameters[self]['v_til0']*parameters[self]['tg_ha0']*parameters[self]['dtg_ha0'])/(1+parameters[self]['tg_ha0']**2)
        parameters[self]['pos0'] = self.prediction['state'][:2]
        parameters[self]['posT'] = self.poseT[:2]  # x,y
        parameters[self]['tg_haT'] = np.tan(self.poseT[2]/2.)
        return parameters

    def define_collision_constraints(self, hyperplanes, environment, splines, horizon_time=None):
        if horizon_time is None:
            horizon_time = self.define_symbol('T')  # motion time
        v_til, tg_ha = splines[0], splines[1]
        if self.options['substitution']:
            x, y = self.x, self.y
        else:
            dx = v_til*(1-tg_ha**2)
            dy = v_til*(2*tg_ha)
            x = self.integrate_once(dx, self.pos0[0], self.t, horizon_time)
            y = self.integrate_once(dy, self.pos0[1], self.t, horizon_time)
        # for circular vehicle, no tg_ha needs to be taken into account in collision avoidance constraints.
        # so don't pass it on then
        if isinstance(self.shapes[0], Circle):
            self.define_collision_constraints_2d(hyperplanes, environment, [x, y], horizon_time)
        else:  # tg_ha is required for collision avoidance
            self.define_collision_constraints_2d(hyperplanes, environment, [x, y], horizon_time, tg_ha=tg_ha)

    def integrate_once(self, dx, x0, t, T=1.):
        dx_int = T*running_integral(dx)
        if isinstance(t, (SX, MX)):
            x = dx_int-evalspline(dx_int, t/T) + x0
        else:
            x = dx_int-dx_int(t/T) + x0
        return x

    def splines2signals(self, splines, time):
        # for plotting and logging
        # note: here the splines are not dimensionless anymore
        signals = {}
        v_til, tg_ha = splines[0], splines[1]
        dtg_ha = tg_ha.derivative()
        dx = v_til*(1-tg_ha**2)
        dy = v_til*(2*tg_ha)
        if not hasattr(self, 'signals'):  # first iteration
            x = self.integrate_once(dx, self.pose0[0], time[0])
            y = self.integrate_once(dy, self.pose0[1], time[0])
        else:
            x = self.integrate_once(dx, self.signals['state'][0, -1], time[0])
            y = self.integrate_once(dy, self.signals['state'][1, -1], time[0])
        x_s, y_s, v_til_s, tg_ha_s, dtg_ha_s = sample_splines([x, y, v_til, tg_ha, dtg_ha], time)
        den = sample_splines([(1+tg_ha**2)], time)[0]
        theta = 2*np.arctan2(tg_ha_s,1)
        dtheta = 2*np.array(dtg_ha_s)/(1.+np.array(tg_ha_s)**2)
        v_s = v_til_s*den
        acc = v_til*(1+tg_ha**2)
        acc = acc.derivative()
        acc_s = sample_splines([acc], time)[0]
        signals['state'] = np.c_[x_s, y_s, theta.T].T
        signals['input'] = np.c_[v_s, dtheta.T].T
        signals['acc'] = np.c_[acc_s].T
        if hasattr(self, 'rel_pos_c'):
            x_c = x_s + sample_splines([self.rel_pos_c[0]*2*tg_ha + self.rel_pos_c[1]*(1-tg_ha**2)], time)[0]/den
            y_c = y_s + sample_splines([self.rel_pos_c[1]*2*tg_ha - self.rel_pos_c[0]*(1-tg_ha**2)], time)[0]/den
            signals['fleet_center'] = np.c_[x_c, y_c].T

        if (self.options['substitution']): # and not self.options['exact_substitution']):  # don't plot error for exact_subs
            dx2 = self.problem.father.get_variables(self, 'dx')
            dy2 = self.problem.father.get_variables(self, 'dy')
            # select horizon_time
            if isinstance(self.problem, FreeTPoint2point):
                horizon_time = self.problem.father.get_variables(self.problem, 'T')[0][0]
            elif isinstance(self.problem, FixedTPoint2point):
                horizon_time = self.problem.options['horizon_time']
            dx2 = concat_splines([dx2], [horizon_time])[0]
            dy2 = concat_splines([dy2], [horizon_time])[0]
            if not hasattr(self, 'signals'): # first iteration
                x2 = self.integrate_once(dx2, self.pose0[0], time[0])
                y2 = self.integrate_once(dy2, self.pose0[1], time[0])
            else:
                x2 = self.integrate_once(dx2, self.signals['state'][0, -1], time[0])
                y2 = self.integrate_once(dy2, self.signals['state'][1, -1], time[0])
            dx_s, dy_s = sample_splines([dx, dy], time)
            x_s2, y_s2, dx_s2, dy_s2 = sample_splines([x2, y2, dx2, dy2], time)
            signals['err_dpos'] = np.c_[dx_s-dx_s2, dy_s-dy_s2].T
            signals['err_pos'] = np.c_[x_s-x_s2, y_s-y_s2].T

        return signals

    def state2pose(self, state):
        return state

    def ode(self, state, input):
        # state: x, y, theta
        # inputs: V, dtheta
        # find relation between dstate and state, inputs: dx = Ax+Bu
        # dstate = dx, dy, dtheta
        # dstate[2] = input[1]
        u1, u2 = input[0], input[1]
        return np.r_[u1*np.cos(state[2]), u1*np.sin(state[2]), u2].T

    def draw(self, t=-1):
        surfaces = []
        for shape in self.shapes:
            if isinstance(shape, Circle):
                wheel = Square(shape.radius/3.)
                front = Circle(shape.radius/8.)
                surfaces += shape.draw(self.signals['pose'][:, t])[0]
                surfaces += wheel.draw(self.signals['pose'][:, t]+
                                  (shape.radius/2.)*np.array([np.cos(self.signals['pose'][2, t]-np.pi/2.),
                                                             np.sin(self.signals['pose'][2, t]-np.pi/2.),
                                                             0]))[0]
                surfaces += wheel.draw(self.signals['pose'][:, t]+
                                  (shape.radius/2.)*np.array([np.cos(self.signals['pose'][2, t]+np.pi/2.),
                                                             np.sin(self.signals['pose'][2, t]+np.pi/2.),
                                                             0]))[0]
                surfaces += front.draw(self.signals['pose'][:, t]+
                                  (shape.radius/1.5)*np.array([np.cos(self.signals['pose'][2, t]),
                                                               np.sin(self.signals['pose'][2, t]),
                                                               0]))[0]
            else:
                surfaces += shape.draw(self.signals['pose'][:, t])[0]
        return surfaces, []

    def get_pos_splines(self, splines):
        horizon_time = self.define_symbol('T')  # motion time
        pos0 = self.define_parameter('pos0', 2)  # current position
        v_til, tg_ha = splines
        if self.options['substitution']:
            x, y = self.x, self.y
        else:
            dx = v_til*(1-tg_ha**2)
            dy = v_til*(2*tg_ha)
            x = self.integrate_once(dx, pos0[0], self.t, horizon_time)
            y = self.integrate_once(dy, pos0[1], self.t, horizon_time)
        return [x, y]

    # Next two functions are required if vehicle is not passed to problem, but is still used in the optimization
    # problem e.g. when considering a vehicle with a trailer. You manually have to update signals and prediction,
    # here the inputs are coming from e.g. the trailer class.
    def update_signals(self, signals):
        self.signals = signals

    def update_prediction(self, prediction):
        self.prediction = prediction
