import streamlit as st
from docx import Document
from PIL import Image
from gtts import gTTS
import os
import re



# Function to load and configure the page
def structure_and_format():
    im = Image.open("images/logo_aucca.png")
    # st.set_page_config(page_title="Plantas Aucca", layout="wide", initial_sidebar_state="expanded")
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

def text_to_speech(text, lang='es'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)  # 'es' is the language code for Spanish
        filename = 'speech.mp3'
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"Failed to generate speech: {e}")
        return None

def text_speech_button(text, key):
    if st.button('Escuchar el texto', key=key):
        filename = text_to_speech(text)
        audio_file = open(filename, 'rb')
        st.audio(audio_file.read(), format='audio/mp3')







def extract_text(doc, start_section):
    collecting = False
    markdown_output = []
    for para in doc.paragraphs:
        text = para.text.strip()
        style = para.style.name

        if 'Heading 3' in style and text == start_section:
            collecting = True
            continue  # Skip appending the section header to the output

        if collecting and ('Heading 1' in style or 'Heading 2' in style or ('Heading 3' in style and text != start_section)):
            break  # Stop collecting text when another section header is found

        if collecting:
            if 'Heading' in style:
                level = int(''.join(filter(str.isdigit, style)))
                level = min(level, 6)  # Limit to Markdown syntax for headings
                markdown_output.append(f"{'#' * level} {text}")
            elif 'Bullet' in style or 'List Paragraph' in style:
                markdown_output.append(f"- {text}")
            else:
                markdown_output.append(text)

    return "\n\n".join(markdown_output)


# Load the document
file_path = "huerta_agroecologica_comunitaria.docx"
doc = Document(file_path)


agricultura_parrafo = extract_text(doc, "Agricultura")
revolucion_verde_parrafo = extract_text(doc, "Revolución verde")
alimentos_en_chile_parrafo = extract_text(doc, "Modelo de producción de alimentos en Chile")
transgenicos_parrafo = extract_text(doc, "Transgénicos")
agroecologia_p = extract_text(doc, "Agroecología")
agricultura_urbana_p = extract_text(doc, "Agricultura urbana")
permacultura_p = extract_text(doc, "Permacultura")
suelo_p = extract_text(doc, "Suelo")
sol_p = extract_text(doc, "Sol")
tiempo_p = extract_text(doc, "Tiempo")
agua_p = extract_text(doc, "Agua")
camellones_p = extract_text(doc, "Camellones y surcos")
bancal_p = extract_text(doc, "Bancal profundo")
cero_lanbranza_p = extract_text(doc, "Cero labranza")



st.title("LINEAMIENTOS FUNDAMENTALES PARA ABORDAR UNA HUERTA COMUNITARIA AGROECOLÓGICA")

st.subheader("1) Introducción a las crisis de la agricultura y la sociedad.")

with st.expander("Agricultura"):
    st.markdown(agricultura_parrafo , unsafe_allow_html=False)
    text_speech_button(agricultura_parrafo, key="agr")

with st.expander("Revolución verde"):
    st.markdown(revolucion_verde_parrafo , unsafe_allow_html=False)
    text_speech_button(revolucion_verde_parrafo, key="rev")
    
with st.expander("Modelo de producción de alimentos en Chile"):
    st.markdown(alimentos_en_chile_parrafo , unsafe_allow_html=False)
    text_speech_button(alimentos_en_chile_parrafo, key="alim")
    
with st.expander("Transgénicos"):
    st.markdown(transgenicos_parrafo , unsafe_allow_html=False)
    text_speech_button(transgenicos_parrafo, key="trans")

st.subheader("2) Diferentes perspectivas y propuestas de solución a la crisis agrícola y social.")

with st.expander("Agroecología"):
    st.markdown(agroecologia_p , unsafe_allow_html=False)
    text_speech_button(agroecologia_p, key="agroecologia_p")
    
with st.expander("Agricultura urbana"):
    st.markdown(agricultura_urbana_p , unsafe_allow_html=False)
    text_speech_button(agricultura_urbana_p, key="agricultura_urbana_p")
    
with st.expander("Permacultura"):
    st.markdown(permacultura_p , unsafe_allow_html=False)
    text_speech_button(permacultura_p, key="permacultura_p")


st.subheader("3) Planificación del huerto")

with st.expander("Suelo"):
    st.markdown(suelo_p , unsafe_allow_html=False)
    text_speech_button(suelo_p, key="suelo_p")
    
    
with st.expander("Sol"):
    st.markdown(sol_p , unsafe_allow_html=False)
    text_speech_button(sol_p, key="sol_p")
    foto_patron_sol = Image.open("images/patron_sol_aucca.png")
    st.image(foto_patron_sol, caption='Patron Sol en Aucca', use_container_width=False)
    
    
with st.expander("Tiempo"):
    st.markdown(tiempo_p , unsafe_allow_html=False)
    text_speech_button(tiempo_p, key="tiempo_p")
    
with st.expander("Agua"):
    st.markdown(agua_p , unsafe_allow_html=False)
    text_speech_button(agua_p, key="agua_p")
    foto_patron_aguas = Image.open("images/temperatura_viento_lluvia_aucca.png")
    st.image(foto_patron_aguas, caption='Patron temperatura, lluvias y vientos en Aucca', use_container_width=False)
    

st.subheader("4) Tipos de Huerto")

with st.expander("Camellones y surcos"):
    st.markdown(camellones_p , unsafe_allow_html=False)
    text_speech_button(camellones_p, key="camellones_p")
    
with st.expander("Bancal profundo"):
    st.markdown(bancal_p , unsafe_allow_html=False)
    text_speech_button(bancal_p, key="bancal_p")
    
with st.expander("Cero labranza"):
    st.markdown(cero_lanbranza_p , unsafe_allow_html=False)
    text_speech_button(cero_lanbranza_p, key="cero_lanbranza_p")
    

