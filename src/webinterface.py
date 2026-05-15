import streamlit as st
import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime
import os
import sys
from model_energy_system import run_model
import logging
import yaml
from oemof.tools import logger
from detailed_analysis_web import analyse_energy_system
#from detailed_analysis import store_sequences
#from graphic_analysis import pie_charts
#from graphic_analysis import plot_team_results

#Session-Settings
if "number_of_teams" not in st.session_state:
    st.session_state.number_of_teams = 1
teamcodes = {
    "Team": ["1", "2", "3", "4", "5", "6", "7", "8"] ,
    "Code": ["Wedding", "Tegel", "Kreuzberg", "Pankow", "Treptow", "Spandau", "Frohnau", "Steglitz"],
    "Data Status": ["Waiting for Data","Waiting for Data","Waiting for Data","Waiting for Data","Waiting for Data","Waiting for Data","Waiting for Data","Waiting for Data"]
    }
if "teamcodes_df" not in st.session_state:
    st.session_state.teamcodes_df = pd.DataFrame(teamcodes)
if 'teamcodes_complete' not in st.session_state:
    st.session_state.teamcodes_complete = False
if 'dataentry_complete' not in st.session_state:
    st.session_state.dataentry_complete = False            
if 'calculation_complete' not in st.session_state:
    st.session_state.calculation_complete = False            

def check_password():
    def password_entered():
        if st.session_state["password"] == "planspiel":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Passwort nicht im State speichern
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        # First Input
        st.text_input("Passwort eingeben", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Wrong Password
        st.text_input("Passwort eingeben", type="password", on_change=password_entered, key="password")
        st.error("😕 Passwort falsch")
        return False
    else:
        # Password correct
        return True

def main_page():
    st.set_page_config(layout="wide")
    st.title("Energie für (m)eine Stadt - Eingabe und Start der Rechnung")

    data = {
        "Parameter": ["Anzahl Windkraftanlagen", "Anzahl Blockheizkraftwerke", "Anzahl Gaskessel", "Anzahl Wärmepumpen"],
        "Anzahl": [0, 0, 0, 0],
        "Minimum": [0, 0, 0, 0],
        "Maximum": [10, 10, 10, 10],
    }
    df_entry = pd.DataFrame(data)

    #File-Management
    ordner = Path("../data")
    dateiname = "parameters_Team_00.csv"
    inputfile = ordner / dateiname
    df = pd.read_csv(inputfile, index_col="id")
    if "master_df" not in st.session_state:
        st.session_state.master_df = df.copy()

    #Data-Input
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tabellarische Eingabe")
        df_edit = st.data_editor(
            df_entry,
            column_config={
                "id":None,
                "Parameter": st.column_config.Column(
                    "Parameter",
                    help="Parameterbezeichnung",
                    disabled=True,
                ),
                "Anzahl": st.column_config.NumberColumn(
                    "Anzahl",
                    help="Hier Wert eingeben",
                    disabled=False,
                    min_value=0,
                    max_value=10,
                    step=1.0,
                    format="%.1f"
                ),
                "Minimum": st.column_config.Column(
                    "Minimum",
                    help="kleinste Anzahl",
                    disabled=True,
                ),
                "Maximum": st.column_config.Column(
                    "Maximum",
                    help="größte Anzahl",
                    disabled=True,
                ),
            },
            hide_index = True
        )
        st.session_state.master_df.iloc[0,1] = df_edit.iloc[0,1] #WKA
        st.session_state.master_df.iloc[1,1] = df_edit.iloc[1,1] #BHKW
        st.session_state.master_df.iloc[2,1] = df_edit.iloc[2,1] #Boiler
        st.session_state.master_df.iloc[4,1] = df_edit.iloc[3,1] #WP

    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Freifläche für Photovoltaik")
        pvpp_data = {1: "Ja", 2: "Nein"}
        selected_user_id = st.radio(
                "Soll eine PV-Freiflächenanlage vorgesehen werden?",
                options=pvpp_data.keys(),
                horizontal=True,
                format_func=lambda x: pvpp_data[x] # Zeigt Namen an, gibt ID zurück
                )
        if selected_user_id == 1:
            st.session_state.master_df.iloc[3,1] = 1.0 #PVPP
        else:
            st.session_state.master_df.iloc[3,1] = 0.0 #PVPP

    with col2:
        st.subheader("Dimensionierung der Speicher")
        batterysize_data = {1: "0", 2: "1/4", 3: "1/2", 4: "1", 5: "2", 6: "7"}
        batterysize_value = {1: 0.0, 2: 0.25, 3: 0.5, 4: 1.0, 5: 2.0, 6: 7.0}
        heatstoragesize_data = {1: "0", 2: "1/4", 3: "1/2", 4: "1", 5: "2", 6: "7", 7:"30", 8:"90" }
        heatstoragesize_value = {1: 0.0, 2: 0.25, 3: 0.5, 4: 1.0, 5: 2.0, 6: 7.0, 7: 30.0, 8: 90.0 }
        selected_user_id = st.radio(
                "Wie groß soll die Batterie sein (gemessen in mittelerem Tagesbedarf)",
                options=batterysize_data.keys(),
                horizontal=True,
                format_func=lambda x: batterysize_data[x] # Zeigt Namen an, gibt ID zurück
                )
        st.session_state.master_df.iloc[7,1] = batterysize_value[selected_user_id]
        selected_user_id = st.radio(
                "Wie groß soll der Wärmespeicher sein (gemessen in mittelerem Tagesbedarf)",
                options=heatstoragesize_data.keys(),
                horizontal=True,
                format_func=lambda x: heatstoragesize_data[x] # Zeigt Namen an, gibt ID zurück
                )
        st.session_state.master_df.iloc[8,1] = heatstoragesize_value[selected_user_id]

    with col3:
        st.subheader("Nutzung der Dachflächen: max. 80.000 m2 = 8 ha")
        if "val_pv" not in st.session_state:
            st.session_state.val_pv = 33
            st.session_state.val_th = 33
        def update_pv():
            # If ST is changed, PV is adjusted
            if st.session_state.val_pv + st.session_state.val_th > 100:
                st.session_state.val_pv = 100 - st.session_state.val_th
        def update_th():
            # If PV is changed, ST is adjusted
            if st.session_state.val_pv + st.session_state.val_th > 100:
                st.session_state.val_th = 100 - st.session_state.val_pv
        val_pv = st.slider("Phtovotaik", 0, 100, key="val_pv", on_change=update_th)
        val_th = st.slider("Solarthermie", 0, 100, key="val_th", on_change=update_pv)
        val_notused = 100 - val_pv - val_th
        st.progress(val_notused / 100, text=f"Ungenutzt: {val_notused}%")
        st.session_state.master_df.iloc[5,1] = 8.0 * 0.01* val_pv #PV
        st.session_state.master_df.iloc[6,1] = 8.0 * 0.01* val_th #PV

    #Speicherung
    if "teamcodes_df" in st.session_state:
        st.divider()
        col1, col2 = st.columns(2)
        with col1: 
            st.subheader("Teamauswahl")
            teams = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6", "Team 7", "Team 8"]
            selection = st.selectbox("Bitte wähle ein Team für die Dateneingabe aus:", teams, index = 0)
            selected_team = teams.index(selection) + 1
            code = st.text_input("Gib des passenden Code für das Team an:", placeholder="Code")
        with col2:
            st.markdown("<div style='margin-top: 100px;'></div>", unsafe_allow_html=True)
            if st.session_state.teamcodes_complete:
                if st.button("Speichern"):
                    if st.session_state.teamcodes_df.iloc[selected_team-1,1] == code:
                        code = "Code"
                        filename = "parameters_Team_0" + str(selected_team) + ".csv"
                        outputfile = ordner / filename
                        dfnew = st.session_state.master_df.copy()
                        dfnew.to_csv(outputfile)
                        st.success("Daten wurden gespeichert.")
                        st.session_state.teamcodes_df.iloc[selected_team-1,2] = "Data completed"
                        #zurücksetzen
                        df_edit.iloc[0,1] = 0
                    else:
                        st.error("Sorry! Der Code passt nicht.")
        #st.divider()
        #if st.button("Load new page"):
        #    st.rerun()


def admin():
    st.set_page_config(layout="centered")
    st.title("Admin-Bereich")
    if check_password():
        st.success("Eingeloggt!")
        if st.button("Abmelden"):
            del st.session_state["password_correct"] 
            st.rerun() # Seite neu laden, um die Sperre zu aktivieren
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Schritt 1: Teams einteilen")
            st.subheader("Wie viele Teams sollen berechnet werden?")
            numofteams_data = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",}
            # Initialize
            if 'teamnumberfix' not in st.session_state:
                st.session_state.teamnumberfix = False
            if not st.session_state.teamnumberfix:
                numofteams_edit = st.radio(
                    "",
                    options=numofteams_data.keys(),
                    index=st.session_state.number_of_teams-1,
                    horizontal=True,
                    format_func=lambda x: numofteams_data[x] # Zeigt Namen an, gibt ID zurück
                )
                # Frist Button
                if st.button("Auswahl"):
                    st.session_state.teamnumberfix = True
                    st.session_state.number_of_teams = numofteams_edit
                    #print(numofteams_edit)
                    #print(st.session_state.number_of_teams)
                    st.rerun() # Seite neu laden, um den Button sofort zu ändern
            else:
                if st.button("Reset"):
                    st.session_state.teamnumberfix = False
                    st.session_state.teamcodes_complete = False
                    st.session_state.teamcodes_df = pd.DataFrame(teamcodes)
                    st.session_state.dataentry_complete = False
                    st.session_state.calculation_complete = False
                    st.rerun()
            if st.session_state.teamnumberfix == True and st.session_state.teamcodes_complete == False:      
                st.subheader("")
                st.subheader("Bitte gib jedem Team einen Code für die Dateneingabe:")
                teamcodes_entry = st.session_state.teamcodes_df
                teamcodes_edit = st.data_editor(
                        teamcodes_entry.iloc[0:st.session_state.number_of_teams],
                        column_config={
                            "id":None,
                            "Team": st.column_config.Column(
                                "Team",
                                help="Teamnummer",
                                disabled=True,
                            ),
                            "Code": st.column_config.Column(
                                "Code",
                                help="Geben Sie hier einen individuellen Code für jedes Team an.",
                                disabled=False,
                            ),
                            "Data Status":None,
                        },
                        hide_index = True
                    )
                if st.button("Bestätigen"):
                    st.session_state.teamcodes_complete = True
                    st.session_state.teamcodes_df=teamcodes_edit
                    st.rerun()
        with col2:
            if st.session_state.teamcodes_complete == True:      
                #st.divider()
                st.subheader("Schritt 2: Dateneingabe")
                #if "teamcodes_df" in st.session_state:
                if st.session_state.teamcodes_complete:
                    st.dataframe(st.session_state.teamcodes_df.iloc[0:st.session_state.number_of_teams],
                        hide_index=True)
                infofeld = st.empty()
                infofeld.warning("Dateneingabe läuft")
                if st.button("Zur Dateneingabe"):
                    st.switch_page(data_page)
                auswahl = st.session_state.teamcodes_df['Data Status'].head(st.session_state.number_of_teams)
                if (auswahl == "Data completed").all():
                    infofeld.success("Dateneingabe für alle Teams abgeschlossen.")
                    st.session_state.dataentry_complete = True

        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            if st.session_state.dataentry_complete == True:      
                #Start Caculation
                st.subheader("Schritt 3: Berechnung starten")
                if st.button("Run"):
                    warning_placeholder = st.empty()
                    warning_placeholder.warning("Berechnung läuft")
                    exp_cfg_file_name = "config.yml"
                    config_file_path = os.path.abspath("../experiment_config/" + exp_cfg_file_name)
                    with open(config_file_path, encoding="utf-8") as ymlfile:
                        cfg = yaml.load(ymlfile, Loader=yaml.CLoader)
                    logger.define_logging(logfile="main.log", screen_level=logging.INFO, file_level=logging.INFO)
                    logging.info("main.py started")
                    if cfg["run_model"]:
                        logging.info("run_model")
                        for n in range(st.session_state.number_of_teams):
                            run_model(config_path=config_file_path, team_number=n)

                    logging.info("Run detailed analysis.")
                    ordnersummary = Path("../results/summary")
                    #exp_cfg_file_name = "config.yml"
                    #config_file_path = os.path.abspath("../experiment_config/" + exp_cfg_file_name)
                    for n in range(st.session_state.number_of_teams):
                        teamdata, teamdata_as_table = analyse_energy_system(config_path=config_file_path, team_number=n)
                        apath = f"../results/data/analysis/"
                        os.makedirs(apath, exist_ok=True)
                        filename="teamdata_" + str(n+1) + ".csv"
                        teamdata.to_csv(f"{apath}{filename}")
                        if n == 0:
                            df_teamdata = teamdata
                            df_teamdata_table = teamdata_as_table
                        else:
                            df_teamdata_aux = teamdata
                            df_teamdata_table_aux = teamdata_as_table
                            df_teamdata = pd.concat([df_teamdata, df_teamdata_aux])
                            df_teamdata_table = pd.concat([df_teamdata_table, df_teamdata_table_aux], axis=1)
                    resultfile = ordnersummary / "results.csv"
                    resulttable = ordnersummary / "results_table.csv"
                    df_teamdata.to_csv(resultfile)
                    df_teamdata_table.to_csv(resulttable)
                    # if cfg["plot_team_results"] & cfg["run_detailed_analysis"]:
                    #     plot_team_results(config_path=config_file_path, df_teamdata=df_teamdata)
                    # if cfg["enable_analysing_sequences"]:
                    #     for n in range(st.session_state.number_of_teams):
                    #         store_sequences(config_path=config_file_path, team_number=n)
                    # if cfg["enable_pie_charts"]:
                    #     for n in range(st.session_state.number_of_teams):
                    #         pie_charts(config_path=config_file_path, team_number=n)
                    st.session_state.calculation_complete = True
                    warning_placeholder.success("Berechnung abgeschlossen")
        with col4:
            #Results Evaluation 
            if st.session_state.calculation_complete:
                st.subheader("Schritt 4: Ergebnisse auswerten")
                if st.button("Zur Auswertung"):
                    st.switch_page(analysis_page)
                st.divider()
                # st.subheader("Schritt 5: Ergebnisse Speichern")
                # if st.button("Ergebnisse speichern"):
                #     quelle = Path("../data")
                #     jetzt = datetime.now()
                #     zielname = "../backup/data_" + str(jetzt)
                #     ziel = Path(zielname)
                #     shutil.copytree(quelle, ziel)
                #     st.session_state.teamnumberfix = False
                #     st.session_state.teamcodes_complete = False
                #     st.session_state.teamcodes_df = pd.DataFrame(teamcodes)
                #     st.session_state.dataentry_complete = False
                #     st.session_state.calculation_complete = False
                #     st.rerun()
                # if st.button("Ende ohne Speichern"):
                #     st.session_state.teamnumberfix = False
                #     st.session_state.teamcodes_complete = False
                #     st.session_state.teamcodes_df = pd.DataFrame(teamcodes)
                #     st.session_state.dataentry_complete = False
                #     st.session_state.calculation_complete = False
                #     st.rerun()

def analysis_global():
    st.set_page_config(layout="centered")
    st.title("Übersicht aller Teams")

    st.divider()
    st.subheader("Globale Ergebnisse")
    ordnersummary = Path("../results/summary")
    resulttable = ordnersummary / "results_table.csv"
    df_teamdata_table = pd.read_csv(resulttable)
    df_teamdata_table.columns.values[0] = "Parameter"
    if st.session_state.calculation_complete:
        #xychartfile = ordnersummary / "results_with_team_names.png"
        #st.image(xychartfile)
        
        st.dataframe(df_teamdata_table.iloc[0:3],
            hide_index=True)

        st.subheader("Teamentscheidungen")
        st.dataframe(df_teamdata_table.iloc[4:13],
            hide_index=True,
            height = (13-4+1)*35+3)

        st.subheader("Elektrische Energieflüsse in kWh pro Person und Jahr")
        st.dataframe(df_teamdata_table.iloc[15:25],
            hide_index=True,
            height = (25-15+1)*35+3)

        st.subheader("Thermische Energieflüsse in kWh pro Person und Jahr")
        st.dataframe(df_teamdata_table.iloc[24:31],
            hide_index=True,
            height = (31-24+1)*35+3)

        st.subheader("Speichernutzung")
        st.dataframe(df_teamdata_table.iloc[35:37],
            hide_index=True,
            height = (37-35+1)*35+3)

        st.subheader("Emissionen")
        st.dataframe(df_teamdata_table.iloc[41:45],
            hide_index=True,
            height = (45-41+1)*35+3)

        st.subheader("Investionskosten")
        st.dataframe(df_teamdata_table.iloc[47:56],
            hide_index=True,
            height = (56-47+1)*35+3)

        st.subheader("Betriebskosten")
        st.dataframe(df_teamdata_table.iloc[57:61],
            hide_index=True,
            height = (61-57+1)*35+3)

        st.divider()
        if st.button("Team Ergebnisse"):
            st.switch_page(analysis_page_team)



def analysis_individual():
    st.set_page_config(layout="wide")
    st.title("Teamergebnisse")
    if "number_of_teams" in st.session_state:
        numofteams=st.session_state.number_of_teams
    numofteams_data = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",}
    numofteamshown = st.radio(
            "Welches Team sollen gezeigt werden?",
            options=numofteams_data.keys(),
            horizontal=True,
            format_func=lambda x: numofteams_data[x] # Zeigt Namen an, gibt ID zurück
            )
    st.write(f"Der gewählte Wert ist: **{numofteamshown}**")
    st.write(f"Verfügbare Temas: **{numofteams}**")
    
    if st.session_state.calculation_complete:
        if st.button("Select"):
            if numofteamshown>numofteams:
                st.error("Sorry es wurden weniger Teams berechnet als hier ausgewählt!")
            else:
                ordner = Path("../results/teams/")
                dateiname = "team_" + str(numofteamshown) + "/PieCharts.png"
                piechartfile = ordner / dateiname
                st.image(piechartfile, caption="Team")
        st.divider()
        if st.button("Globale Ergebnisse"):
            st.switch_page(analysis_page)

admin_page = st.Page(admin, title="Admin", icon="🔒")
data_page = st.Page(main_page, title="Dateneingabe", icon="📲")
analysis_page = st.Page(analysis_global, title="Globale Ergebnisse", icon="📊")
analysis_page_team = st.Page(analysis_individual, title="Team Ergebnisse", icon="📈")

pg = st.navigation([admin_page, data_page, analysis_page, analysis_page_team])
pg.run()

 


