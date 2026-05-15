###############################################################################
# imports
###############################################################################

import oemof.solph as solph
import oemof.tools.economics as eco

import os
import pandas as pd
import yaml
import logging


def analyse_energy_system(config_path, team_number):
    ########################################
    #         Mange Paths and Files        #
    ########################################
    with open(config_path, encoding="utf-8") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.CLoader)

    logging.info("Analyse Data")

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))

    file_name_param_01 = cfg["design_parameters_file_name"][team_number]
    file_name_param_02 = cfg["parameters_file_name"]
    #path = f"{abs_path}/{cfg['institution']}/{cfg['instructor']}/{cfg['schedule']}"
    fpath = "../data/"
    file_path_param_01 = fpath + file_name_param_01
    file_path_param_02 = fpath + file_name_param_02
    param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
    param_df_02 = pd.read_csv(file_path_param_02, index_col=1)
    param_df = pd.concat([param_df_01, param_df_02], sort=True)
    param_value = param_df["value"]
    num_persons = 10000.0

    ########################################
    #      Extract Data From Solution      #
    ########################################
    energysystem = solph.EnergySystem()
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
    #path = f"{abs_path}/{cfg['institution']}/{cfg['instructor']}/{cfg['schedule']}"
    dpath = "../results/optimisation_results/dumps"
    #os.makedirs(dpath, exist_ok=True)
    energysystem.restore(dpath=dpath, filename="model_team_{}.oemof".format(team_number+1))

    ########################################
    #       Compute Number of Components   #
    ########################################
    number_of_chps = param_value["number_of_chps"]
    number_of_boilers = param_value["number_of_boilers"]
    number_of_windturbines = param_value["number_of_windturbines"]
    number_of_heat_pumps = param_value["number_of_heat_pumps"]
    number_of_daydemand_capacity_el = param_value["capacity_electr_storage"]
    number_of_daydemand_capacity_th = param_value["capacity_thermal_storage"]
    area_pv = param_value["area_PV"]
    area_solar_th = param_value["area_solar_th"]
    number_of_pv_pp = param_value["number_of_PV_pp"]

    # if cfg["enable_building_retrofit"]:
    #     percentage_building_retrofit = param_value["feature_building_retrofit"]
    # else:
    #     percentage_building_retrofit = 0

    # if cfg["enable_mobility"]:
    #     percentage_of_bev = param_value["percentage_of_bev"]
    # else:
    #     percentage_of_bev = 0

    string_results = solph.views.convert_keys_to_strings(energysystem.results["main"])
    shortage_electricity = string_results["shortage_bel", "electricity"]["sequences"]
    shortage_heat = string_results["shortage_bth", "heat"]["sequences"]
    excess_electricity = string_results["electricity", "excess_bel"]["sequences"]
    excess_heat = string_results["heat", "excess_bth"]["sequences"]
    gas_consumption = string_results["rgas", "natural_gas"]["sequences"]
    heat_demand = string_results["heat", "demand_th"]["sequences"]
    el_demand = string_results["electricity", "demand_el"]["sequences"]
    if number_of_windturbines > 0:
        el_from_wind = string_results["wind_turbine", "electricity"]["sequences"]
    if area_pv > 0:
        el_from_pv = string_results["PV", "electricity"]["sequences"]
    if number_of_pv_pp > 0:
        el_from_pv_pp = string_results["PV_pp", "electricity"]["sequences"]
    if area_solar_th > 0:
        heat_from_solar = string_results["solar_thermal", "heat"]["sequences"]
    if number_of_chps > 0:
        el_from_chp = string_results["chp", "electricity"]["sequences"]
        heat_from_chp = string_results["chp", "heat"]["sequences"]
        fuel_to_chp = string_results["natural_gas", "chp"]["sequences"]
    if number_of_boilers > 0:
        heat_from_boiler = string_results["boiler", "heat"]["sequences"]
        fuel_to_boiler = string_results["natural_gas", "boiler"]["sequences"]
    if number_of_heat_pumps > 0:
        heat_from_hp = string_results["heat_pump", "heat"]["sequences"]
        el_to_hp = string_results["electricity", "heat_pump"]["sequences"]
    if number_of_daydemand_capacity_el > 0:
        EES_discharge = string_results["storage_el", "electricity"]["sequences"]
    if number_of_daydemand_capacity_th > 0:
        TES_discharge = string_results["storage_th", "heat"]["sequences"]

    # if cfg["enable_mobility"]:
    #     fuel_consumption = string_results["rfuel", "fuel"]["sequences"]
    #     if percentage_of_bev > 0:
    #         mobility_of_bev = string_results["bev_discharge", "mobility_bev"]["sequences"]
    #         el_to_bev = string_results["electricity", "bev_charge"]["sequences"]
    #     if percentage_of_bev < 100:
    #         mobility_of_car = string_results["car", "mobility"]["sequences"]
    #         fuel_to_car = string_results["fuel", "car"]["sequences"]

    ########################################
    #      Compute Nominal Power           #
    ########################################
    nom_power_chps_el = (
        number_of_chps
        * (param_value["conversion_factor_bel_chp"] / param_value["conversion_factor_bth_chp"])
        * param_value["chp_heat_output"]
    )
    nom_power_chps_th = number_of_chps * param_value["chp_heat_output"]
    nom_power_boilers = number_of_boilers * param_value["boiler_heat_output"]
    nom_power_heat_pumps = number_of_heat_pumps * param_value["heatpump_heat_output"]
    nom_capacity_storage_el = number_of_daydemand_capacity_el * param_value["daily_demand_el"]
    nom_capacity_storage_th = number_of_daydemand_capacity_th * param_value["daily_demand_th"]
    #    nom_capacity_storage_bev = param_value['capacity_bev_storage'] * param_value['vehicle'] * (param_value['percentage_of_bev'] / 100)

    if area_pv > 0:
        nom_power_pv = el_from_pv.flow.max()
    else:
        nom_power_pv = 0
    if area_solar_th > 0:
        nom_power_solar_thermal = heat_from_solar.flow.max()
    else:
        nom_power_solar_thermal = 0
    if number_of_pv_pp > 0:
        nom_power_pv_pp = el_from_pv_pp.flow.max()
    else:
        nom_power_pv_pp = 0
    ########################################
    #         Compute KPI Cost             #
    ########################################
    capex_chp = number_of_chps * param_value["invest_cost_chp"]
    capex_boiler = number_of_boilers * param_value["invest_cost_boiler"]
    capex_wind = number_of_windturbines * param_value["invest_cost_wind"]
    capex_hp = number_of_heat_pumps * param_value["invest_cost_heatpump"]
    capex_storage_el = number_of_daydemand_capacity_el * param_value["invest_cost_storage_el"]
    capex_storage_th = number_of_daydemand_capacity_th * param_value["invest_cost_storage_th"]
    capex_pv = area_pv * param_value["invest_cost_pv"]
    capex_solarthermal = area_solar_th * param_value["invest_cost_solarthermal"]
    capex_PV_pp = number_of_pv_pp * param_value["invest_cost_PV_pp"] * param_value["PV_pp_surface_area"]
    #capex_building_retrofit = percentage_building_retrofit * param_value["invest_cost_building_retrofit"]
    # Investitionskosten Mobility
    # if cfg["enable_mobility"]:
    #     capex_car = (
    #         (100 - param_value["percentage_of_bev"]) / 100 * param_value["invest_cost_car"] * param_value["vehicle"]
    #     )
    #     capex_bev = param_value["percentage_of_bev"] / 100 * param_value["invest_cost_bev"] * param_value["vehicle"]
    # else:
    #     capex_car = 0
    #     capex_bev = 0

    annuity_chp = eco.annuity(capex_chp, param_value["lifetime"], param_value["wacc"])
    annuity_boiler = eco.annuity(capex_boiler, param_value["lifetime"], param_value["wacc"])
    annuity_wind = eco.annuity(capex_wind, param_value["lifetime"], param_value["wacc"])
    annuity_hp = eco.annuity(capex_hp, param_value["lifetime"], param_value["wacc"])
    annuity_storage_el = eco.annuity(capex_storage_el, param_value["lifetime"], param_value["wacc"])
    annuity_storage_th = eco.annuity(capex_storage_th, param_value["lifetime"], param_value["wacc"])
    annuity_pv = eco.annuity(capex_pv, param_value["lifetime"], param_value["wacc"])
    annuity_solar_th = eco.annuity(capex_solarthermal, param_value["lifetime"], param_value["wacc"])
    annuity_PV_pp = eco.annuity(capex_PV_pp, param_value["lifetime"], param_value["wacc"])
    #annuity_building_retrofit = eco.annuity(capex_building_retrofit, param_value["lifetime"], param_value["wacc"])
    #annuity_car = eco.annuity(capex_car, param_value["lifetime"], param_value["wacc"])
    #annuity_bev = eco.annuity(capex_bev, param_value["lifetime"], param_value["wacc"])

    total_annuity = (
        annuity_chp
        + annuity_boiler
        + annuity_wind
        + annuity_hp
        + annuity_storage_el
        + annuity_storage_th
        + annuity_pv
        + annuity_solar_th
        + annuity_PV_pp
    #    + annuity_building_retrofit
    #    + annuity_car
    #    + annuity_bev
    )

    var_costs_gas = gas_consumption.flow.sum() * param_value["var_costs_gas"]
    var_costs_el_import = shortage_electricity.flow.sum() * param_value["var_costs_shortage_bel"]
    var_costs_heat_import = shortage_heat.flow.sum() * param_value["var_costs_shortage_bth"]
    #if cfg["enable_mobility"]:
    #    var_costs_fuel = fuel_consumption.flow.sum() * param_value["var_costs_fuel"]
    #else:
    #    var_costs_fuel = 0

    var_costs_es = var_costs_gas + var_costs_el_import + var_costs_heat_import
    #var_costs_es = var_costs_gas + var_costs_el_import + var_costs_heat_import + var_costs_fuel

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
        el_from_PV_sum = el_from_pv.flow.sum() + el_from_pv_pp.flow.sum()
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

    # if cfg["enable_mobility"]:
    #     if percentage_of_bev > 0:
    #         mobility_of_bev_sum = mobility_of_bev.flow.sum() * param_value["conversion_factor_bev"] * 1000
    #         el_consumption_bev = el_to_bev.flow.sum()
    #     else:
    #         mobility_of_bev_sum = 0
    #         el_consumption_bev = 0
    #     if percentage_of_bev < 100:
    #         mobility_of_car_sum = mobility_of_car.flow.sum()
    #         fuelconsump_car = fuel_to_car.flow.sum()
    #     else:
    #         mobility_of_car_sum = 0
    #         fuelconsump_car = 0
    # else:
    #     mobility_of_bev_sum = 0
    #     el_consumption_bev = 0
    #     mobility_of_car_sum = 0
    #     fuelconsump_car = 0

    #el_demand_bev = el_consumption_bev
    el_demand_sum = el_demand.flow.sum()
    el_consumption_incl_heatpump = el_demand.flow.sum() + el_consumption_hp
    #el_consumption_incl_heatpump_bev = el_demand.flow.sum() + el_consumption_hp + el_consumption_bev
    el_from_grid = shortage_electricity.flow.sum()
    heat_from_grid = shortage_heat.flow.sum()
    heat_demand_sum = heat_demand.flow.sum()
    #mobility_demand_sum = mobility_of_bev_sum + mobility_of_car_sum

    ########################################
    #         Compute Storage Use          #
    ########################################
    if nom_capacity_storage_el > 0:
        EES_discharge_sum = EES_discharge.flow.sum()
        EES_full_load_cycles = EES_discharge_sum / nom_capacity_storage_el
    else:
        EES_discharge_sum = 0
        EES_full_load_cycles = 0

    if nom_capacity_storage_th > 0:
        TES_discharge_sum = TES_discharge.flow.sum()
        TES_full_load_cycles = TES_discharge_sum / nom_capacity_storage_th
    else:
        TES_discharge_sum = 0
        TES_full_load_cycles = 0

    #    if percentage_of_bev > 0:
    #        storage_bev_discharge_sum = storage_bev_discharge.flow.sum()
    #        storage_bev_full_load_cycles = (storage_bev_discharge_sum / nom_capacity_storage_bev)
    #    else:
    #        storage_bev_discharge_sum = 0
    #        bev_full_load_cycles = 0
    ########################################
    #       Compute KPI Sufficiency        #
    ########################################

    coverage_el = abs(
    #    (el_consumption_incl_heatpump_bev - shortage_electricity.flow.sum()) / el_consumption_incl_heatpump_bev
        (el_consumption_incl_heatpump - shortage_electricity.flow.sum()) / el_consumption_incl_heatpump
    )
    coverage_heat = abs((heat_demand.flow.sum() - shortage_heat.flow.sum()) / heat_demand.flow.sum())
    selfsufficiency = (coverage_el + coverage_heat) / 2

    ########################################
    #         Compute Emission Details     #
    ########################################
    emissions_el_import = el_from_grid * param_value["emission_el"]
    emissions_heat_import = heat_from_grid * param_value["emission_heat"]
    emissions_chp = fuelconsump_chp * param_value["emission_gas"]
    emissions_boiler = fuelconsump_boiler * param_value["emission_gas"]
    # if cfg["enable_mobility"]:
    #     emissions_car = fuelconsump_car * param_value["emission_fuel"]
    # else:
    #     emissions_car = 0

    #em_co2 = emissions_el_import + emissions_heat_import + emissions_chp + emissions_boiler + emissions_car
    em_co2 = emissions_el_import + emissions_heat_import + emissions_chp + emissions_boiler 

    ########################################
    #         Setup Return Data            #
    ########################################
    markersize = max([float(selfsufficiency), 0.03])
    basic_results_and_team_decision = {
        "team name": cfg["team_names"][team_number],
        "costs": [(var_costs_es + total_annuity) / num_persons],  # EUR/a & Person
        "emissions": [em_co2 / num_persons],  # kg/a & Person
        "selfsufficiency": markersize * 100,  # Autarkie in Prozent gestellt mit *100
        "chps": number_of_chps,
        "boilers": number_of_boilers,
        "windturbines": number_of_windturbines,
        "heatpumps": number_of_heat_pumps,
        "EES": number_of_daydemand_capacity_el,
        "TES": number_of_daydemand_capacity_th,
        "PV": area_pv,
        "solarthermal": area_solar_th,
#        "building_retrofit": percentage_building_retrofit,  # results.csv um eine Spalte erweitern für Gebäudesanierung
#        "percentage_of_bev": percentage_of_bev,  # results um eine Spalte erweitern für E-Mobility
        "el_from_pv": el_from_PV_sum * (1e3 / num_persons),  # kWh/a & Person
        "el_from_wind": el_from_wind_sum * (1e3 / num_persons),  # kWh/a & Person
        "el_from_chp": el_from_chp_sum * (1e3 / num_persons),  # kWh/a & Person
        "el_from_grid": shortage_electricity.flow.sum() * (1e3 / num_persons),  # kWh/a & Person
        "el_demand": el_demand_sum * (1e3 / num_persons),  # kWh/a & Person
        "el_hp_demand": el_consumption_hp * (1e3 / num_persons),  # kWh/a & Person
#        "el_bev_demand": el_demand_bev * (1e3 / num_persons),  # kWh/a & Person
        "el_excess": excess_electricity.flow.sum() * (1e3 / num_persons),  # kWh/a & Person
#        "total_el_demand": el_consumption_incl_heatpump_bev * (1e3 / num_persons),  # kWh/a & Person
        "total_el_demand": el_consumption_incl_heatpump * (1e3 / num_persons),  # kWh/a & Person
        "heat_from_chp": heat_from_chp_sum * (1e3 / num_persons),  # kWh/a & Person
        "heat_from_boiler": heat_from_boiler_sum * (1e3 / num_persons),  # kWh/a & Person
        "heat_from_solar": heat_from_solar_sum * (1e3 / num_persons),  # kWh/a & Person
        "heat_from_hp": heat_from_hp_sum * (1e3 / num_persons),  # kWh/a & Person
        "heat_shortage": heat_from_grid * (1e3 / num_persons),  # kWh/a & Person
        "heat_excess": excess_heat.flow.sum() * (1e3 / num_persons),  # kWh/a & Person
        "heat_demand": heat_demand_sum * (1e3 / num_persons),  # kWh/a & Person
        "em_chp": emissions_chp / num_persons,  # kg/a & Person
        "em_boiler": emissions_boiler / num_persons,  # kg/a & Person
#        "em_car": emissions_car / num_persons,  # kg/a & Person
        "em_el_shortage": emissions_el_import / num_persons,  # kg/a & Person
        "em_heat_shortage": emissions_heat_import / num_persons,  # kg/a & Person
        "var_costs_gas": var_costs_gas / num_persons,  # EUR/a & Person
        "var_costs_el": var_costs_el_import / num_persons,
        "var_costs_heat": var_costs_heat_import / num_persons,
#        "var_costs_fuel": var_costs_fuel / num_persons,
        "var_costs_total": var_costs_es / num_persons,
        "annuity_chp": annuity_chp / num_persons,  # EUR/a & Person
        "annuity_boiler": annuity_boiler / num_persons,
        "annuity_wind": annuity_wind / num_persons,
        "annuity_hp": annuity_hp / num_persons,
        "annuity_storage_el": annuity_storage_el / num_persons,
        "annuity_storage_th": annuity_storage_th / num_persons,
        "annuity_pv": annuity_pv / num_persons,
        "annuity_solar_th": annuity_solar_th / num_persons,
        "annuity_PV_pp": annuity_PV_pp / num_persons,
#        "annuity_building_retrofit": annuity_building_retrofit / num_persons,
#        "annuity_car": annuity_car / num_persons,
#        "annuity_bev": annuity_bev / num_persons,
        "total_annuity": total_annuity / num_persons,
    }

    data_ser = pd.Series(
        [(var_costs_es + total_annuity) / num_persons, em_co2 / num_persons, selfsufficiency * 100],
        index=["Kosten [Eur/a u. Person]", "CO2 Emissionen [kg/a u. Person]", "Gesamtenergie-Autarkie [%]"],
    )

    # Team Decision
    data_add = pd.Series([-1], index=["Energiesystem"])
    data_ser = pd.concat([data_ser, data_add])

    data_add = pd.Series(
        [
            number_of_chps,
            number_of_boilers,
            number_of_heat_pumps,
            number_of_pv_pp,
            number_of_windturbines,
            area_pv,
            area_solar_th,
            number_of_daydemand_capacity_el,
            number_of_daydemand_capacity_th,
#            percentage_building_retrofit,
#            percentage_of_bev,
        ],
        index=[
            "Anzahl BHKW [-]",
            "Anzahl Gaskessel [-]",
            "Anzahl Wärmepumpen [-]",
            "PV-Freiflächenanlage [-]",
            "Anzahl WKA [-]",
            "Dachfläche PV [ha]",
            "Dachfläche Solarthermie [ha]",
            "Kapazität Stromspeicher [-] * Tagesbedarf",
            "Kapazität Wärmespeicher [-] * Tagesbedarf",
#            "Reduzierung Wärmebedarf Gebäude [%]",  # building retrofit in results_table hinzugefügt
#            "Anteil E-Mobilität [%]",
        ],
    )
    data_ser = pd.concat([data_ser, data_add])

    # Electric Energy Sums
    data_add = pd.Series([-1,-2], index=["Energieflüsse", "Strom in kWh/Person & Jahr"])
    data_ser = pd.concat([data_ser, data_add])

    data_add = pd.Series(
        [
            excess_electricity.flow.sum() * (1e3 / num_persons),
            el_demand_sum * (1e3 / num_persons),
            el_consumption_hp * (1e3 / num_persons),
#            el_demand_bev * (1e3 / num_persons),
#            el_consumption_incl_heatpump_bev * (1e3 / num_persons),
            el_consumption_incl_heatpump * (1e3 / num_persons),
            el_from_chp_sum * (1e3 / num_persons),
            el_from_wind_sum * (1e3 / num_persons),
            el_from_PV_sum * (1e3 / num_persons),
            el_from_grid * (1e3 / num_persons),
        ],
        index=[
            "Überschuss el. Energie [kWh/Person]",
            "Bedarf el. Energie Verbrauch[kWh/Person]",
            "Bedarf el. Energie Wärmepumpe [kWh/Person]",
#            "Bedarf el. Energie E-Mobilität [kWh/Person]",
            "Gesamtbedarf el. Energie [kWh/Person]",
            "El. Energie von BHKW [kWh/Person]",
            "El. Energie von WKA [kWh/Person]",
            "El. Energie von PV [kWh/Person]",
            "El. Energie Netzbezug [kWh/Person]",
        ],
    )
    data_ser = pd.concat([data_ser, data_add])

    # Heat Sums
    data_add = pd.Series([-2], index=["Wärme in kWh/Person & Jahr"])
    data_ser = pd.concat([data_ser, data_add])

    data_add = pd.Series(
        [
            excess_heat.flow.sum() * (1e3 / num_persons),
            heat_demand_sum * (1e3 / num_persons),
            heat_from_chp_sum * (1e3 / num_persons),
            heat_from_boiler_sum * (1e3 / num_persons),
            heat_from_solar_sum * (1e3 / num_persons),
            heat_from_hp_sum * (1e3 / num_persons),
            heat_from_grid * (1e3 / num_persons),
        ],
        index=[
            "Überschuss Wärme [kWh/Person]",
            "Bedarf Wärme [kWh/Person]",
            "Wärme von BHKW [kWh/Person]",
            "Wärme von Gaskessel [kWh/Person]",
            "Wärme von Solarthermie [kWh/Person]",
            "Wärme von Wärmepumpe [kWh/Person]",
            "Wärmebezug [kWh/Person]",
        ],
    )
    data_ser = pd.concat([data_ser, data_add])

    # # Mobility Sums
    # data_add = pd.Series([-2], index=["Mobilität in km/Person & Jahr"])
    # data_ser = pd.concat([data_ser, data_add])

    # data_add = pd.Series(
    #     [
    #         mobility_demand_sum / num_persons,
    #         mobility_of_bev_sum / num_persons,
    #         mobility_of_car_sum / num_persons,
    #     ],
    #     index=[
    #         "Gesamtbedarf Mobilität[km/Person]",
    #         "E-Mobilität [km/Person]",
    #         "Konventionelle Mobilität [km/Person]",
    #     ],
    # )
    # data_ser = pd.concat([data_ser, data_add])

    # Consumption Sums
    data_add = pd.Series([-1,-2], index=["Betriebsanalyse", "Verbrauch"])
    data_ser = pd.concat([data_ser, data_add])

    data_add = pd.Series(
        [
            gas_consumption.flow.sum() * (1e3 / num_persons),
#            fuelconsump_car * (1e3 / num_persons),
        ],
        index=[
            "Gasverbrauch [kWh/Person]",
#            "Kraftstoffverbrauch [kWh/Person]",
        ],
    )
    data_ser = pd.concat([data_ser, data_add])

    # Storage Use
    data_add = pd.Series([-2], index=["Speichernutzung"])
    data_ser = pd.concat([data_ser, data_add])

    data_add = pd.Series(
        [
            EES_full_load_cycles,
            TES_full_load_cycles,
        ],
        index=[
            "Vollzyklen Stromspeicher [-]",
            "Vollzyklen Wärmespeicher [-]",
        ],
    )
    data_ser = pd.concat([data_ser, data_add])

    # Coverage
    data_add = pd.Series([-2], index=["Deckungsgrad"])
    data_ser = pd.concat([data_ser, data_add])

    data_add = pd.Series(
        [
            coverage_el * 100,
            coverage_heat * 100,
        ],
        index=[
            "Autharkie el. Energie [%]",
            "Autharkie Wärme [%]",
        ],
    )
    data_ser = pd.concat([data_ser, data_add])

    # Emissions
    data_add = pd.Series([-2], index=["Emissionen"])
    data_ser = pd.concat([data_ser, data_add])

    data_add = pd.Series(
        [
            emissions_chp / num_persons,  # kg/Personen
            emissions_boiler / num_persons,
#            emissions_car / num_persons,
            emissions_el_import / num_persons,
            emissions_heat_import / num_persons,
        ],
        index=[
            "Emissionen durch BHKW [kg/Person]",
            "Emissionen durch Gaskessel [kg/Person]",
#            "Emissionen durch Mobilität [kg/Person]",
            "Emissionen durch Strombezug [kg/Person]",
            "Emissionen durch Wärmebezug [kg/Person]",
        ],
    )
    data_ser = pd.concat([data_ser, data_add])

    # Costs
    data_add = pd.Series([-1,-2], index=["Kostenanalyse", "Investition"])
    data_ser = pd.concat([data_ser, data_add])

    data_add = pd.Series(
        [
            total_annuity / num_persons,
            annuity_chp / num_persons,
            annuity_boiler / num_persons,
            annuity_wind / num_persons,
            annuity_hp / num_persons,
            annuity_solar_th / num_persons,
            (annuity_pv / num_persons + annuity_PV_pp / num_persons),
            annuity_storage_th / num_persons,
            annuity_storage_el / num_persons,
            # annuity_building_retrofit / num_persons,
            # annuity_car / num_persons,
            # annuity_bev / num_persons,
        ],
        index=[
            "Gesamtinvestionskosten [EUR/a u. Person]",
            "Investition BHKW [EUR/a u. Person]",
            "Investition Gaskessel [EUR/a u. Person]",
            "Investition WKA [EUR/a u. Person",
            "Investition Wärmepumpen [EUR/a u. Person]",
            "Investition Solarthermie [EUR/a u. Person]",
            "Investition PV [EUR/a u. Person]",
            "Investition Wärmespeicher [EUR/a u. Person]",
            "Investition Stromspeicher [EUR/a u. Person]",
            # "Investition Gebäudesanierung [EUR/a u. Person]",
            # "Investition Mobilität [EUR/a u. Person]",
            # "Investition E-Mobilität [EUR/a u. Person]",
        ],
    )
    data_ser = pd.concat([data_ser, data_add])

    data_add = pd.Series([-2], index=["Betriebskosten"])
    data_ser = pd.concat([data_ser, data_add])

    data_add = pd.Series(
        [
            var_costs_es / num_persons,
            var_costs_gas / num_persons,
#            var_costs_fuel / num_persons,
            var_costs_el_import / num_persons,
            var_costs_heat_import / num_persons,
        ],
        index=[
            "Gesamte Betriebskosten [EUR/a u. Person]",
            "Kosten Gaseinkauf [EUR/a u. Person]",
#            "Kosten Kraftstoffeinkauf EUR/a u. Person]",
            "Kosten Strombezug [EUR/a u. Person]",
            "Kosten Wärmebezug [EUR/a u. Person]",
        ],
    )
    data_ser = pd.concat([data_ser, data_add])

    detailed_team_results = {cfg["team_names"][team_number]: data_ser}

    ########################################
    #              Return Data             #
    ########################################
    # Basic Results and team decision on system design (number of units,
    # size of storage etc)
    df_basic_results_and_team_decision = pd.DataFrame(
        data=basic_results_and_team_decision, index=[cfg["team_names"][team_number]]
    )

    # Detailed simulation results and operation analysis (energy, costs and
    # emissions produced by each technology, charging cycles etc.)
    df_detailed_team_results = pd.DataFrame.from_dict(detailed_team_results)

    return df_basic_results_and_team_decision, df_detailed_team_results


# def display_results(config_path, team_number):
#     with open(config_path, encoding="utf-8") as ymlfile:
#         cfg = yaml.load(ymlfile, Loader=yaml.CLoader)
#     logging.info("Display Results")
#     file_name = "teamdata_" + cfg["team_names"][team_number] + ".csv"

#     apath = f"../{cfg['institution']}/{cfg['instructor']}/{cfg['schedule']}/results/data/analysis/"
#     os.makedirs(apath, exist_ok=True)
#     datafile = apath + file_name
#     # df = pd.read_csv(datafile, index_col=0)
#     # param_value = df[cfg['team_names'][team_number]]
#     df = pd.read_csv(datafile)
#     print("costs=",c)
#     logging.info(cfg["team_names"][team_number])
#     print("Team:", cfg["team_names"][team_number])
#     print("Kosten: %4.0f Euro/Person & Jahr",  c)
#     print("Kosten: {:.0f}".format(float(df["costs"])), "Euro/Person & Jahr")
#     print("Emissionen: {:.0f}".format(float(df["emissions"])), "kg/Person & Jahr")
#     print("Deckungsgrad: {:.0f}".format(float(df["selfsufficiency"])), "%")
#     if cfg["enable_mobility"]:
#         print("Anteilige Treibstoffkosten: {:.0f}".format(float(df["var_costs_fuel"])), "Euro/Person & Jahr")
#     if cfg["enable_building_retrofit"]:
#         print(
#             "Anteiliege Kosten Gebäudesanierung: {:.0f}".format(float(df["annuity_building_retrofit"])),
#             "Euro/Person & Jahr",
#         )
#     print("__________________________________________________________")


# def store_sequences(config_path, team_number):
#     with open(config_path, encoding="utf-8") as ymlfile:
#         cfg = yaml.load(ymlfile, Loader=yaml.CLoader)

#     logging.info("Store Sequences")

#     abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
#     file_name_param_01 = cfg["design_parameters_file_name"][team_number]
#     # file_name_param_02 = cfg['parameters_file_name']
#     path = f"{abs_path}/{cfg['institution']}/{cfg['instructor']}/{cfg['schedule']}"
#     fpath = path + "/data/"
#     file_path_param_01 = fpath + file_name_param_01
#     # file_path_param_02 = (abs_path + '/data/'+ file_name_param_02)
#     param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
#     # param_df_02 = pd.read_csv(file_path_param_02, index_col=1)
#     # param_df = pd.concat([param_df_01, param_df_02], sort=True)
#     param_value = param_df_01["value"]

#     energysystem = solph.EnergySystem()
#     abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
#     energysystem.restore(
#         dpath=path + "/results/data/dumps", filename="model_team_{}.oemof".format(cfg["team_names"][team_number])
#     )
#     results = energysystem.results["main"]

#     electricity_seq = solph.views.node(results, "electricity")["sequences"]
#     heat_seq = solph.views.node(results, "heat")["sequences"]
#     natural_gas_seq = solph.views.node(results, "natural_gas")["sequences"]
#     sequences_df = pd.merge(electricity_seq, heat_seq, left_index=True, right_index=True)
#     sequences_df = pd.merge(sequences_df, natural_gas_seq, left_index=True, right_index=True)

#     if cfg["enable_mobility"]:
#         fuel_seq = solph.views.node(results, "fuel")["sequences"]
#         sequences_df = pd.merge(sequences_df, fuel_seq, left_index=True, right_index=True)
#         if param_value["percentage_of_bev"] < 100:
#             car_seq = solph.views.node(results, "car")["sequences"]
#             mobility_seq = solph.views.node(results, "mobility")["sequences"]
#             bev_seq = solph.views.node(results, "bev")["sequences"]
#             mobility_bev_seq = solph.views.node(results, "mobility_bev")["sequences"]
#             sequences_df = pd.merge(sequences_df, car_seq, left_index=True, right_index=True)
#             sequences_df = pd.merge(sequences_df, mobility_seq, left_index=True, right_index=True)
#             sequences_df = pd.merge(sequences_df, bev_seq, left_index=True, right_index=True)
#             sequences_df = pd.merge(sequences_df, mobility_bev_seq, left_index=True, right_index=True)

#     spath = f"../{cfg['institution']}/{cfg['instructor']}/{cfg['schedule']}/results/data/sequences"
#     os.makedirs(spath, exist_ok=True)
#     sequences_df.to_csv(f"{spath}/team_{cfg['team_names'][team_number]}_sequences.csv", header=True)
