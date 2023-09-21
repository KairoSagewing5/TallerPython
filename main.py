# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 11:23:47 2023

@author: kairo
"""

#%% DEPENDENCIAS

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
                                               NavigationToolbar2Tk)

from cartopy import crs as ccrs
import cartopy.io.shapereader as shpreader

import pandas as pd
import time
#import tkinter as tk
import PySimpleGUI as sg

from functools import lru_cache


#%% OBTENCION DE LA BASE DE DATOS


def get_dataframe(states: list[int], year : int = 2014) -> pd.DataFrame:
    
    df = pd.DataFrame()
    try:
        for i in states:
            if not isinstance(i, int):
                raise TypeError
        if (year > 2022 or year < 2010):
            raise ValueError
    except TypeError:
        print("el argumento states de la función get_dataframe debe contener solo int")
        
    else:

        df = request_url_crashAPI(states[0], year)
        for i in states[1:]:
            df = pd.concat([df,request_url_crashAPI(i, year)])
    return df


@lru_cache(maxsize = 60)
def request_url_crashAPI(state: int, year : int = 2014) -> pd.DataFrame:
    try:
        if not isinstance(state, int):
            raise TypeError
        if (year > 2022 or year < 2010):
            raise ValueError
    except TypeError:
        print("El argumento states de la función get_dataframe debe contener solo int")
    except ValueError:
        print("El argumento year de la función get_dataframe debe ser un entero entre 2011 y 2022 ambos inclusive")
    else:
        return pd.read_csv("https://crashviewer.nhtsa.dot.gov/CrashAPI/crashes/GetCaseList?states=" +
                           str(state) + 
                           "&fromYear=" + 
                           str(year) + 
                           "&toYear=" + 
                           str(year) + 
                           "&minNumOfVehicles=1&maxNumOfVehicles=6&format=csv"
                           )

#%% PREPROCESADO DE LA BASE DE DATOS

def preprocess(df : pd.DataFrame) -> pd.DataFrame:
    """
        Transforma un dataframe de pandas obtenido en Crash API 
        que contiene una fecha tipo "dd/mm/yyyy hh:mm AM" en un nuevo dataframe
        con la fecha en formato iso y elimina datos irrelvantes
    """
    
    # Transformar fechas + horas de string a (year, month, day) como ints
    
    df["crashdate"] = df["crashdate"].apply(lambda x: x.split(" ")[0])
    df["year"] = df["crashdate"].apply(lambda x: x.split("/")[2])
    df["month"] = df["crashdate"].apply(lambda x: x.split("/")[1])
    df["day"] = df["crashdate"].apply(lambda x: x.split("/")[0])
    
    # Eliminar datos sin relevancia
    
    df.pop("st_case")
    df.pop("countyname")
    df.pop("state")
    df.pop("crashdate")
    
    # De momento, eliminar datos relevantes
    
    df.pop("totalvehicles")
    df.pop("fatals")
    df.pop("peds")
    df.pop("persons")

    return df


#%% LLAMADA A LA API


clock = time.time()

state_list = list(range(1,52))
#df = get_dataframe(state_list)
df = get_dataframe([1,2,3,4,5,6])


df = preprocess(df)

clock = time.time() - clock
print(clock)



df["accidents"] = 1 


grouped_df = df.groupby("statename")
count_of_accidents = pd.DataFrame(grouped_df["accidents"].count())

"""
print(count_of_accidents.idxmax()["accidents"])
print(count_of_accidents.idxmin()["accidents"])

print(count_of_accidents.loc[count_of_accidents.index == 
                             count_of_accidents.idxmax()["accidents"]]["accidents"].iloc[0]
      )
print(count_of_accidents.loc[count_of_accidents.index == 
                             count_of_accidents.idxmin()["accidents"]]["accidents"].iloc[0]
      )
"""



#%% CONFIGURACION DE LA VENTANA

"""
window = tk.Tk()

window.title('Accidents')

window.geometry("1000x500")
"""

#%% DIBUJADO DEL MAPA


def plot():

    fig = Figure(figsize = (5, 5), dpi = 100) # Tamaño de la imagen


    ax = fig.add_axes([0, 0, 1, 1], projection=ccrs.LambertConformal(),
                      frameon=False)
    ax.patch.set_visible(False)
    
    ax.set_extent([-125, -66.5, 20, 50], ccrs.Geodetic()) # Tipo de mapa
    
    shapename = 'admin_1_states_provinces_lakes' # Mapa de Estados Unidos por cada estado
    states_shp = shpreader.natural_earth(resolution='110m',
                                         category='cultural', name=shapename)
    
    
    ax.set_title('Accidents') # Nombre de la imagen
    
    
    # Maximo, minimo y mediana de la distribucion de accientes
    accidents_max = count_of_accidents.loc[
        count_of_accidents.index == count_of_accidents.idxmax()["accidents"]
        ]["accidents"].iloc[0]
    
    accidents_min = count_of_accidents.loc[
        count_of_accidents.index == count_of_accidents.idxmin()["accidents"]
        ]["accidents"].iloc[0]
    
    median = count_of_accidents.median()["accidents"]
    
    
    #Coloreado de cada estado segun el numero de accidentes
    for astate in shpreader.Reader(states_shp).records():
    
        edgecolor = 'black'
    
        try:
            state_accs = count_of_accidents.loc[count_of_accidents.index == astate.attributes['name']]["accidents"].iloc[0]
        except:
            state_accs = 0
    
        # Colocar 5 rangos segun el max y el min de todos ellos
        
        if state_accs == 0:
            facecolor = "white"
        elif state_accs <= accidents_min + (median - accidents_min) * 1/3:
            facecolor = "lightyellow"
        elif state_accs <= accidents_min + (median - accidents_min) * 2/3:
            facecolor = "gold"
        elif state_accs <= median:
            facecolor = "orange"
        elif state_accs <= median + (accidents_max - median) * 1/3:
            facecolor = "red"
        elif state_accs <= median + (accidents_max - median) * 2/3:
            facecolor = "firebrick"
        else:
            facecolor = "darkred"
      
        
        """
        if state_accs == 0:
            facecolor = (0.9,0.9,0.5)
        else:
            facecolor = ( (state_accs - accidents_min) / (accidents_max - accidents_min),
                         0.8 - (state_accs - accidents_min) / (accidents_max - accidents_min) * 0.8,
                         0
                         )
        """
    
        # coloreado
        
        ax.add_geometries([astate.geometry], ccrs.PlateCarree(),
                          facecolor=facecolor, edgecolor=edgecolor)
    

"""
    # Colocado de la imagen en la ventada de Tkinter

    canvas = FigureCanvasTkAgg(fig,
                               master = window)  
    canvas.draw()

    canvas.get_tk_widget().pack()
  
    # Permitir navegacion

    toolbar = NavigationToolbar2Tk(canvas,
                                   window)
    toolbar.update()
  
    canvas.get_tk_widget().pack()



# Widget de entrada de request

label = tk.Label(text = "Año (Entre 2011 y 2022)")
entry = tk.Entry()
entry.pack()



# Widget de dibujado

plot_button = tk.Button(master = window, 
                        command = plot,
                        height = 2, 
                        width = 10,
                        text = "2014")
  
plot_button.pack()
  

# Correr la ventana
window.mainloop()
"""

def make_window(theme):
    sg.theme(theme)
    menu_def = [['&Application', ['E&xit']],
                ['&Help', ['&About']] ]
    right_click_menu_def = [[], ['Edit Me', 'Versions', 'Nothing','More Nothing','Exit']]
    graph_right_click_menu_def = [[], ['Erase','Draw Line', 'Draw',['Circle', 'Rectangle', 'Image'], 'Exit']]

    # Table Data
    data = [["John", 10], ["Jen", 5]]
    headings = ["Name", "Score"]

    input_layout =  [

                # [sg.Menu(menu_def, key='-MENU-')],
                [sg.Text('Anything that requires user-input is in this tab!')], 
                [sg.Input(key='-INPUT-')],
                [sg.Slider(orientation='h', key='-SKIDER-'),
                 sg.Image(data=sg.DEFAULT_BASE64_LOADING_GIF, enable_events=True, key='-GIF-IMAGE-'),],
                [sg.Checkbox('Checkbox', default=True, k='-CB-')],
                [sg.Radio('Radio1', "RadioDemo", default=True, size=(10,1), k='-R1-'), sg.Radio('Radio2', "RadioDemo", default=True, size=(10,1), k='-R2-')],
                [sg.Combo(values=('Combo 1', 'Combo 2', 'Combo 3'), default_value='Combo 1', readonly=False, k='-COMBO-'),
                 sg.OptionMenu(values=('Option 1', 'Option 2', 'Option 3'),  k='-OPTION MENU-'),],
                [sg.Spin([i for i in range(1,11)], initial_value=10, k='-SPIN-'), sg.Text('Spin')],
                [sg.Multiline('Demo of a Multi-Line Text Element!\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nYou get the point.', size=(45,5), expand_x=True, expand_y=True, k='-MLINE-')],
                [sg.Button('Button'), sg.Button('Popup'), sg.Button(image_data=sg.DEFAULT_BASE64_ICON, key='-LOGO-')]]

    asthetic_layout = [[sg.T('Anything that you would use for asthetics is in this tab!')],
               [sg.Image(data=sg.DEFAULT_BASE64_ICON,  k='-IMAGE-')],
               [sg.ProgressBar(100, orientation='h', size=(20, 20), key='-PROGRESS BAR-'), sg.Button('Test Progress bar')]]

    logging_layout = [[sg.Text("Anything printed will display here!")],
                      [sg.Multiline(size=(60,15), font='Courier 8', expand_x=True, expand_y=True, write_only=True,
                                    reroute_stdout=True, reroute_stderr=True, echo_stdout_stderr=True, autoscroll=True, auto_refresh=True)]
                      # [sg.Output(size=(60,15), font='Courier 8', expand_x=True, expand_y=True)]
                      ]
    
    graphing_layout = [[sg.Text("Anything you would use to graph will display here!")],
                      [sg.Graph((200,200), (0,0),(200,200),background_color="black", key='-GRAPH-', enable_events=True,
                                right_click_menu=graph_right_click_menu_def)],
                      [sg.T('Click anywhere on graph to draw a circle')],
                      [sg.Table(values=data, headings=headings, max_col_width=25,
                                background_color='black',
                                auto_size_columns=True,
                                display_row_numbers=True,
                                justification='right',
                                num_rows=2,
                                alternating_row_color='black',
                                key='-TABLE-',
                                row_height=25)]]

    popup_layout = [[sg.Text("Popup Testing")],
                    [sg.Button("Open Folder")],
                    [sg.Button("Open File")]]
    
    theme_layout = [[sg.Text("See how elements look under different themes by choosing a different theme here!")],
                    [sg.Listbox(values = sg.theme_list(), 
                      size =(20, 12), 
                      key ='-THEME LISTBOX-',
                      enable_events = True)],
                      [sg.Button("Set Theme")]]
    
    layout = [ [sg.MenubarCustom(menu_def, key='-MENU-', font='Courier 15', tearoff=True)],
                [sg.Text('Demo Of (Almost) All Elements', size=(38, 1), justification='center', font=("Helvetica", 16), relief=sg.RELIEF_RIDGE, k='-TEXT HEADING-', enable_events=True)]]
    layout +=[[sg.TabGroup([[  sg.Tab('Input Elements', input_layout),
                               sg.Tab('Asthetic Elements', asthetic_layout),
                               sg.Tab('Graphing', graphing_layout),
                               sg.Tab('Popups', popup_layout),
                               sg.Tab('Theming', theme_layout),
                               sg.Tab('Output', logging_layout)]], key='-TAB GROUP-', expand_x=True, expand_y=True),

               ]]
    layout[-1].append(sg.Sizegrip())
    window = sg.Window('All Elements Demo', layout, right_click_menu=right_click_menu_def, right_click_menu_tearoff=True, grab_anywhere=True, resizable=True, margins=(0,0), use_custom_titlebar=True, finalize=True, keep_on_top=True)
    window.set_min_size(window.size)
    return window

def main():
    window = make_window(sg.theme())

    # This is an Event Loop 
    while True:
        event, values = window.read(timeout=100)
        # keep an animation running so show things are happening
        if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
            print('============ Event = ', event, ' ==============')
            print('-------- Values Dictionary (key=value) --------')
            for key in values:
                print(key, ' = ',values[key])
        if event in (None, 'Exit'):
            print("[LOG] Clicked Exit!")
            break

        window['-GIF-IMAGE-'].update_animation(sg.DEFAULT_BASE64_LOADING_GIF, time_between_frames=100)
        if event == 'About':
            print("[LOG] Clicked About!")
            sg.popup('PySimpleGUI Demo All Elements',
                     'Right click anywhere to see right click menu',
                     'Visit each of the tabs to see available elements',
                     'Output of event and values can be see in Output tab',
                     'The event and values dictionary is printed after every event', keep_on_top=True)
        elif event == 'Popup':
            print("[LOG] Clicked Popup Button!")
            sg.popup("You pressed a button!", keep_on_top=True)
            print("[LOG] Dismissing Popup!")
        elif event == 'Test Progress bar':
            print("[LOG] Clicked Test Progress Bar!")
            progress_bar = window['-PROGRESS BAR-']
            for i in range(100):
                print("[LOG] Updating progress bar by 1 step ("+str(i)+")")
                progress_bar.update(current_count=i + 1)
            print("[LOG] Progress bar complete!")
        elif event == "-GRAPH-":
            graph = window['-GRAPH-']       # type: sg.Graph
            graph.draw_circle(values['-GRAPH-'], fill_color='yellow', radius=20)
            print("[LOG] Circle drawn at: " + str(values['-GRAPH-']))
        elif event == "Open Folder":
            print("[LOG] Clicked Open Folder!")
            folder_or_file = sg.popup_get_folder('Choose your folder', keep_on_top=True)
            sg.popup("You chose: " + str(folder_or_file), keep_on_top=True)
            print("[LOG] User chose folder: " + str(folder_or_file))
        elif event == "Open File":
            print("[LOG] Clicked Open File!")
            folder_or_file = sg.popup_get_file('Choose your file', keep_on_top=True)
            sg.popup("You chose: " + str(folder_or_file), keep_on_top=True)
            print("[LOG] User chose file: " + str(folder_or_file))
        elif event == "Set Theme":
            print("[LOG] Clicked Set Theme!")
            theme_chosen = values['-THEME LISTBOX-'][0]
            print("[LOG] User Chose Theme: " + str(theme_chosen))
            window.close()
            window = make_window(theme_chosen)
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == 'Versions':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True)

    window.close()
    exit(0)

if __name__ == '__main__':
    sg.theme('black')
    sg.theme('dark red')
    sg.theme('dark green 7')
    # sg.theme('DefaultNoMoreNagging')
    main()