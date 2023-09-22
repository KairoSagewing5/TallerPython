# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 11:23:47 2023

@author: kairo
"""

#%% DEPENDENCIAS


# Dibujado de funciones
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches

# Interfaz gráfica
import PySimpleGUI as sg

# Dibujado de mapas cartográficos
from cartopy import crs as ccrs
import cartopy.io.shapereader as shpreader

# Manejo de bases de datos
import pandas as pd

# Control del tiempo de ejecución
import time

# Agilidad para evitar repetir peticiones a la API
from functools import lru_cache


#%% CODIGO DE CADA ESTADO EN LA API DE CRASHAPI


STATE_CODES = {
    "Alabama":1,
    "Alaska":2,
    "Arizona":4,
    "Arkansas":5,
    "California":6,
    "Colorado":8,
    "Connecticut":9,
    "Delaware":10,
    "District of Columbia":11,
    "Florida":12,
    "Georgia":13,
    "Hawaii":15,
    "Idaho":16,
    "Illinois":17,
    "Indiana":18,
    "Iowa":19,
    "Kansas":20,
    "Kentucky":21,
    "Louisiana":22,
    "Maine":23,
    "Maryland":24,
    "Massachusetts":25,
    "Michigan":26,
    "Minnesota":27,
    "Mississippi":28,
    "Missouri":29,
    "Montana":30,
    "Nebraska":31,
    "Nevada":32,
    "New Hampshire":33,
    "New Jersey":34,
    "New Mexico":35,
    "New York":36,
    "North Carolina":37,
    "North Dakota":38,
    "Ohio":39,
    "Oklahoma":40,
    "Oregon":41,
    "Pennsylvania":42,
    "Puerto Rico":43,
    "Rhode Island":44,
    "South Carolina":45,
    "South Dakota":46,
    "Tennessee":47,
    "Texas":48,
    "Utah":49,
    "Vermont":50,
    "Virginia":51,
    "Virgin Islands":52,
    "Washington":53,
    "West Virginia":54,
    "Wisconsin":55,
    "Wyoming":56
}


#%% OBTENCION DE LA BASE DE DATOS


def getDataframe(states: list[int], year : int = 2014, request_together : int = 5) -> pd.DataFrame:
    """
        Obtiene la base de datos de accidentes de CrashAPI
        a partir de una lista de estados (siguiendo el código
        especificado en STATE_CODES)
        
        states : list[int]     -> Lista de estados de los que obtener 
                                    información. Los enteros deben
                                    estar en STATE_CODES
        year : int             -> Año del que obtener información.
                                    Debe estar entre 2010 y 2021
                                    ambos inclusive.
        request_together : int -> Número de estados que pedir juntos
                                    a CrashAPI para reducir tiempo
                                    de espera. Números mayores de
                                    5 pueden provocar pérdida de
                                    información por el límite de
                                    peticiones de la API.
    """
    
    df = pd.DataFrame()
    
    #Comprobar si los datos son del tipo correcto y sus valores con adecuados
    try:
        for i in states:
            if not isinstance(i, int) or i not in list(STATE_CODES.values()):
                raise TypeError
        if not isinstance(year, int):
            raise TypeError
        if (year > 2021 or year < 2010):
            raise ValueError
        if not isinstance(request_together, int):
            raise TypeError
            
    except TypeError:
        print("Los argumentos de la función get_dataframe deben ser una lista de enteros para 'states' y un entero solo para 'year y 'request_together'")
    except ValueError:
        print("El argumento year de la función get_dataframe debe ser un entero entre 2011 y 2022 ambos inclusive")        
    else:
        
        # Procesar la lista de estados en paquetes de tamaño request_together
        processed_str = str()
        
        while states:
            
            # Conversión de lista a string sin espacios ni corchetes
            processed_str = str( states[0:request_together] ).replace(" ", "").removeprefix("[").removesuffix("]")
            states = states[request_together:]
            
            # Llamada a la API y concatenación de los paquetes
            df = pd.concat( [df, requestCrashAPI(processed_str, year)] )

    return df


@lru_cache(maxsize = 60)
def requestCrashAPI(states: str, year : int = 2014) -> pd.DataFrame:
    """
        Obtiene la base de datos de accidentes de CrashAPI
        a para un único estado estados (siguiendo el código
        especificado en STATE_CODES). La base de datos queda
        en caché usando los parámetros como 'key'
        
        states : str           -> Estados del que obtener información.
                                    Debe ser una string con un entero
                                    elegido según STATE_CODES
        year : int             -> Año del que obtener información.
                                    Debe estar entre 2010 y 2021
                                    ambos inclusive.
    """
    try:
        if not isinstance(states, str):
            raise TypeError
        if year > 2021 or year < 2010:
            raise ValueError
            
    except TypeError:
        print("El argumento states de la función get_dataframe debe contener solo int")
    except ValueError:
        print("El argumento year de la función get_dataframe debe ser un entero entre 2011 y 2022 ambos inclusive")
    else:
        
        # Petición a la API según parámetros
        return pd.read_csv("https://crashviewer.nhtsa.dot.gov/CrashAPI/crashes/GetCaseList?states=" + states + 
                           "&fromYear=" + str(year) + "&toYear=" + str(year) + 
                           "&minNumOfVehicles=1&maxNumOfVehicles=6&format=csv"
                           )


#%% PREPROCESADO DE LA BASE DE DATOS


def preprocess(df : pd.DataFrame) -> pd.DataFrame:
    """
        Transforma un dataframe de pandas obtenido de CrashAPI 
        que contiene una fecha tipo "dd/mm/yyyy hh:mm AM" en un nuevo dataframe
        con la fecha en formato iso y eliminando datos irrelevantes
        
        df : pd.Dataframe      -> Dataframe obtenido de CrashAPI.
                                    Se recomienda utilizar get_dataframe().
    """
    
    # Transformar fechas y horas de string a columnas (year, month, day) como enteros
    df["crashdate"] = df["crashdate"].apply(lambda x: x.split(" ")[0])
    df["year"] = df["crashdate"].apply(lambda x: x.split("/")[2])
    df["month"] = df["crashdate"].apply(lambda x: x.split("/")[1])
    df["day"] = df["crashdate"].apply(lambda x: x.split("/")[0])
    
    # Eliminar datos sin relevancia
    df.pop("st_case")
    df.pop("countyname")
    df.pop("state")
    df.pop("crashdate")
    
    # De momento, eliminar datos relevantes que no se van a utilizar
    df.pop("totalvehicles")
    df.pop("fatals")
    df.pop("peds")
    df.pop("persons")

    return df


#%% DIBUJADO DEL MAPA


def groupCountAccidents(df : pd.DataFrame) -> pd.DataFrame:
    """
        Transforma un dataframe de pandas obtenido de CrashAPI en
        otro dataframe que agrupa las observaciones por estado y
        las cuenta.
        (se recomienda preprocesarlo primero con preprocess() )
        
        df : pd.Dataframe      -> Dataframe obtenido de CrashAPI.
                                    Se recomienda utilizar getDataframe()
                                    y luego preprocess().
    """
    
    df["accidents"] = 1 
    grouped_df = df.groupby("statename")
    accident_count = pd.DataFrame(grouped_df["accidents"].count())
    
    
    return accident_count


def plotMapAccidents(accident_count : pd.DataFrame, year : int = None) -> plt.Figure():
    """
        Dibuja el mapa de estados unidos y colorea cada estado
        según rangos de datos:
            - En tercios entre el mínimo y la mediana
            - En sextos entre la mediana y el máximo saltándose
                tercer sexto ya que no suele contener observaciones
        Para obtener la leyenda de los datos, utilizar plotMapAccidentsLeyend()
        
        accident_count : pd.Dataframe -> Dataframe obtenido de CrashAPI, preprocesado, agrupado
                                            por estados y con las observaciones contadas.
                                            Se recomienda utilizar groupCountAccidents().
    """

    # Generación de la imagen vacía    
    fig = plt.figure()
    
    # Elección de ejes cartesianos para el mapa de la Tierra (en vez de un mapa curvado)
    ax = fig.add_axes([0, 0, 1, 1], 
                      projection = ccrs.LambertConformal(),
                      frameon = False)
    
    # Ocultar los ejes 
    ax.patch.set_visible(False)
    
    # Centrar el mapa en Estados Unidos
    ax.set_extent([-125, -66.5, 20, 50], ccrs.Geodetic())
    
    # Obtención de la geografía de cada estado
    shapename = 'admin_1_states_provinces_lakes' 
    states_shp = shpreader.natural_earth(resolution='110m',
                                         category='cultural', name=shapename)
    
    # Título de la imagen
    if year == None:
        ax.set_title('Accidentes de Estados Unidos')
    else:
        ax.set_title('Accidentes de Estados Unidos en ' + str(year))
    
    # Maximo, minimo y mediana de la distribucion de accientes
    accidents_max = accident_count.loc[
        accident_count.index == accident_count.idxmax()["accidents"]
        ]["accidents"].iloc[0]
    
    accidents_min = accident_count.loc[
        accident_count.index == accident_count.idxmin()["accidents"]
        ]["accidents"].iloc[0]
    
    median = accident_count.median()["accidents"]
    
    
    #Coloreado de cada estado segun el numero de accidentes
    for each_state in shpreader.Reader(states_shp).records():
        
        # Bordes de cada estado
        edgecolor = 'black'
        
        # Comprobar que el estado existe y tiene datos
        try:
            state_accidents = accident_count.loc[accident_count.index == each_state.attributes['name']]["accidents"].iloc[0]
        except:
            state_accidents = 0
    
        # Colorear el interior segun rangos dependientes del máximo, el mínimo y la mediana de los datos
        if state_accidents == 0:
            facecolor = "white"
        elif state_accidents <= accidents_min + (median - accidents_min) * 1/3:
            facecolor = "lightyellow"
        elif state_accidents <= accidents_min + (median - accidents_min) * 2/3:
            facecolor = "yellow"
        elif state_accidents <= median:
            facecolor = "gold"
        elif state_accidents <= median + (accidents_max - median) * 1/6:
            facecolor = "orange"
        elif state_accidents <= median + (accidents_max - median) * 2/6:
            facecolor = "xkcd:pumpkin"
        elif state_accidents <= median + (accidents_max - median) * 4/6:
            facecolor = "xkcd:vermillion"
        elif state_accidents <= median + (accidents_max - median) * 5/6:
            facecolor = "xkcd:brownish red"
        else:
            facecolor = "xkcd:dried blood"

        
        # coloreado
        ax.add_geometries([each_state.geometry], 
                          ccrs.PlateCarree(),
                          facecolor = facecolor, 
                          edgecolor = edgecolor)
    
        
    return fig


def plotMapAccidentsLeyend(count_of_accidents : pd.DataFrame, extra_info : bool = True):
    """
        Dibuja la leyenda del mapa generado por plotMapAccidents(),
        generada aparte para no tapar el propio mapa.
        
        accident_count : pd.Dataframe -> Dataframe obtenido de CrashAPI, preprocesado, agrupado
                                            por estados y con las observaciones contadas.
                                            Se recomienda utilizar groupCountAccidents().
        extra_info : bool             -> Por defecto True. Muestra información adicional sobre
                                            los datos por la línea de comandos.
    """
    

    # Maximo, minimo y mediana de la distribucion de accientes
    accidents_max = count_of_accidents.loc[
        count_of_accidents.index == count_of_accidents.idxmax()["accidents"]
        ]["accidents"].iloc[0]
    
    accidents_min = count_of_accidents.loc[
        count_of_accidents.index == count_of_accidents.idxmin()["accidents"]
        ]["accidents"].iloc[0]
    
    median = count_of_accidents.median()["accidents"]
    
    
    # Generación de la imagen vacía  
    fig = plt.figure(figsize = (3.5, 2.1))
    ax = fig.add_axes([0, 0, 1, 1],
                      frameon = True)
    
    # Ocultar los ejes
    ax.patch.set_visible(False)
    
    # Lista de rangos de datos con sus correspondientes colores
    legend_info = [
        mpatches.Patch(color = "white", 
                       label = "Sin datos de accidentes", linestyle = "-"),
        mpatches.Patch(color = "lightyellow", 
                       label = "Entre 0 y " + str(int(accidents_min + (median - accidents_min) * 1/3)) + " accidentes"),
        mpatches.Patch(color = "yellow", 
                       label = "Entre " + str(int(accidents_min + (median - accidents_min) * 1/3))
                              + " y " + str(int(accidents_min + (median - accidents_min) * 2/3)) + " accidentes"),
        mpatches.Patch(color = "gold", 
                       label = "Entre " + str(int(accidents_min + (median - accidents_min) * 2/3))
                              + " y " + str(int(median)) + " (la mediana) accidentes"),
        mpatches.Patch(color = "orange", 
                       label = "Entre " + str(int(median))
                              + " y " + str(int(median + (accidents_max - median) * 1/6)) + " accidentes"),
        mpatches.Patch(color = "xkcd:pumpkin", 
                       label = "Entre " + str(int(median + (accidents_max - median) * 1/6))
                              + " y " + str(int(median + (accidents_max - median) * 2/6)) + " accidentes"),
        mpatches.Patch(color = "xkcd:vermillion", 
                       label = "Entre " + str(int(median + (accidents_max - median) * 2/6))
                              + " y " + str(int(median + (accidents_max - median) * 4/6)) + " accidentes"),
        mpatches.Patch(color = "xkcd:brownish red", 
                       label = "Entre " + str(int(median + (accidents_max - median) * 4/6))
                              + " y " + str(int(median + (accidents_max - median) * 5/6)) + " accidentes"),
        mpatches.Patch(color = "xkcd:dried blood", 
                       label = "Entre " + str(int(median + (accidents_max - median) * 5/6))
                              + " y " + str(int(accidents_max)) + " accidentes")
    ]
    
    # Generar la leyenda
    plt.legend(handles = legend_info)
    
    # Mostrar información adicional de la base de datos
    if extra_info:
        print(count_of_accidents.describe())
        
    return fig


#%% DEFINICIÓN DE LA INTERFAZ GRÁFICA


def make_window(theme : sg.theme) -> sg.Window:
    """
        Define y genera la interaz gráfica de PySimpleGUI.
        
        theme : sg.theme       -> Tema elegido para la interfaz. Se define como
                                    sg.theme("green mono") por defecto
    """
    
    # Establece el tema elegido
    sg.theme(theme)
    
    # Define las pestañas principales de la ventana
    menu_def = [['&Menú', ['&Salir']],
                ['&Ayuda', ['&¿Cómo usar el visualizador?']] ]
    
    # Define lo que aparece al hacer click derecho
    right_click_menu_def = [[], ['&Salir']]

    # Define la colocación de los elementos y widgets de la aplicación en la primera pestaña de la aplicación
    main_layout =  [
        [sg.Text('Observa la distribucion de accidentes de trafico en Estados Unidos')], 
        [sg.Slider(orientation = 'h', 
                      key = '-SLIDER-', 
                      range = (2010,2021),
                      pad = 30,
                      s = (42,20)),
         sg.Button('Dibujar', 
                      key = '-BUTTON-')
         ], 
        [sg.Frame ( 
            title = "Zona de dibujado",
            layout = [[
            sg.Canvas(size = (425,285), 
                      key = 'plot-canvas', 
                      border_width = 2, 
                      background_color = "#11875d"),
            sg.Canvas(size = (252,151), 
                      key = 'plot-canvas2', 
                      border_width = 2, 
                      background_color = "#11875d")
            ]]
        )],
    ]
    
    
    # Define la colocación de los elementos y widgets de la aplicación en la segunda pestaña de la aplicación
    # Genera una conjunto de columnas para los seleccionables de los estados
    # Coloca automáticamente los estados en orden alfabético en columnas de
    # STATE_PER_COLUMN número de estados
    STATES_PER_COLUMN = 14
    
    states_layout = list()
    state_columns = list()
    names = list(STATE_CODES.keys())
    
    # Reparte la lista alfabética de estados en las diferentes columnas
    for column in range(0, int(len(names) / STATES_PER_COLUMN + 1) ):
        for row in range(0, STATES_PER_COLUMN):
            if column * STATES_PER_COLUMN + row < len(names):
                state_columns.append([
                    sg.Checkbox(str(names[column * STATES_PER_COLUMN + row]), 
                                default = True, 
                                key = str(names[column * STATES_PER_COLUMN + row]))
                        ])
        
        states_layout.append(sg.Column(state_columns.copy()))
        state_columns.clear()
    
    states_layout = [states_layout]
    
    # Define la colocación de los elementos y widgets de la aplicación en la última pestaña de la aplicación
    logging_layout = [
        [sg.Text("Información adicional sobre la base de datos")],
        [sg.Multiline(size = (60,15), 
                       font = 'Courier 8', 
                       expand_x = True, 
                       expand_y = True, 
                       write_only = True,
                       reroute_stdout = True, 
                       reroute_stderr = True, 
                       echo_stdout_stderr = True, 
                       autoscroll = True, 
                       auto_refresh = True
                       )]
        ]
    
    
    # Coloca el resto de definiciones en orden y define el menú
    layout = [ [sg.MenubarCustom(menu_def, 
                       key = '-MENU-', 
                       font = 'Courier 15', 
                       tearoff = True)],
                [sg.Text('Visualizador de los datos de accidentes en Estados Unidos', 
                       size = (50, 1), 
                       justification = 'center', 
                       font = ("Helvetica", 16), 
                       relief = sg.RELIEF_RIDGE, 
                       key = '-TEXT HEADING-', 
                       enable_events = True)]]
    
    
    layout +=[[sg.TabGroup([
                       [sg.Tab('Gráfico de Accidentes', main_layout),
                       sg.Tab('Estados de Interés', states_layout),
                       sg.Tab('Información adicional', logging_layout)]
                       ], 
                           
                       key = '-TAB GROUP-', 
                       expand_x = True, 
                       expand_y = True),

               ]]
    
    layout[-1].append(sg.Sizegrip())
    
    # Define el comportamiento de la ventana de la aplicación
    window = sg.Window('Accidentes de EEUU', 
                       layout, 
                       right_click_menu = right_click_menu_def, 
                       right_click_menu_tearoff = True, 
                       grab_anywhere = False, 
                       resizable = True, 
                       margins = (0,0), 
                       use_custom_titlebar = True, 
                       finalize = True, 
                       keep_on_top = False,
                       element_justification = "c"
                       )
    
    window.set_min_size((700,500))
    
    # Expande las columnas de la segunda pestaña para que ocupen el tamaño nuevo de la ventana
    for i in states_layout[0]:
        i.expand(True, True)
        
    return window

def main():
    
    # Genera la ventana
    window = make_window(sg.theme())
    
    # Define variables para los handlers de pyplot que permiten embedding
    figure_canvas_agg = None 
    figure_canvas_agg2 = None 
    
    
    # Bucle principal de la interfaz gráfica
    while True:
        
        # Comprobar si el usuario hace algo
        event, values = window.read(timeout = 100)
               
        # Si elige salir, salir del bucle principal
        if event in (None, 'Salir', sg.WIN_CLOSED):
            break

        # Si decide leer la ayuda, crear un popup con información
        if event == '¿Cómo usar el visualizador?':
            sg.popup('Visualizador de accidentes en EEUU.',
                     '---Pagina "Gráfico de Accidentes"---',
                     'Puedes mover la barra deslizante de izquierda a derecha.',
                     'De esa forma se puede elegir el año del que obtener información sobre accidentes.',
                     'Se generará un gráfico con los datos de ese año al presionar el botón "Dibujar".',
                     '---Pagina "Estados de Interés"---',
                     'Puedes elegir los estados que se contabilizarán en el dibujado del mapa.', 
                     'Los rangos de los colores son dinámicos, y dependen de los datos máximo, mínimo y mediana.', 
                     'Se recomienda eliminar estados con valores muy elevados o sin apenas accidentes',
                     'Estos repercuten en el resultado final al aumentar los rangos de cada color, opacando diferencias menores entre otros estados',
                     '---Pagina "Información Adicional"---',
                     'Puedes observar algunos datos cuantitativos de la base de datos que se haya elegido',
                     keep_on_top=True)
        
        # Si pulsa el botón "Dibujar",
        if event  == '-BUTTON-':
            
            # Eliminar dibujos anteriores para que no se acumulen
            if not figure_canvas_agg == None:
                figure_canvas_agg.get_tk_widget().forget()
                figure_canvas_agg2.get_tk_widget().forget()
                plt.close('all')
            
            # Comprobar el tiempo de ejecución
            clock = time.time()
            
            # Generar una lista de los estados que se van a pedir a CrashAPI
            state_codes = list(STATE_CODES.values())
            for state_name in list(STATE_CODES.keys()):
                try:
                    if not (values[state_name]):
                        state_codes.remove(STATE_CODES[state_name])
                except KeyError:
                    pass
            
            # Realizar la petición a CrashaPI
            df = getDataframe(state_codes, int(values['-SLIDER-']))       
            df = preprocess(df)
            accident_count = groupCountAccidents(df)
            
            #Comprobar el tiempo utilizado en la petición
            clock = time.time() - clock
            print("Tiempo utilizado para obtener la base de datos:", round(clock,1), "segundos.")

            # Dibujar el mapa con la información obtenida            
            fig = plotMapAccidents(accident_count, int(values['-SLIDER-']))
            fig2 = plotMapAccidentsLeyend(accident_count)
            
            # Colocar los dibujos generados en la ventana mediante embedding
            figure_canvas_agg = FigureCanvasTkAgg(fig, window['plot-canvas'].TKCanvas)
            figure_canvas_agg.draw()
            figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
            
            figure_canvas_agg2 = FigureCanvasTkAgg(fig2, window['plot-canvas2'].TKCanvas)
            figure_canvas_agg2.draw()
            figure_canvas_agg2.get_tk_widget().pack(side='top', fill='both', expand=1)
            
            
    # Al salir, eliminar los dibujos para que no salgan por la lína de comandos y cerrar la ventana
    if not figure_canvas_agg == None:
        figure_canvas_agg.get_tk_widget().forget()
        figure_canvas_agg2.get_tk_widget().forget()
        plt.close('all')

    window.close()
    

if __name__ == '__main__':
    sg.theme('green mono')
    main()