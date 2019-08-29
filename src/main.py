# -*- coding: utf-8 -*-

"""

This program is part of a game-based workshop about energy systems.
During the workshop up to 8 teams design energy systems by selecting and
combining technologies to supply heat and electrical power. Their design
parameter are the simulation input.
This Program calls the energy system simulation (optimization) for
each team and analysis the results based on settings made in
'experimental_config/config.yml'.

Date: 29th of August 2019
Author: Jakob Wolf (jakob.wolf@beuth-hochschule.de)
Licence: GPL-3.0

"""

import os
from model_energy_system import run_model
from basic_analysis import display_results
import yaml

try:
    from detailed_analysis import my_detailed_analysis
except ImportError:
    my_detailed_analysis = None


def main():
    # Choose configuration file to run model with
    exp_cfg_file_name = 'config.yml'
    config_file_path = os.path.abspath(
        '../experiment_config/' + exp_cfg_file_name)
    with open(config_file_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.CLoader)

    # global teamdata
    if cfg['run_model']:
        for n in range(cfg['number_of_teams']):
            run_model(config_path=config_file_path, team_number=n)

    # Basic analysis
    if cfg['display_results']:
        for n in range(cfg['number_of_teams']):
                display_results(config_path=config_file_path, team_number=n)

    if cfg['run_detailed_analysis']:
        my_detailed_analysis(config_file_path=config_file_path)


main()


