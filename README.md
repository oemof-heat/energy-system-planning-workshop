# Workshop
In this simulation game you can create and evaluate a new energy system for electricity and heat supply for a imaginary German town with 10000 inhabitants. Choose from technical options such as wind, solar thermal, photovoltaics, heat pumps and conventional technologies as well as energy storages. You avoid shortages, watch costs and CO2-emissions. oemof is used to optimize the operation of each team's energy system during one typical calender year.  

With this simulation game several targets can be addressed: learn technical challanges in energy transition, apply knowledge in fundamentals of energy technology and physics, discuss options for climate protection, understand oemof and optimization problems, involve people and teams.

The game generally works with a trainer and a group of approx. 15-35 participants. All necessary material can be downloaded here. Own adaptations are possible. It is strongly recommended to set up and test the oemof computation before the game.

# Subfolder-Structure
This repository includes the subdirectories with the following contents:

data: all data to run the calculations including data description (meta-data)

experiment_config: file to control the calculation process

presentation: material to present the workshop content, given data, boundary condition and technical options

results: calculation results

src: python sources

# Installation
The following steps are recommended to install the energy-system-planning-workshop on a Windows PC.

1.	Download and install Miniconda: https://docs.anaconda.com/miniconda/miniconda-install/
2.	Download energy-system-planning-workshop (Planspiel) from this Github-repository and store all files with the given folder structure on your harddrive in a defined project-folder
3.	Open a Miniconda Terminal Window and navigate to the projekt-folder
4.	Create a new environment ("planspiel") for python 3.8 with the command: conda create -n "planspiel" python=3.8
5.	Activate the environment with the command: conda activate planspiel
6.	Install all required packages using the command: pip install –r requirements.txt
7.	Download and install Solver 'cbc' für Python 3.8: https://oemof-solph.readthedocs.io/en/latest/readme.html#installing-a-solver


# Operation
The following steps are recommended to run the energy-system-planning-workshop on a Windows PC.

1.	Define calculation setup in the file “config.yml” in the folder “experiment_config” using a standard editor.
2.	Define boundary conditions for the optimization by adapting data in file “parameters_Team_XX” (XX for Team numbers 01-08) in folder “data”.
3.	Open a Miniconda Terminal Window and navigate to the projekt-folder (defined in the installation process)
4.	Activate the environment which was created in the installation process with the command: conda activate planspiel
5.	Navigate in the Terminal Window to the folder "src" 
6.	Start optimization in Terminal Window with: “python main.py”
7.	Wait computation to finish in Terminal Window
8.	Find and analyse results in folder “results”

# Contact
christoph.pels-leusden(at)bht-berlin.de

# License
Copyright (C) 2021 Berliner Hochschule für Technik

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see http://www.gnu.org/licenses/.
