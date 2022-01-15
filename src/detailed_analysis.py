###############################################################################
# imports
###############################################################################
import oemof.solph as solph
import oemof.tools.economics as eco

import os
import pandas as pd
import matplotlib.pyplot as plt
import yaml


def my_detailed_analysis(config_file_path, plot_results=True):

    with open(config_file_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.CLoader)

    for n in range(cfg['number_of_teams']):
        if n == 0:
            teamdata = analyse_energy_system(
                config_path=config_file_path, team_number=n)
        else:
            teamdata_aux = analyse_energy_system(
                config_path=config_file_path, team_number=n)
            teamdata = pd.concat(
                [teamdata, teamdata_aux])

        if n == cfg['number_of_teams']-1:
            print('S i m u l a t i o n  f i n i s h e d !')

    teamdata.to_csv('../results/optimisation_results/tables/results.csv')

    if plot_results:
            plot_team_results(config_path=config_file_path,
                              df_basic_results_and_team_decision=teamdata)

    return


def analyse_energy_system(config_path, team_number):
    ########################################
    #         Mange Paths and Files        #
    ########################################
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.CLoader)

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

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

    ########################################
    #       Compute Number of Components   #
    ########################################
    number_of_chps = param_value['number_of_chps']
    number_of_boilers = param_value['number_of_boilers']
    number_of_windturbines = param_value['number_of_windturbines']
    number_of_heat_pumps = param_value['number_of_heat_pumps']
    number_of_daydemand_capacity_el = param_value['capacity_electr_storage']
    number_of_daydemand_capacity_th = param_value['capacity_thermal_storage']
    area_pv = param_value['area_PV']
    area_solar_th = param_value['area_solar_th']
    number_of_pv_pp = param_value['number_of_PV_pp']

    ########################################
    #      Extract Data From Solution      #
    ########################################
    energysystem = solph.EnergySystem()
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    energysystem.restore(
        dpath=abs_path + "/results/optimisation_results/dumps",
        filename="model_team_{0}.oemof".format(team_number+1))

    string_results = solph.views.convert_keys_to_strings(
        energysystem.results['main'])
    shortage_electricity = string_results[
        'shortage_bel', 'electricity']['sequences']
    shortage_heat = string_results[
        'shortage_bth', 'heat']['sequences']
    excess_electricity = string_results[
        'electricity', 'excess_bel']['sequences']
    excess_heat = string_results[
        'heat', 'excess_bth']['sequences']
    gas_consumption = string_results[
        'rgas', 'natural_gas']['sequences']
    heat_demand = string_results[
        'heat', 'demand_th']['sequences']
    el_demand = string_results[
        'electricity', 'demand_el']['sequences']
    if number_of_windturbines > 0:
        el_from_wind = string_results[
        'wind_turbine', 'electricity']['sequences']
    if area_pv > 0:
        el_from_pv = string_results[
            'PV', 'electricity']['sequences']
    if number_of_pv_pp > 0:
        el_from_pv_pp = string_results[
            'PV_pp', 'electricity']['sequences']
    if area_solar_th > 0:
        heat_from_solar = string_results[
        'solar_thermal', 'heat']['sequences']
    if number_of_chps > 0:
        el_from_chp = string_results[
            'chp', 'electricity']['sequences']
        heat_from_chp = string_results[
        'chp', 'heat']['sequences']
        fuel_to_chp = string_results[
            'natural_gas', 'chp']['sequences']
    if number_of_boilers > 0:
        heat_from_boiler = string_results[
        'boiler', 'heat']['sequences']
        fuel_to_boiler = string_results[
            'natural_gas', 'boiler']['sequences']
    if number_of_heat_pumps > 0:
        heat_from_hp = string_results[
            'heat_pump', 'heat']['sequences']
        el_to_hp = string_results[
            'electricity', 'heat_pump']['sequences']
        
    ########################################
    #         Compute KPI Cost             #
    ########################################
    capex_chp = (number_of_chps * param_value['invest_cost_chp'])
    capex_boiler = (number_of_boilers * param_value['invest_cost_boiler'])
    capex_wind = (number_of_windturbines * param_value['invest_cost_wind'])
    capex_hp = (number_of_heat_pumps * param_value['invest_cost_heatpump'])
    capex_storage_el = (number_of_daydemand_capacity_el
                        * param_value['invest_cost_storage_el'])
    capex_storage_th = (number_of_daydemand_capacity_th
                        * param_value['invest_cost_storage_th'])
    capex_pv = area_pv * param_value['invest_cost_pv']
    capex_solarthermal = (area_solar_th
                          * param_value['invest_cost_solarthermal'])
    capex_PV_pp = (number_of_pv_pp
                   * param_value['invest_cost_PV_pp']
                   * param_value['PV_pp_surface_area'])

    annuity_chp = eco.annuity(
        capex_chp,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_boiler = eco.annuity(
        capex_boiler,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_wind = eco.annuity(
        capex_wind,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_hp = eco.annuity(
        capex_hp,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_storage_el = eco.annuity(
        capex_storage_el,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_storage_th = eco.annuity(
        capex_storage_th,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_pv = eco.annuity(
        capex_pv,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_solar_th = eco.annuity(
        capex_solarthermal,
        param_value['lifetime'],
        param_value['wacc'])
    annuity_PV_pp = eco.annuity(
        capex_PV_pp,
        param_value['lifetime'],
        param_value['wacc'])

    total_annuity = (annuity_chp + annuity_boiler + annuity_wind
                     + annuity_hp + annuity_storage_el
                     + annuity_storage_th + annuity_pv
                     + annuity_solar_th + annuity_PV_pp
                     )

    var_costs_gas = gas_consumption.flow.sum()*param_value['var_costs_gas']
    var_costs_el_import = (shortage_electricity.flow.sum()
                           * param_value['var_costs_shortage_bel'])
    var_costs_heat_import = (shortage_heat.flow.sum()
                             * param_value['var_costs_shortage_bth'])
    var_costs_es = var_costs_gas + var_costs_el_import + var_costs_heat_import

    ########################################
    #         Compute Sum of Energy        #
    ########################################
    if number_of_chps > 0:
        el_from_chp_sum = el_from_chp.flow.sum()
        heat_from_chp_sum = heat_from_chp.flow.sum()
        fuelconsump_chp = fuel_to_chp.flow.sum()
    else:
        el_from_chp_sum = 0
        heat_from_chp_sum = 0
        fuelconsump_chp = 0

    if number_of_boilers > 0:
        heat_from_boiler_sum = heat_from_boiler.flow.sum()
        fuelconsump_boiler = fuel_to_boiler.flow.sum()
    else:
        heat_from_boiler_sum = 0
        fuelconsump_boiler = 0

    if (area_pv > 0) & (number_of_pv_pp > 0):
        el_from_PV_sum = (el_from_pv.flow.sum() + el_from_pv_pp.flow.sum())
    elif area_pv > 0:
        el_from_PV_sum = el_from_pv.flow.sum()
    elif number_of_pv_pp > 0:
        el_from_PV_sum = el_from_pv_pp.flow.sum()
    else:
        el_from_PV_sum = 0

    if area_solar_th > 0:
        heat_from_solar_sum = heat_from_solar.flow.sum()
    else:
        heat_from_solar_sum = 0

    if number_of_windturbines > 0:
        el_from_wind_sum = el_from_wind.flow.sum()
    else:
        el_from_wind_sum = 0

    if number_of_heat_pumps > 0:
        heat_from_hp_sum = heat_from_hp.flow.sum()
        el_consumption_hp = el_to_hp.flow.sum()
    else:
        heat_from_hp_sum = 0
        el_consumption_hp = 0

    el_consumption_incl_heatpump = el_demand.flow.sum() + el_consumption_hp
    el_from_grid = shortage_electricity.flow.sum()
    heat_from_grid = shortage_heat.flow.sum()
    heat_demand_sum = heat_demand.flow.sum()


    ########################################
    #       Compute KPI Sufficiency        #
    ########################################
    coverage_el = ((el_demand.flow.sum() - shortage_electricity.flow.sum())
                       /el_demand.flow.sum())
    coverage_heat = ((heat_demand.flow.sum() - shortage_heat.flow.sum())
                      / heat_demand.flow.sum())
    selfsufficiency = (coverage_el + coverage_heat)/2

    ########################################
    #         Compute Emission Details     #
    ########################################
    emissions_el_import = el_from_grid*param_value['emission_el']
    emissions_heat_import = heat_from_grid*param_value['emission_heat']
    emissions_chp = fuelconsump_chp*param_value['emission_gas']  
    emissions_boiler = fuelconsump_boiler*param_value['emission_gas']
    
    em_co2 = emissions_el_import + emissions_heat_import + emissions_chp + emissions_boiler

    ########################################
    #         Setup Return Data            #
    ########################################
    markersize = max([float(selfsufficiency), .03])
    basic_results_and_team_decision = {
                 'team name': cfg['team_names'][team_number],
                 'costs': [(var_costs_es+total_annuity)/1e6],
                 'emissions': [em_co2/1e3],
                 'selfsufficiency': markersize*100, #Autarkie in Prozent gestellt mit *100
                 'chps': number_of_chps,
                 'boilers': number_of_boilers,
                 'windturbines': number_of_windturbines,
                 'heatpumps': number_of_heat_pumps,
                 'EES': number_of_daydemand_capacity_el,
                 'TES': number_of_daydemand_capacity_th,
                 'PV': area_pv,
                 'solarthermal': area_solar_th,
                 'selfsufficiency electric': coverage_el,                 
                 'selfsufficiency heat': coverage_heat,                 
                 'emissions production': [(emissions_chp + emissions_boiler)/1e3],                 
                 'emissions purchase': [(emissions_el_import + emissions_heat_import)/1e3], 
                 'cost invest': [total_annuity/1e6], 
                 'cost operation': [var_costs_es/1e6],
                 'total el demand': el_consumption_incl_heatpump,
                 'total el production': el_from_chp_sum + el_from_PV_sum + el_from_wind_sum,
                 'total el purchase': el_from_grid,
                 'total el excess': excess_electricity.flow.sum(),
                 'total heat demand': heat_demand_sum,
                 'total heat production': heat_from_chp_sum + heat_from_boiler_sum + heat_from_solar_sum + heat_from_hp_sum,
                 'total heat purchase': heat_from_grid,
                 'total heat excess': excess_heat.flow.sum()
                 }

    ########################################
    #              Return Data             #
    ########################################
    # Basic Results and team decision on system design (number of units,
    # size of storage etc)
    df_basic_results_and_team_decision = pd.DataFrame(
        data=basic_results_and_team_decision,
        index=[team_number])

    return df_basic_results_and_team_decision


def plot_team_results(config_path, df_basic_results_and_team_decision):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.CLoader)

    red_beuth = (227/255, 35/255, 37/255)
    beuth_col_1 = (223/255, 242/255, 243/255)
    beuth_col_2 = (178/255, 225/255, 227/255)
    beuth_col_3 = (0/255, 152/255, 161/255)
    for show_team_names in [False, True]:
        plt.figure(figsize=(8, 6)) #default figsize=(8, 6)
        plt.style.use('ggplot')
        plt.rcParams['axes.facecolor'] = beuth_col_3
        plt.ylabel('CO2-Emissionen in t/a', fontsize=14)
        plt.xlabel('Kosten in Mio. €/a', fontsize=14)
        plt.axis([0, 50, 0, 40000]) #Default Settings 0, 50, 0, 40000
        #plt.axis([0, 30, 0, 30000])

        plt.title(
            'Jährliche Emissionen und Kosten der Energieversorgung',
            fontsize=14)
        plt.suptitle(cfg['workshop_title'],
                     fontsize=10)
        plt.tick_params(axis='both', which='major', labelsize=12)
        #N = len(df_basic_results_and_team_decision)
        labels_list = []
        for tn in cfg['team_names']:
            # new_name = 'Team ' + tn
            new_name = tn
            labels_list.append(new_name)
        labels = labels_list
        plt.scatter(
            df_basic_results_and_team_decision['costs'],
            df_basic_results_and_team_decision['emissions'],
            marker='o',
            c=[red_beuth],
            s=df_basic_results_and_team_decision['selfsufficiency'] * 10, #default *1000
            edgecolors=beuth_col_2,
            linewidths=1.0,
            alpha=1,
            cmap=plt.get_cmap('Spectral'))
        plt.text(1, 2000, 'Copyright ©, Berliner Hochschule für '
                 + 'Technik, 2022. All rights reserved.',
                 fontsize=11.5, color=beuth_col_1,
                 ha='left', va='top', alpha=0.5)
        if not show_team_names:
            # plt.show()
            plt.savefig('../results/plots/results_no_names.png', dpi=300)

        if show_team_names:
            for label, x, y in zip(
                    labels,
                    df_basic_results_and_team_decision['costs'],
                    df_basic_results_and_team_decision['emissions']):
                plt.annotate(
                    label,
                    xy=(x, y),
                    xytext=(75, 40),
                    textcoords='offset points',
                    ha='right',  # horizontal alignment
                    va='bottom',  # vertical alignment 'bottom'
                    bbox=dict(
                        boxstyle='round,pad=0.5',
                        fc=beuth_col_1,
                        alpha=0.5),
                    arrowprops=dict(
                        arrowstyle='->',
                        connectionstyle='arc3,rad=0'))
            plt.savefig(
                '../results/plots/results_with_team_names.png',
                dpi=300)
