import streamlit as st
import pandas as pd
import re
from PIL import Image
import pydeck as pdk




# Function to load and configure the page
def structure_and_format():
    im = Image.open("images/logo_aucca.png")
    st.set_page_config(page_title="Plantas Aucca", layout="wide", initial_sidebar_state="expanded")
    # st.sidebar.image(im, use_container_width=True)
    # st.logo(im)
    
    st.logo(im, size="large", link=None, icon_image=im)
    
    
    css_path = "style.css"

    with open(css_path) as css:
        st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)
    
    # Hide Streamlit footer and menu
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Hide index column in tables
    hide_table_row_index = """
        <style>
        thead tr th:first-child {display:none}
        tbody th {display:none}
        </style>
    """
    st.markdown(hide_table_row_index, unsafe_allow_html=True)

structure_and_format()

# Function to load plant list
@st.cache_data
def load_listado_plantas_aucca():
    return pd.read_csv("plantas_aucca_02_02_25.csv", sep=';', encoding='latin1')




# Load the plant list
plantas_list = load_listado_plantas_aucca()


# CLEANING
# Trim whitespace in 'Disponible Nov 2024', 'Familia', and 'Propiedades' columns
def espacios(value):
    return value.strip() if isinstance(value, str) else value
plantas_list[['Disponible Nov 2024', 'Familia', 'Propiedades','Categoria']] = plantas_list[['Disponible Nov 2024', 'Familia', 'Propiedades','Categoria']].applymap(espacios)
plantas_list['Disponible Nov 2024'] = plantas_list['Disponible Nov 2024'].fillna("No especificado").astype(str)

def clean_properties(value):
    if isinstance(value, str):
        # Split by multiple delimiters, strip whitespace, and convert each word to lowercase
        words = [word.strip().lower() for word in re.split(r'[,\-]', value)]
        # Join words back into a single string, separated by commas
        return ', '.join(words)
    return value
# plantas_list['Familia'] = plantas_list['Familia'].apply(clean_properties)
plantas_list['Propiedades'] = plantas_list['Propiedades'].apply(clean_properties)
plantas_list["Nombre total"] = plantas_list["Nombre vulgar"].fillna('') + " (" + plantas_list["Nombre Científico"].fillna('') + ")"
plantas_list = plantas_list.rename(columns={"Meses UNIRCADENAS": 'Meses Siembra (Chile)'})

nombres_list = [
    "Nombre vulgar",
    "Nombre Científico",
    "Familia",
    "Categoria",
    'Nombre total']

caracteristicas_list = ["Fijador de Nitrógeno",
    "Acumulador Dinámico",
    "Propiedades",
    "Minerales",
    "Observaciones",]

info_siembra_list = [
    "Época de siembra (CHILE)",
    "Meses Siembra (Chile)",
    "Método",
    "Profundidad de Siembra",
    "Tiempo de germinar",
    "Transplante",
    "Distancia entre (Plantas)",
    "Distancia entre (hileras)",
    "Tiempo para cosechar", ]

diponibilidad_list = [
    "lat",
    "lon",
    "Disponible Nov 2024",
    'Zona',
    'ruta mapa']

plantas_list[caracteristicas_list] = plantas_list[caracteristicas_list].fillna("Sin información").astype(str)
plantas_list['Familia'] = plantas_list['Familia'].fillna("Sin información").astype(str)
all_variables_list = nombres_list + caracteristicas_list + info_siembra_list + diponibilidad_list
plantas_list =  plantas_list[all_variables_list]

total_filas = plantas_list.shape[0]


plantas_df = plantas_list.copy()


# Function to get unique words from a column
def get_unique_words_from_column(df, column_name):
    all_properties = df[column_name].dropna().tolist()
    all_words = [word.strip() for prop in all_properties for word in re.split(r'[,\-;]', prop)]
    unique_words = sorted(set(all_words))
    return unique_words









st.title("EXPLORADOR DE FITODIVERSIDAD Y GUÍA DE CULTIVO AGROECOLÓGICO (CHILE)")

# st.sidebar.markdown("Nivel 1")


# LEVEL 1: Filter based on Disponibilidad
disponible_opciones = sorted(plantas_df['Disponible Nov 2024'].dropna().astype(str).unique())
disponible_seleccionado = st.sidebar.selectbox("Disponibilidad en Aucca", ["Todas"] + disponible_opciones)

# Apply first-level filter
if disponible_seleccionado == "Todas":
    plantas_df_2 = plantas_df.copy()
else:
    plantas_df_2 = plantas_df[plantas_df['Disponible Nov 2024'] == disponible_seleccionado]
    

# Meses de siembra (Multi-selection)
unique_properties_words_meses = get_unique_words_from_column(plantas_df_2, 'Meses Siembra (Chile)')
meses_seleccion = st.sidebar.multiselect("Meses Siembra (Chile)", ["Todas"] + unique_properties_words_meses)
if "Todas" not in meses_seleccion and meses_seleccion:
    plantas_df_2 = plantas_df_2[
    plantas_df_2['Meses Siembra (Chile)'].apply(
        lambda x: any(item in str(x) for item in meses_seleccion) if pd.notna(x) else False
    )
]

# st.sidebar.markdown("Nivel 2")

# LEVEL 2: Additional filters

# Categoria (Multi-selection)
categoria_opciones = get_unique_words_from_column(plantas_df_2, 'Categoria')
categoria_seleccionada = st.sidebar.multiselect("Categoría", ["Todas"] + categoria_opciones)

if "Todas" not in categoria_seleccionada and categoria_seleccionada:
    plantas_df_2 = plantas_df_2[plantas_df_2['Categoria'].isin(categoria_seleccionada)]

# Fijador de Nitrógeno
nitrogeno_opciones = sorted(plantas_df_2['Fijador de Nitrógeno'].dropna().astype(str).unique())
nitro_seleccionada = st.sidebar.selectbox("Fijador de Nitrógeno", ["Todas"] + nitrogeno_opciones)
if nitro_seleccionada != "Todas":
    plantas_df_2 = plantas_df_2[plantas_df_2['Fijador de Nitrógeno'] == nitro_seleccionada]

# Acumulador Dinámico (Multi-selection)
unique_properties_words_acumulador = get_unique_words_from_column(plantas_df_2, 'Acumulador Dinámico')
acumulador_seleccion = st.sidebar.multiselect("Acumulador Dinámico", ["Todas"] + unique_properties_words_acumulador)
if "Todas" not in acumulador_seleccion and acumulador_seleccion:
    plantas_df_2 = plantas_df_2[plantas_df_2['Acumulador Dinámico'].dropna().apply(lambda x: any(item in x for item in acumulador_seleccion))]

# Propiedades (Multi-selection)
unique_properties_words_propiedades = get_unique_words_from_column(plantas_df_2, 'Propiedades')
propiedades_seleccion = st.sidebar.multiselect("Propiedades Medicinales", ["Todas"] + unique_properties_words_propiedades)
if "Todas" not in propiedades_seleccion and propiedades_seleccion:
    plantas_df_2 = plantas_df_2[plantas_df_2['Propiedades'].dropna().apply(lambda x: any(item in x for item in propiedades_seleccion))]

# # Familia
# familia_opciones = sorted(plantas_df_2['Familia'].dropna().astype(str).unique())
# familia_seleccionada = st.sidebar.selectbox("Familia", ["Todas"] + familia_opciones)
# if familia_seleccionada != "Todas":
#     plantas_df_2 = plantas_df_2[plantas_df_2['Familia'] == familia_seleccionada]


# Display the filtered DataFrame
nombre_vulgar_selection_words = sorted(plantas_df_2['Nombre vulgar'].unique())
nombre_total_selection_words = sorted(plantas_df_2["Nombre total"].unique())



def results(df,total_filas, nombre_vulgar_selection_words, label="N° Registros", variable="Nombre vulgar"): 
    # Count the number of plants based on the selection criteria
    n_plantas = df[variable].count()
    # Convert the count to a string and create a single-line list of selected words
    markdown_list = ', '.join(nombre_vulgar_selection_words)
    
    
    # Create the result text
    result_text = f"Hay {n_plantas} regristros de plantas y arboles que cumplen con tu criterio de selección : {markdown_list}"
    
    # Display in two columns
    
    if n_plantas == total_filas: 
        st.write(f"Hay {n_plantas} regristros de plantas y arboles en la base de datos, puedes explorar usando filtros")
       
    else:
        st.write("#### Resultados")
        col1, col2 = st.columns([0.3, 1.7])
        with col1:
            # Display the metric
            st.metric(
                label=label,
                value=n_plantas
            )

        with col2:
            # Display the result text
            st.success(result_text)
        
    
results(plantas_df_2,total_filas, nombre_vulgar_selection_words, label="N° Registros", variable="Nombre vulgar")



with st.expander("Ver base de datos"):
    st.dataframe(
        plantas_df_2,
        hide_index=True
    )


# FILTER 4: by "Nombre total"
nombre_vulgar_selection = st.selectbox("Planta específica para leer en detalle", ["Selecciona una planta"] + nombre_total_selection_words)


# Filter by "Nombre total" if a selection is made
if nombre_vulgar_selection != "Selecciona una planta":
    planta_seleccionada_df = plantas_df_2[plantas_df_2["Nombre total"] == nombre_vulgar_selection]

    if not planta_seleccionada_df.empty:
        
        nombre_total_text = planta_seleccionada_df['Nombre total'].iloc[0]

        st.markdown(f"# {nombre_total_text}")
        
    
        col1, col2 = st.columns(2)
       
        with col1:
            st.markdown("## 🌿 Identificación")
            nombres_list = ["Nombre vulgar", "Nombre Científico", "Familia", "Categoria"]
            for field in nombres_list:
                st.markdown(f"**{field}:** {planta_seleccionada_df.iloc[0][field] if pd.notna(planta_seleccionada_df.iloc[0][field]) else 'No disponible'}")

            st.markdown("## 🌱 Características Servicios Ecosistémicos")
            caracteristicas_list = ["Fijador de Nitrógeno", "Acumulador Dinámico", "Minerales", "Propiedades"]
            for field in caracteristicas_list:
                st.markdown(f"**{field}:** {planta_seleccionada_df.iloc[0][field] if pd.notna(planta_seleccionada_df.iloc[0][field]) else 'No disponible'}")

            st.markdown("## 📚 Guía para Cultivo")
            info_siembra_list = [
                "Época de siembra (CHILE)", "Método", "Profundidad de Siembra",
                "Tiempo de germinar", "Transplante", "Distancia entre (Plantas)",
                "Distancia entre (hileras)", "Tiempo para cosechar", "Observaciones"
            ]
            for field in info_siembra_list:
                st.markdown(f"**{field}:** {planta_seleccionada_df.iloc[0][field] if pd.notna(planta_seleccionada_df.iloc[0][field]) else 'No disponible'}")

        with col2:
            st.markdown("## 📍 Localización en Aucca")
            # Check if latitude and longitude are numbers and not empty
            if pd.to_numeric(planta_seleccionada_df['lat'], errors='coerce').notna().all() and pd.to_numeric(planta_seleccionada_df['lon'], errors='coerce').notna().all():
                # Define the map using pydeck with a satellite map style
                map_layer = pdk.Deck(
                    map_style='mapbox://styles/mapbox/satellite-v9',  # Using the satellite style
                    initial_view_state={
                        "latitude": planta_seleccionada_df['lat'].mean(),
                        "longitude": planta_seleccionada_df['lon'].mean(),
                        "zoom": 18.5,
                        "pitch": 0,
                    },
                    layers=[
                        pdk.Layer(
                            'ScatterplotLayer',
                            data=planta_seleccionada_df,
                            get_position='[lon, lat]',
                            get_color='[255, 165, 0, 160]',  # Orange color
                            get_radius=1,  # Small radius for the markers
                        )
                    ]
                )
                st.pydeck_chart(map_layer)
            else:
                rupa_mapa = planta_seleccionada_df['ruta mapa'].iloc[0]
                mapa_zona_img = Image.open(rupa_mapa)
                st.image(mapa_zona_img,  use_container_width=True)
    else:
        st.write("")

else:
    st.write("")