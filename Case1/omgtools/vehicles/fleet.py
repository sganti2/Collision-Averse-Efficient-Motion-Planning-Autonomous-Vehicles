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
from ..execution.plotlayer import PlotLayer
import numpy as np


def get_fleet_vehicles(var):
    if isinstance(var, Fleet):
        return var, var.vehicles
    elif isinstance(var, list):
        if isinstance(var[0], Vehicle):
            return Fleet(var), var
        if isinstance(var[0], Fleet):
            return var[0], var[0].vehicles
    elif isinstance(var, Vehicle):
        return Fleet(var), [var]


class Fleet(PlotLayer):

    def __init__(self, vehicles=None, interconnection='circular'):
        vehicles = vehicles or []
        PlotLayer.__init__(self)
        self.vehicles = vehicles if isinstance(vehicles, list) else [vehicles]
        self.interconnection = interconnection
        self.set_neighbors()

    def get_neighbors(self, vehicle):
        return self.nghb_list[vehicle]

    def set_neighbors(self):
        self.N = len(self.vehicles)
        self.nghb_list = {}
        for l, vehicle in enumerate(self.vehicles):
            if self.interconnection == 'circular':
                nghb_ind = [(self.N+l+1) % self.N, (self.N+l-1) % self.N]
            elif self.interconnection == 'full':
                nghb_ind = [k for k in range(self.N) if k != l]
            else:
                raise ValueError('Interconnection type ' + self.interconnection +
                                 ' not understood.')
            self.nghb_list[vehicle] = [self.vehicles[ind] for ind in nghb_ind]

    def set_configuration(self, configuration, orientation=0.):
        self.configuration = {}
        if len(configuration) != self.N:
            raise ValueError('You should provide configuration info ' +
                             'for each vehicle.')
        cth, sth = np.cos(-orientation), np.sin(-orientation)
        for l, config in enumerate(configuration):
            if len(config) == 2:
                config = [config[0]*cth-config[1]*sth, config[0]*sth+config[1]*cth]
            if isinstance(config, dict):
                self.configuration[self.vehicles[l]] = config
            if isinstance(config, list):
                self.configuration[self.vehicles[l]] = {
                    k: con for k, con in enumerate(config)}
        self.set_rel_pos_c()
        self.rel_config = {}
        for vehicle in self.vehicles:
            self.rel_config[vehicle] = {}
            ind_veh = sorted(self.configuration[vehicle].keys())
            for nghb in self.get_neighbors(vehicle):
                self.rel_config[vehicle][nghb] = []
                ind_nghb = sorted(self.configuration[nghb].keys())
                if len(ind_veh) != len(ind_nghb):
                    raise ValueError('All vehicles should have same number ' +
                                     'of variables for which the configuration ' +
                                     'is imposed.')
                for ind_v, ind_n in zip(ind_veh, ind_nghb):
                    self.rel_config[vehicle][nghb].append(
                        self.configuration[vehicle][ind_v] -
                        self.configuration[nghb][ind_n])

    def set_rel_pos_c(self):
        if not hasattr(self, 'configuration'):
            raise ValueError('No configuration set!')
        for veh in self.vehicles:
            ind_veh = sorted(self.configuration[veh].keys())
            veh.rel_pos_c = [-self.configuration[veh][ind] for ind in ind_veh]

    def get_rel_config(self, vehicle):
        return self.rel_config[vehicle]

    def set_initial_conditions(self, states, inputs=None):
        if inputs is None:
            inputs = [None for _ in range(len(states))]
        for state, input, vehicle in zip(states, inputs, self.vehicles):
            vehicle.set_initial_conditions(state, input)

    def set_terminal_conditions(self, conditions):
        for condition, vehicle in zip(conditions, self.vehicles):
            vehicle.set_terminal_conditions(condition)

    def overrule_state(self, states):
        for state, vehicle in zip(states, self.vehicles):
            vehicle.overrule_state(state)

    def overrule_input(self, inputs):
        for input, vehicle in zip(inputs, self.vehicles):
            vehicle.overrule_input(input)

    def reinit_splines(self, problem, values=None):
        if values is None:
            values = [None for veh in self.vehicles]
        for vehicle, value in zip(self.vehicles, values):
            vehicle.reinit_splines(problem, value)

    # ========================================================================
    # Plot related functions
    # ========================================================================

    def init_plot(self, signal, **kwargs):
        if self.vehicles[0].init_plot(signal, **kwargs) is None:
            return None
        vehicle_types = self.sort_vehicles()
        info = []
        for veh_type, vehicles in vehicle_types.items():
            infos = [v.init_plot(signal, **kwargs) for v in vehicles]
            for k in range(len(infos[0])):
                inf = []
                for l in range(len(infos[0][0])):
                    labels = infos[0][k][l]['labels']
                    surfaces, lines = [], []
                    for v in range(len(vehicles)):
                        if 'surfaces' in infos[v][k][l]:
                            surfaces += infos[v][k][l]['surfaces']
                        if 'lines' in infos[v][k][l]:
                            lines += infos[v][k][l]['lines']
                    dic = {'labels': labels, 'surfaces': surfaces, 'lines': lines}
                    if 'xlim' in kwargs:
                        dic['xlim'] = kwargs['xlim']
                    if 'ylim' in kwargs:
                        dic['ylim'] = kwargs['ylim']
                    inf.append(dic)
                info.append(inf)
        return info

    def update_plot(self, signal, t, **kwargs):
        if self.vehicles[0].update_plot(signal, t, **kwargs) is None:
            return None
        vehicle_types = self.sort_vehicles()
        data = []
        for vehicles in vehicle_types.values():
            datas = [v.update_plot(signal, t, **kwargs) for v in vehicles]
            for k in range(len(datas[0])):
                dat = []
                for l in range(len(datas[0][k])):
                    surfaces, lines = [], []
                    for v in range(len(vehicles)):
                        if 'surfaces' in datas[v][k][l]:
                            surfaces += datas[v][k][l]['surfaces']
                        if 'lines' in datas[v][k][l]:
                            lines += datas[v][k][l]['lines']
                    dat.append({'surfaces': surfaces, 'lines': lines})
                data.append(dat)
        return data

    def sort_vehicles(self):
        vehicle_types = {}
        for vehicle in self.vehicles:
            veh_type = vehicle.__class__.__name__
            if veh_type in vehicle_types:
                vehicle_types[veh_type].append(vehicle)
            else:
                vehicle_types[veh_type] = [vehicle]
        return vehicle_types
