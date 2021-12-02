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

1.	Download and install Anaconda Navigator: https://www.anaconda.com/products/individual
2.	Open Anaconda Navigator
3.	Create new environment for python 3.7
4.	Activate your environment
5.	Open Terminal in your environment
6.	Install oemof.solph: https://oemof-solph.readthedocs.io/en/latest/readme.html#installation
7.	Download and install Solver 'cbc' für Python 3.7: https://oemof-solph.readthedocs.io/en/latest/readme.html#installing-a-solver
8.	Download energy-system-planning-workshop (Planspiel) from this repository and store all files with the given folder structure on your harddrive in a defined project-foler
9.	In Terminal Window: Navigate to the project-foler
10.	Install all required packages using the command “pip install –r requirements.txt”

# Operation
The following steps are recommended to run the energy-system-planning-workshop on a Windows PC.

1.	Define calculation setup in the file “config.yml” in the folder “experiment_config” using a standard editor.
2.	Define boundary conditions for the optimization by adapting data in file “parameters_Team_XX” (XX for Team numbers 01-08) in folder “data”.
3.	Open Anaconda Navigator
4.	Activate environment which was created in the installation process
5.	Open Terminal in this environment
6.	Navigate to folder src in the Terminal Window
7.	Start optimization in Terminal Window with: “python main.py”
8.	Wait computation to finish in Terminal Window
9.	Analyse results in folder “results”

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
