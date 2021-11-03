# -*- coding: utf-8 -*-

"""

Date: 3rd of November 2021
Author: Christoph Pels Leusden, Jakob Wolf

"""

###############################################################################
# imports
###############################################################################

# Default logger of oemof
import oemof.solph as solph
from oemof.solph import helpers
from oemof.tools import logger
import logging
import os
import pandas as pd
import yaml


def run_model(config_path, team_number):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.CLoader)

    if cfg['debug']:
        number_of_time_steps = 3
    else:
        number_of_time_steps = 8760

    solver = cfg['solver']
    debug = cfg['debug']
    solver_verbose = cfg['solver_verbose']  # show/hide solver output

    # initiate the logger (see the API docs for more information)
    logger.define_logging(logfile='model_team_{0}.log'.format(team_number+1),
                          screen_level=logging.INFO,
                          file_level=logging.DEBUG)

    logging.info('Initialize the energy system')
    date_time_index = pd.date_range('1/1/2030', periods=number_of_time_steps,
                                    freq='H')

    energysystem = solph.EnergySystem(timeindex=date_time_index)

    ##########################################################################
    # Read time series and parameter values from data files
    ##########################################################################

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    file_path_ts = abs_path + '/data/' + cfg[
        'time_series_file_name']
    data = pd.read_csv(file_path_ts)

    # file_path_weather_ts = abs_path + '/data_preprocessed/' + cfg[
    #     'weather_time_series']
    # weather_data = pd.read_csv(file_path_weather_ts)

    file_name_param_01 = cfg['design_parameters_file_name'][team_number]
    file_name_param_02 = cfg['parameters_file_name']
    file_path_param_01 = (abs_path + '/data/'
                          + file_name_param_01)
    file_path_param_02 = (abs_path + '/data/'
                          + file_name_param_02)
    param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
    param_df_02 = pd.read_csv(file_path_param_02, index_col=1)
    param_df = pd.concat([param_df_01, param_df_02], sort=True)
    param_value = param_df['value']

    ##########################################################################
    # Create oemof object
    ##########################################################################

    logging.info('Create oemof objects')

    bgas = solph.Bus(label="natural_gas")
    bel = solph.Bus(label="electricity")
    bth = solph.Bus(label='heat')

    energysystem.add(bgas, bel, bth)

    # Sources and sinks
    energysystem.add(solph.Sink(
        label='excess_bel',
        inputs={bel: solph.Flow(
            variable_costs=param_value['var_costs_excess_bel'])}))
    energysystem.add(solph.Sink(
        label='excess_bth',
        inputs={bth: solph.Flow(
            variable_costs=param_value['var_costs_excess_bth'])}))
    energysystem.add(solph.Source(
        label='shortage_bel',
        outputs={bel: solph.Flow(
            variable_costs=param_value['var_costs_shortage_bel'])}))
    energysystem.add(solph.Source(
        label='shortage_bth',
        outputs={bth: solph.Flow(
            variable_costs=param_value['var_costs_shortage_bth'])}))
    energysystem.add(solph.Source(
        label='rgas',
        outputs={bgas: solph.Flow(
            nominal_value=param_value['nom_val_gas'],
            summed_max=param_value['sum_max_gas'],
            variable_costs=param_value['var_costs_gas'])}))

    if param_value['number_of_windturbines'] > 0:
        energysystem.add(solph.Source(
        label='wind_turbine',
        outputs={bel: solph.Flow(
            fix=data['Wind_power [kW/unit]'],
            nominal_value = 0.001 * param_value['number_of_windturbines']
            )},))

    energysystem.add(solph.Sink(
        label='demand_el',
        inputs={bel: solph.Flow(
            fix=data['Demand_el [MWh]'],  # [MWh]
            nominal_value=1)}))

    energysystem.add(solph.Sink(
        label='demand_th',
        inputs={bth: solph.Flow(
            fix=data['Demand_th [MWh]'],  # [MWh]
            nominal_value=1)}))

    # Open-field photovoltaic power plant
    if param_value['number_of_PV_pp'] > 0:
        energysystem.add(solph.Source(
            label='PV_pp',
            outputs={bel: solph.Flow(
                fix=(data['Sol_irradiation [Wh/sqm]'] * 0.000001
                              * param_value['eta_PV']),  # [MWh/m²]
                nominal_value=param_value['PV_pp_surface_area']*10000  # [m²]
                )}))

    # Rooftop photovoltaic
    if param_value['area_PV'] > 0:
        energysystem.add(solph.Source(
            label='PV',
            outputs={bel: solph.Flow(
                fix=(data['Sol_irradiation [Wh/sqm]'] * 0.000001
                              * param_value['eta_PV']),  # [MWh/m²]
                nominal_value=param_value['area_PV']*10000  # [m²]
                )}))

    # Rooftop solar thermal
    if param_value['area_solar_th'] > 0:
        energysystem.add(solph.Source(
            label='solar_thermal',
            outputs={bth: solph.Flow(
                fix=(data['Sol_irradiation [Wh/sqm]'] * 0.000001
                              * param_value['eta_solar_th']),  # [MWh/m²]
                nominal_value=param_value['area_solar_th']*10000  # [m²]
                )}))

    if param_value['number_of_chps'] > 0:
        energysystem.add(solph.Transformer(
            label='chp',
            inputs={
                bgas: solph.Flow()},
            outputs={
                bth: solph.Flow(
                    nominal_value=param_value['number_of_chps']*0.5),  # [MW]
                bel: solph.Flow()},
            conversion_factors={
                bth: param_value['conversion_factor_bth_chp'],
                bel: param_value['conversion_factor_bel_chp']}))

    if param_value['number_of_heat_pumps'] > 0:
        energysystem.add(solph.Transformer(
            label='heat_pump',
            inputs={bel: solph.Flow()},
            outputs={bth: solph.Flow(
                nominal_value=(param_value['number_of_heat_pumps']
                               * param_value['COP_heat_pump']))},  # [MW]
            conversion_factors={bth: param_value['COP_heat_pump']}))

    if param_value['number_of_boilers'] > 0:
        energysystem.add(solph.Transformer(
            label='boiler',
            inputs={bgas: solph.Flow()},
            outputs={bth: solph.Flow(
                nominal_value=param_value['number_of_boilers']*3)},  # [MW]
            conversion_factors={bth: param_value['conversion_factor_boiler']}))

    if param_value['capacity_thermal_storage'] > 0:
        storage_th = solph.components.GenericStorage(
            nominal_storage_capacity=(param_value['capacity_thermal_storage']
                              * param_value['daily_demand_th']),
            label='storage_th',
            inputs={bth: solph.Flow(
                nominal_value=(param_value['capacity_thermal_storage']
                               * param_value['daily_demand_th']
                               / param_value['charge_time_storage_th']))},
            outputs={bth: solph.Flow(
                nominal_value=(param_value['capacity_thermal_storage']
                               * param_value['daily_demand_th']
                               / param_value['charge_time_storage_th']))},
            loss_rate=param_value['capacity_loss_storage_th'],
            initial_storage_level=param_value['init_capacity_storage_th'],
            inflow_conversion_factor=param_value[
                'inflow_conv_factor_storage_th'],
            outflow_conversion_factor=param_value[
                'outflow_conv_factor_storage_th'])
        energysystem.add(storage_th)

    if param_value['capacity_electr_storage'] > 0:
        storage_el = solph.components.GenericStorage(
            nominal_storage_capacity=(param_value['capacity_electr_storage']
                              * param_value['daily_demand_el']),
            label='storage_el',
            inputs={bel: solph.Flow(
                nominal_value=(param_value['capacity_electr_storage']
                               * param_value['daily_demand_el']
                               / param_value['charge_time_storage_el']))},
            outputs={bel: solph.Flow(
                nominal_value=(param_value['capacity_electr_storage']
                               * param_value['daily_demand_el']
                               / param_value['charge_time_storage_el']))},
            loss_rate=param_value['capacity_loss_storage_el'],
            initial_storage_level=param_value['init_capacity_storage_el'],
            inflow_conversion_factor=param_value[
                'inflow_conv_factor_storage_el'],
            outflow_conversion_factor=param_value[
                'outflow_conv_factor_storage_el'])
        energysystem.add(storage_el)

    ##########################################################################
    # Optimise the energy system and plot the results
    ##########################################################################

    logging.info('Optimise the energy system')

    model = solph.Model(energysystem)

    if debug:
        filename = os.path.join(
            helpers.extend_basic_path('lp_files'), 'model_team_{0}.lp'.format(team_number+1))
        logging.info('Store lp-file in {0}.'.format(filename))
        model.write(filename, io_options={'symbolic_solver_labels': True})

    # if tee_switch is true solver messages will be displayed
    logging.info('Solve the optimization problem of team {0}'.format(team_number+1))
    model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})

    logging.info('Store the energy system with the results.')

    energysystem.results['main'] = solph.processing.results(model)
    energysystem.results['meta'] = solph.processing.meta_results(model)

    energysystem.dump(dpath=abs_path + "/results/optimisation_results/dumps",
                      filename="model_team_{0}.oemof".format(team_number+1))


