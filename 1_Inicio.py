import streamlit as st
import pandas as pd
import re
from PIL import Image
import pydeck as pdk
from gtts import gTTS
from docx import Document
import difflib
import unicodedata

# ======================
# INITIALIZE SESSION STATE (persist keys across re-runs)
# ======================
if "result_display" not in st.session_state:
    st.session_state["result_display"] = ""
if "plant_result" not in st.session_state:
    st.session_state["plant_result"] = None
if "related_expander" not in st.session_state:
    st.session_state["related_expander"] = ""
if "last_query" not in st.session_state:
    st.session_state["last_query"] = ""

# ======================
# PAGE CONFIGURATION
# ======================
def structure_and_format():
    im = Image.open("images/logo_aucca.png")
    st.set_page_config(page_title="AUCCA Chatbot", layout="wide", initial_sidebar_state="expanded")
    st.logo(im, size="large", link=None, icon_image=im)
    with open("style.css") as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    button[data-baseweb="button"][id="send_btn"] {
      background-color: #FF5733 !important;
      color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

structure_and_format()

# ======================
# HELPER: CLEAR RESULTS (only if query text changes)
# ======================
def clear_results():
    st.session_state["result_display"] = ""
    st.session_state["plant_result"] = None
    st.session_state["related_expander"] = ""

# ======================
# OPTIONAL: TEXT-TO-SPEECH
# ======================
def text_to_speech(text, lang='es'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        filename = "speech.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        st.error(f"Error TTS: {e}")
        return None

def text_speech_button(text, key):
    if st.button("Escuchar respuesta", key=key):
        fname = text_to_speech(text)
        if fname:
            with open(fname, "rb") as af:
                st.audio(af.read(), format="audio/mp3")

# ======================
# KNOWLEDGE BASE: LOAD DOCX CONTENT
# ======================


def cargar_informacion():
    def extract_text(doc, start_section):
        collecting = False
        markdown_output = []
        for para in doc.paragraphs:
            text = para.text.strip()
            style = para.style.name

            if 'Heading 3' in style and text == start_section:
                collecting = True
                continue

            if collecting and ('Heading 1' in style or 'Heading 2' in style or ('Heading 3' in style and text != start_section)):
                break

            if collecting:
                if 'Heading' in style:
                    level = int(''.join(filter(str.isdigit, style)))
                    level = min(level, 6)
                    markdown_output.append(f"{'#' * level} {text}")
                elif 'Bullet' in style or 'List Paragraph' in style:
                    markdown_output.append(f"- {text}")
                else:
                    markdown_output.append(text)

        return "\n\n".join(markdown_output)
    doc = Document("huerta_agroecologica_comunitaria.docx")

    preguntas =  {}
    taller_huerta_contenidos =  {
        "qué es la agricultura": extract_text(doc, "Agricultura"),
        "qué es la revolución verde": extract_text(doc, "Revolución verde"),
        "cómo es la producción de alimentos en Chile": extract_text(doc, "Modelo de producción de alimentos en Chile"),
        "qué son los transgénicos": extract_text(doc, "Transgénicos"),
        "qué es la agroecología": extract_text(doc, "Agroecología"),
        "qué es la agricultura urbana": extract_text(doc, "Agricultura urbana"),
        "qué es la permacultura": extract_text(doc, "Permacultura"),
        "qué es el suelo en agricultura": extract_text(doc, "Suelo"),
        "qué papel juega el sol en la agricultura": extract_text(doc, "Sol"),
        "cómo influye el tiempo en la agricultura": extract_text(doc, "Tiempo"),
        "por qué es importante el agua en la agricultura": extract_text(doc, "Agua"),
        "qué son los camellones y surcos": extract_text(doc, "Camellones y surcos"),
        "qué es un bancal profundo": extract_text(doc, "Bancal profundo"),
        "qué es la cero labranza": extract_text(doc, "Cero labranza"),
        "cuáles son los tipos de huerta": (
            "Existen diferentes tipos de huerta: \n\n"
            f"# Camellones y surcos \n\n {extract_text(doc, 'Camellones y surcos')}\n"
            f"# Cero labranza\n\n{extract_text(doc, 'Cero labranza')}\n"
            f"# Bancal profundo\n\n{extract_text(doc, 'Bancal profundo')}"
        ),
    }
    info_general_aucca =  {
     # Información general aucca
        "qué es aucca": (
            "AUCCA es un **Centro Eco-Pedagógico** ubicado en Talagante, Chile. Su misión es **difundir prácticas medioambientales regenerativas**, "
            "fomentando el intercambio de saberes bajo los principios del **Buen Vivir**. Desde su fundación en **2013**, ha trabajado como una "
            "organización sin fines de lucro enfocada en la agroecología, la educación ambiental y la cultura, promoviendo el desarrollo sostenible "
            "y la participación comunitaria."
        ),
        "cuál es la ubicación": (
            "AUCCA está ubicado en **Talagante, Chile**, a 40 km de Santiago y a 1,6 km del río Mapocho. "
            "Colinda con cuatro poblaciones de alta vulnerabilidad económica y social, incluyendo la villa de viviendas sociales 'Los Presidentes'. "
            "Esta ubicación estratégica permite un impacto directo en comunidades que enfrentan desafíos socioeconómicos."
        ),
        "cuál es la misión": (
            "La misión de AUCCA es **difundir prácticas medioambientales regenerativas** en Talagante, promoviendo el intercambio de saberes basados en los principios del **'Buen Vivir'**. "
            "Se busca fortalecer la educación ambiental y la soberanía alimentaria a través de la participación comunitaria."
        ),
        "cuál es la historia": (
            "AUCCA fue fundado en **2013** como una organización sin fines de lucro. "
            "El centro cuenta con un área demostrativa de **1500 m²**, en la que crecen más de **174 especies** de árboles y plantas. "
            "AUCCA adopta la práctica cultural de la **‘minga’**, fomentando la construcción colectiva del espacio a través del trabajo comunitario. "
            "Es un referente en la conservación de semillas y promueve activamente la agroecología y permacultura."
        ),
        "cuáles son los objetivos": (
            "Los objetivos específicos de AUCCA son:\n"
            "1. **Construir** un centro demostrativo de prácticas medioambientales sustentables.\n"
            "2. **Facilitar** el acceso a la educación ambiental mediante talleres accesibles.\n"
            "3. **Fomentar** la economía local a través de ferias ecológicas y comercio justo.\n"
            "4. **Establecer** redes con organizaciones culturales y medioambientales a nivel local, nacional y latinoamericano."
        ),
        "cuáles son las áreas temáticas": (
            "AUCCA trabaja en diversas áreas temáticas clave:\n"
            "- **Agroecología y Permacultura:** Producción de semillas agroecológicas, comercialización de **45 especies** de hierbas medicinales, "
            "y canastas familiares con **13 variedades** de hortalizas.\n"
            "- **Educación Ambiental:** Talleres de sustentabilidad a bajo costo en colaboración con colegios y centros comunitarios.\n"
            "- **Arte y Cultura:** El 20% de sus actividades se centran en prácticas ancestrales como cestería, alfarería y danza, "
            "promoviendo encuentros culturales como herramientas de autogestión."
        ),
        "cuáles son las alianzas": (
            "AUCCA ha establecido importantes alianzas con diversos actores, incluyendo:\n"
            "- Centros de salud familiar (CECOF Eduardo Frei).\n"
            "- Escuelas: Santa María, Tegualda, Montessori.\n"
            "- Redes nacionales e internacionales como el Movimiento de Agricultura Urbana Chile (MAU), "
            "el Movimiento por el Agua y los Territorios (MAT), y la Red de Agroecología de Talagante."
        ),
        "quiénes son beneficiarios": (
            "AUCCA beneficia a participantes de distintas comunas de la Región Metropolitana, con una predominancia de mujeres, "
            "quienes representan el **72%** del total de beneficiarios. La diversidad de participantes permite un intercambio enriquecedor de conocimientos y experiencias."
        ),
        "proyectos destacados": (
            "Entre los proyectos más destacados de AUCCA se encuentran:\n"
            "- **Bosque Comestible:** Proyecto de implementación planificada para octubre de 2024, que busca crear un ecosistema agroforestal sustentable.\n"
            "- **Proyecto 'Sembremos Salud Comunitaria' (2023):** Iniciativa que promueve la salud a través de la alimentación sostenible y la producción agroecológica."
        ),
        "financiamiento": (
            "AUCCA se financia principalmente mediante:\n"
            "- Venta de productos agroecológicos como hierbas y hortalizas.\n"
            "- Organización de ferias ecológicas.\n"
            "- Autogestión a través de talleres y eventos culturales que promueven la sostenibilidad."
        ),
        "contacto": (
            "Puedes comunicarte con AUCCA a través de los siguientes canales:\n"
            "- **Correo electrónico:** [aucca.contacto@gmail.com](mailto:aucca.contacto@gmail.com)\n"
            "- **Facebook:** [Centro Eco Pedagógico](https://www.facebook.com/centro.ecopedagogico)\n"
            "- **Instagram:**\n"
            "  - [@aucca.ecopedagogico](https://www.instagram.com/aucca.ecopedagogico)"
        ),
        "qué talleres": (
            "Los talleres de AUCCA abarcan una amplia gama de temáticas, incluyendo:\n"
            "- Agricultura regenerativa y producción de alimentos saludables.\n"
            "- Manejo de residuos y compostaje.\n"
            "- Bioconstrucción y uso de materiales naturales.\n"
            "Se ofrecen talleres accesibles para toda la comunidad, con precios asequibles y modalidades prácticas."
        ),
        "cuáles son los principios": (
            "AUCCA se rige por principios fundamentales como la sostenibilidad, la educación comunitaria, "
            "la equidad social y el respeto por el entorno natural. Se promueve la participación activa y el trabajo colaborativo en cada iniciativa."
        ),
        "qué eventos": (
            "AUCCA organiza eventos anuales como ferias agroecológicas, encuentros de intercambio de semillas y jornadas de educación ambiental. "
            "Estos eventos fortalecen los lazos comunitarios y promueven prácticas sustentables."
        ),
        "voluntariado": (
            "El programa de voluntariado de AUCCA permite a personas interesadas en la agroecología participar activamente en el mantenimiento del espacio. "
            "Los voluntarios colaboran en la huerta, la construcción ecológica y los talleres educativos."
        ),
    }   
    info_baño_seco =  {
        # Información sobre el Baño Seco
        "qué es el baño seco": (
            "El baño seco compostero de AUCCA es un sistema de saneamiento ecológico que procesa los desechos humanos sin el uso de agua. "
            "Se basa en la separación y descomposición de los desechos en dos cámaras, donde se transforman en compost utilizado para mejorar suelos degradados."
        ),
        "cómo se usa el baño seco": (
            "Para utilizar correctamente el baño seco, se deben depositar tanto la orina como las heces en el cajón sanitario. Luego, es importante añadir una pala de aserrín para cubrir los desechos."
            "Esto ayuda a controlar los olores, absorber la humedad y facilitar el proceso de descomposición."
        ),
        "cómo funciona el baño seco": (
            "El baño seco de AUCCA funciona mediante un sistema de doble cámara. Los desechos se recogen en una cámara, "
            "y después de cada uso, se agrega aserrín u otro material seco para absorber la humedad y controlar olores. "
            "Cuando una cámara se llena, se sella y se deja compostar durante un período de 6 a 12 meses."
        ),
        "qué hacer después de usar el baño seco": (
            "Después de usar el baño seco, es fundamental agregar material de cobertura como aserrín, cenizas o hojas secas. "
            "Este material ayuda a controlar los olores y facilita el proceso de compostaje."
        ),
        "cuánto tiempo tarda en compostarse el baño seco": (
            "El proceso de compostaje en el baño seco de AUCCA puede tardar entre 6 meses y un año, dependiendo de las condiciones ambientales "
            "y el manejo del material de cobertura."
        ),
        "para qué se usa el compost del baño seco": (
            "El compost producido por el baño seco se utiliza para mejorar suelos degradados y en áreas forestales. "
            "No se recomienda su uso en cultivos de hortalizas para consumo humano."
        ),
        "cómo se limpia el baño seco": (
            "El baño seco se limpia utilizando una mezcla de agua con vinagre o jabón biodegradable, asegurando una higiene adecuada "
            "sin afectar el proceso de compostaje."
        ),
        "qué materiales se pueden usar como cobertura": (
            "Se pueden utilizar aserrín, hojas secas, cenizas y otros materiales ricos en carbono para cubrir los desechos, controlar los olores y facilitar el compostaje."
        ),
        "qué pasa si no se cierra la tapa del baño seco": (
            "Si no se cierra la tapa del baño seco, pueden ingresar insectos, lo que puede generar olores desagradables y problemas de higiene."
        ),
        "cuál es el beneficio del baño seco para el medio ambiente": (
            "El baño seco ayuda a reducir el consumo de agua potable, previene la contaminación de fuentes hídricas y transforma los desechos humanos en un recurso útil."
        ),
        "cómo mantener el baño seco en buenas condiciones": (
            "Es importante realizar limpiezas regulares, controlar la ventilación y asegurarse de que siempre se agregue suficiente material de cobertura después de cada uso."
        ),
    
    }
    info_biofiltro =  {
        # Información sobre el Biofiltro
        "qué es el biofiltro": (
            "El biofiltro de AUCCA es un sistema natural de tratamiento de aguas grises que utiliza procesos físicos y biológicos para limpiar el agua proveniente de actividades domésticas como lavado de manos y duchas."
        ),
        "cómo funciona el biofiltro": (
            "El biofiltro funciona mediante un proceso de decantación, filtrado y fitorremediación con plantas acuáticas que eliminan impurezas del agua antes de reutilizarla para riego."
        ),
        "qué tipos de plantas se usan en el biofiltro": (
            "El biofiltro de AUCCA utiliza plantas semi-acuáticas como juncos y lirios, cuyas raíces promueven la actividad de microorganismos que descomponen la materia orgánica."
        ),
        "cuál es el mantenimiento del biofiltro": (
            "El mantenimiento del biofiltro incluye la limpieza de los decantadores cada 3-6 meses, la revisión de la trampa de aceites cada 1-2 meses y la sustitución del material filtrante cada 3-5 años."
        ),
        "cada cuánto se limpian los decantadores del biofiltro": (
            "Los decantadores del biofiltro deben limpiarse cada 3 a 6 meses para evitar la acumulación de sólidos que puedan obstruir el sistema."
        ),
        "qué hacer si el biofiltro tiene malos olores": (
            "Si el biofiltro presenta malos olores, puede indicar un problema en la filtración o acumulación de materia orgánica. "
            "Se recomienda revisar la trampa de aceites y realizar una limpieza profunda."
        ),
        "cuál es el beneficio del biofiltro para el medio ambiente": (
            "El biofiltro reduce el consumo de agua potable, promueve la reutilización sostenible del agua y mejora la calidad del agua utilizada en los cultivos."
        ),
        "para qué se usa el agua tratada en el biofiltro": (
            "El agua tratada en el biofiltro se reutiliza para el riego de huertas y áreas verdes, promoviendo la autosuficiencia hídrica en AUCCA."
        ),
        "qué hacer si el flujo de agua en el biofiltro es lento": (
            "Si el flujo de agua es lento, se debe revisar si hay obstrucciones en las capas filtrantes y realizar un mantenimiento del humedal."
        ),
        "cuáles son las capas del biofiltro": (
            "El biofiltro está compuesto por capas de ripio (grava) y arena, que permiten la filtración del agua, así como plantas acuáticas que oxigenan y purifican el agua."
        ),
        "cuál es la vida útil del biofiltro": (
            "Con un mantenimiento adecuado, el biofiltro puede tener una vida útil de más de 10 años, con reemplazo periódico de materiales filtrantes."
        ),
        "qué pasa si la trampa de aceites no se limpia": (
            "Si la trampa de aceites no se limpia regularmente, puede saturarse y afectar la capacidad del biofiltro para eliminar impurezas del agua, comprometiendo la calidad del proceso de filtrado."
        ),
        "cómo se construyó el biofiltro de AUCCA": (
            "El biofiltro de AUCCA fue construido el 6 de julio de 2018 utilizando materiales naturales y mano de obra comunitaria. "
            "Las capas de filtrado y las plantas fueron seleccionadas para optimizar el proceso de tratamiento del agua."
        ),
        "cuánto tiempo toma filtrar el agua en el biofiltro": (
            "El tiempo de filtrado en el biofiltro varía según la carga de agua, pero generalmente el proceso completo toma entre 24 y 48 horas para obtener agua apta para riego."
        ),
        "cómo se monitorea la calidad del agua tratada": (
            "Se monitorea a través de observaciones periódicas, evaluando el flujo, la claridad del agua y la salud de las plantas del humedal artificial."
        ),
        "puedo beber el agua del biofiltro": (
            "No, el agua tratada en el biofiltro no es apta para el consumo humano directo. Solo se utiliza para riego y otros usos no potables."
        ),
        "qué beneficios tiene el biofiltro para la comunidad": (
            "El biofiltro permite el ahorro de agua potable, reduce la carga de aguas residuales y educa a la comunidad sobre el manejo sostenible del recurso hídrico."
        ),
        "cómo se realiza el reemplazo del material filtrante": (
            "El material filtrante, como la arena y la grava, se reemplaza cada 3 a 5 años dependiendo del nivel de saturación para garantizar una filtración eficiente."
        ),
    }
    info_compost =  {
        #Compost
        "qué es el compostaje": (
            "El compostaje es un proceso biológico en el que los microorganismos descomponen la materia orgánica, "
            "transformándola en compost, un fertilizante natural rico en nutrientes. En AUCCA se utilizan técnicas de compostaje aeróbico y lombricultura."
        ),
        "cómo se hace compost en aucca": (
            "En AUCCA se practica el compostaje utilizando residuos orgánicos como restos de comida, hojas secas y estiércol. "
            "Se controla la humedad, el oxígeno y la proporción de carbono y nitrógeno para optimizar el proceso de descomposición."
        ),
        "qué materiales se pueden compostar": (
            "Se pueden compostar restos de frutas y verduras, cáscaras de huevo, hojas secas, papel sin tinta, "
            "aserrín y residuos de jardín. No se deben incluir carnes, lácteos o aceites."
        ),
        "qué no se debe compostar": (
            "No se deben compostar productos de origen animal como carnes, huesos, lácteos, aceites, heces de animales carnívoros "
            "o materiales tratados químicamente, ya que pueden generar olores desagradables y atraer plagas."
        ),
        "cuánto tiempo tarda el compostaje": (
            "El proceso de compostaje en AUCCA puede tardar entre 3 y 6 meses, dependiendo de factores como la temperatura, "
            "la humedad y la aireación adecuada de la pila de compost."
        ),
        "cuáles son los beneficios del compost": (
            "El compost mejora la fertilidad del suelo, incrementa su capacidad de retención de agua, promueve la actividad microbiana "
            "y reduce la dependencia de fertilizantes químicos."
        ),
        "cómo se airea el compost": (
            "El compost debe airearse periódicamente, volteándolo con una horquilla o pala cada 1 o 2 semanas para garantizar "
            "una adecuada oxigenación y evitar la formación de malos olores."
        ),
        "cómo controlar el olor del compost": (
            "Para controlar los olores del compost, se recomienda mantener un buen equilibrio entre materiales verdes (ricos en nitrógeno) "
            "y materiales marrones (ricos en carbono), además de garantizar una adecuada aireación."
        ),
        "cómo saber si el compost está listo": (
            "El compost está listo cuando tiene un color oscuro, textura homogénea, un olor a tierra fresca y no se distinguen los materiales originales."
        ),
        "qué tipo de compostaje se hace en aucca": (
            "En AUCCA se realizan diferentes tipos de compostaje, incluyendo el compostaje aeróbico en pilas, la lombricultura con lombrices rojas californianas "
            "y el compostaje en baños secos."
        ),
        "qué es la lombricultura": (
            "La lombricultura es un método de compostaje en el que se utilizan lombrices para descomponer la materia orgánica, "
            "produciendo humus de lombriz, un fertilizante rico en nutrientes."
        ),
        "cómo se hace la lombricultura": (
            "Para hacer lombricultura en AUCCA, se colocan lombrices rojas californianas en un lecho de residuos orgánicos, "
            "controlando la humedad y la alimentación con restos de frutas y verduras."
        ),
        "cuál es la diferencia entre compostaje aeróbico y anaeróbico": (
            "El compostaje aeróbico requiere oxígeno para la descomposición de la materia orgánica y produce compost de alta calidad. "
            "El compostaje anaeróbico se realiza en ausencia de oxígeno, generando gases como metano y con un proceso más lento."
        ),
        "qué hacer si el compost está demasiado húmedo": (
            "Si el compost está muy húmedo, se deben añadir materiales secos como hojas, aserrín o cartón para absorber el exceso de humedad "
            "y mejorar la aireación."
        ),
        "qué hacer si el compost está demasiado seco": (
            "Si el compost está seco, se debe agregar agua en pequeñas cantidades y mezclarlo bien para asegurar una humedad óptima para la descomposición."
        ),
        "cuál es la proporción ideal de materiales para compostar": (
            "La proporción ideal es 3 partes de materiales ricos en carbono (hojas secas, paja, cartón) por 1 parte de materiales ricos en nitrógeno "
            "(restos de frutas y verduras, césped)."
        ),
        "qué temperatura debe tener el compost": (
            "El compost debe mantenerse entre 50 y 65 grados Celsius para una descomposición eficiente y eliminación de patógenos."
        ),
        "cómo prevenir plagas en el compost": (
            "Para evitar plagas, es importante cubrir los residuos orgánicos con materiales secos, mantener la pila bien aireada "
            "y evitar el compostaje de carnes y lácteos."
        ),
        "dónde se usa el compost de aucca": (
            "El compost generado en AUCCA se utiliza para enriquecer la huerta agroecológica comunitaria y mejorar los suelos degradados del centro."
        ),
        "qué herramientas se necesitan para hacer compost": (
            "Las herramientas básicas para el compostaje incluyen una pala o rastrillo para voltear el compost, un recipiente de almacenamiento, "
            "y un medidor de humedad y temperatura para monitorear las condiciones."
        ),
        "cuál es el papel de los microorganismos en el compostaje": (
            "Los microorganismos, como bacterias y hongos, descomponen la materia orgánica en nutrientes disponibles para las plantas, "
            "transformando los residuos en compost de alta calidad."
        ),
        "qué hacer si el compost tiene mal olor": (
            "Un mal olor indica exceso de humedad o descomposición anaeróbica. Se debe airear el compost y añadir más material seco "
            "para corregir el problema."
        ),
        "cómo hacer compost en espacios pequeños": (
            "En espacios pequeños, se recomienda utilizar composteras verticales o contenedores con buena ventilación para gestionar los residuos orgánicos de manera eficiente."
        ),
        "cómo contribuye el compostaje a la sostenibilidad": (
            "El compostaje reduce la cantidad de residuos orgánicos enviados a vertederos, minimiza la emisión de gases de efecto invernadero "
            "y fomenta una agricultura más sostenible."
        ),
        "cuánto compost se produce a partir de 1 kg de residuos orgánicos": (
            "Aproximadamente, 1 kg de residuos orgánicos produce 0,3 kg de compost, dependiendo de las condiciones del proceso."
        ),
        "cómo se acelera el proceso de compostaje": (
            "El proceso de compostaje se puede acelerar manteniendo la proporción adecuada de carbono y nitrógeno, asegurando una buena aireación "
            "y triturando los materiales orgánicos antes de agregarlos."
        ),
        "qué es el humus de lombriz": (
            "El humus de lombriz es un fertilizante natural producido por las lombrices que mejora la estructura del suelo, aumenta su capacidad de retención de agua "
            "y aporta microorganismos beneficiosos."
        ),
        "qué tipo de residuos se generan en aucca para compostar": (
            "En AUCCA se generan residuos como restos de cosecha de la huerta, podas de árboles, residuos de cocina y hojas secas, "
            "todos aprovechados en el compostaje."
        ),
        "cómo se involucra la comunidad en el compostaje": (
            "AUCCA involucra a la comunidad en jornadas de educación y trabajo colaborativo, enseñando a las familias a implementar el compostaje en sus hogares."
        ),
    }
    preguntas.update(info_general_aucca)
    preguntas.update(taller_huerta_contenidos)
    preguntas.update(info_baño_seco)
    preguntas.update(info_biofiltro)
    preguntas.update(info_compost)
    
    

    # Sinonimos 
    sinonimos = {}
    sinonimos_general = {
        "qué es aucca": ["qué significa aucca", "qué hace aucca", "qué es el centro aucca", "de qué trata aucca", "qué representa aucca"],
        "cuál es la ubicación": ["dónde está ubicado", "dónde queda", "en qué lugar está aucca", "dirección de aucca", "ubicación exacta de aucca"],
        "cuál es la misión": ["qué busca aucca", "cuál es el propósito de aucca", "cuál es el objetivo principal de aucca", "para qué existe aucca", "cuál es la razón de ser de aucca"],
        "cuál es la historia": ["cómo comenzó aucca", "cuándo se fundó aucca", "cuál es el origen de aucca", "cuándo inició aucca", "qué trayectoria tiene aucca"],
        "cuáles son los objetivos": ["qué metas tiene aucca", "qué busca lograr aucca", "cuáles son las finalidades de aucca", "qué propósitos tiene aucca", "metas de aucca"],
        "cuáles son las áreas temáticas": ["qué temas cubre aucca", "en qué áreas trabaja aucca", "qué enfoques tiene aucca", "de qué trata aucca", "temáticas de aucca"],
        "cuáles son las alianzas": ["con qué organizaciones colabora aucca", "qué redes tiene aucca", "quiénes son los socios de aucca", "colaboradores de aucca", "alianzas de aucca"],
        "quiénes son beneficiarios": ["quién recibe apoyo de aucca", "a quién beneficia aucca", "quién participa en aucca", "beneficiados por aucca", "público de aucca"],
        "proyectos destacados": ["qué proyectos importantes tiene aucca", "qué iniciativas ha desarrollado aucca", "qué logros tiene aucca", "qué programas tiene aucca", "proyectos clave de aucca"],
        "financiamiento": ["cómo se financia aucca", "de dónde obtiene recursos aucca", "qué fuentes de ingreso tiene aucca", "de dónde recibe fondos aucca", "finanzas de aucca"],
        "contacto": ["cómo puedo comunicarme con aucca", "dónde puedo contactar a aucca", "cuáles son los medios de contacto de aucca", "información de contacto aucca", "contacto directo aucca"],
        "qué es la agroecología": ["cómo define aucca la agroecología", "qué significa agroecología para aucca", "qué hacen en agroecología", "explicación de agroecología", "concepto de agroecología"],
        "qué es la permacultura": ["qué significa permacultura", "cómo aplican la permacultura en aucca", "qué es la permacultura en aucca", "concepto de permacultura", "principios de permacultura"],
        "qué talleres": ["qué cursos ofrece aucca", "qué capacitaciones brinda aucca", "qué actividades educativas tiene aucca", "talleres de aucca", "cursos de aucca"],
        "cuáles son los principios": ["qué valores rigen aucca", "en qué se basa aucca", "qué guía a aucca", "principios fundamentales de aucca", "valores de aucca"],
        "qué eventos": ["qué actividades organiza aucca", "qué tipo de eventos tiene aucca", "qué eventos se realizan en aucca", "calendario de eventos aucca", "próximos eventos aucca"],
        "voluntariado": ["cómo puedo ser voluntario en aucca", "qué oportunidades de voluntariado ofrece aucca", "puedo ayudar en aucca", "voluntariado en aucca", "participar en aucca"],
    }
    sinonimos_baño_seco = {
        "qué es el baño seco": ["cómo funciona el baño seco", "para qué sirve el baño seco", "qué hace el baño seco", "definición de baño seco", "concepto de baño seco", "baño seco compostero", "inodoro seco", "baño ecológico", "sistema de baño seco"],
        "cómo se usa el baño seco" : ['como utilizar el baño','usar el baño',],
        "cómo funciona el baño seco": ["cómo se usa el baño seco", "de qué manera opera el baño seco", "cómo se maneja el baño seco", "uso del baño seco", "operación del baño seco", "mecanismo del baño seco", "cómo se instala el baño seco", "funcionamiento del baño seco"],
        "qué hacer después de usar el baño seco": ["cómo limpiar el baño seco", "qué sigue después de usar el baño seco", "qué pasos seguir tras usar el baño seco", "mantenimiento del baño seco", "limpieza del baño seco", "procedimiento después de usar el baño seco", "cuidados del baño seco", "qué hacer tras utilizar el baño seco"],
        "cuánto tiempo tarda en compostarse el baño seco": ["duración del compostaje del baño seco", "tiempo de descomposición del baño seco", "en cuánto tiempo se convierte en compost", "cuándo está listo el compost del baño seco", "procesamiento del baño seco"],
        "para qué se usa el compost del baño seco": ["usos del compost del baño seco", "aplicaciones del compost del baño seco", "cómo se utiliza el compost del baño seco", "destino del compost del baño seco", "beneficios del compost del baño seco"],
        "cómo se limpia el baño seco": ["mantenimiento del baño seco", "limpieza del baño seco", "cómo higienizar el baño seco", "procedimiento de limpieza del baño seco", "qué productos usar para limpiar el baño seco"],
        "qué materiales se pueden usar como cobertura": ["qué poner en el baño seco después de usar", "materiales de cobertura del baño seco", "opciones de cobertura para el baño seco", "tipos de cobertura para el baño seco", "qué se recomienda para cubrir los desechos"],
        "qué pasa si no se cierra la tapa del baño seco": ["problemas por no cerrar el baño seco", "qué ocurre si dejo abierta la tapa", "consecuencias de no cerrar el baño seco", "impacto de dejar la tapa abierta", "qué riesgos hay si la tapa queda abierta"],
        "cuál es el beneficio del baño seco para el medio ambiente": ["ventajas ecológicas del baño seco", "impacto ambiental del baño seco", "por qué el baño seco es sostenible", "cómo contribuye el baño seco al medio ambiente", "beneficios ecológicos del baño seco"],
        "cómo mantener el baño seco en buenas condiciones": ["mantenimiento adecuado del baño seco", "cuidados para el baño seco", "cómo prolongar la vida útil del baño seco", "mejores prácticas para el baño seco", "cómo evitar problemas en el baño seco"]
    }
    sinonimos_bio_filtro = {
        "qué es el biofiltro": ["cómo funciona el biofiltro", "para qué sirve el biofiltro", "qué hace el biofiltro", "definición de biofiltro", "concepto de biofiltro", "biofiltro de aguas grises", "filtro ecológico", "sistema de filtrado de aguas", "tratamiento ecológico de aguas", "filtro natural de aguas"],
        "cómo funciona el biofiltro": ["cómo opera el biofiltro", "de qué manera trabaja el biofiltro", "qué proceso sigue el biofiltro", "mecanismo del biofiltro", "cómo actúa el biofiltro", "funcionamiento del biofiltro", "proceso de filtración del biofiltro", "cómo trabaja el biofiltro"],
        "qué tipos de plantas se usan en el biofiltro": ["qué vegetación hay en el biofiltro", "qué especies se utilizan en el biofiltro", "qué plantas filtran el agua", "plantas del biofiltro", "tipos de flora en el biofiltro", "qué vegetales crecen en el biofiltro", "especies utilizadas en biofiltros"],
        "cuál es el mantenimiento del biofiltro": ["cómo se cuida el biofiltro", "qué cuidados necesita el biofiltro", "mantenimiento regular del biofiltro", "cómo prolongar la vida del biofiltro", "cuidados básicos del biofiltro", "cómo limpiar el biofiltro", "frecuencia de mantenimiento del biofiltro"],
        "cada cuánto se limpian los decantadores del biofiltro": ["frecuencia de limpieza de los decantadores", "cuándo limpiar los decantadores", "mantenimiento de los decantadores", "limpieza periódica del biofiltro", "cómo mantener limpios los decantadores"],
        "qué hacer si el biofiltro tiene malos olores": ["cómo eliminar olores del biofiltro", "qué hacer si huele mal el biofiltro", "control de olores en el biofiltro", "soluciones para malos olores en el biofiltro", "por qué huele mal el biofiltro"],
        "cuál es el beneficio del biofiltro para el medio ambiente": ["ventajas ecológicas del biofiltro", "impacto positivo del biofiltro", "cómo ayuda el biofiltro al medio ambiente", "beneficios ambientales del biofiltro", "contribución ecológica del biofiltro"],
        "para qué se usa el agua tratada en el biofiltro": ["uso del agua del biofiltro", "destino del agua filtrada", "cómo se reutiliza el agua tratada", "aplicaciones del agua filtrada", "dónde se usa el agua del biofiltro"],
        "qué hacer si el flujo de agua en el biofiltro es lento": ["cómo mejorar el flujo del biofiltro", "qué hacer si el agua no fluye bien", "cómo solucionar el flujo lento", "qué hacer si el biofiltro se obstruye", "mejorar la eficiencia del biofiltro"],
        "cuáles son las capas del biofiltro": ["qué materiales componen el biofiltro", "estructura del biofiltro", "de qué está hecho el biofiltro", "capas de filtración del biofiltro", "composición del biofiltro"],
        "cuál es la vida útil del biofiltro": ["duración del biofiltro", "cuánto tiempo dura el biofiltro", "cuándo reemplazar el biofiltro", "vida promedio del biofiltro", "resistencia del biofiltro"],
        "qué pasa si la trampa de aceites no se limpia": ["consecuencias de no limpiar la trampa de aceites", "problemas por no limpiar la trampa", "impacto de la trampa de aceites sucia", "qué sucede si no se mantiene la trampa", "riesgos de una trampa de aceites obstruida"],
        "cómo se construyó el biofiltro de AUCCA": ["proceso de construcción del biofiltro", "cómo se hizo el biofiltro", "materiales usados en la construcción del biofiltro", "historia de la construcción del biofiltro", "etapas de construcción del biofiltro"],
        "cuánto tiempo toma filtrar el agua en el biofiltro": ["duración del proceso de filtrado", "tiempo de filtración del biofiltro", "cuánto tarda el biofiltro en limpiar el agua", "velocidad de filtración del biofiltro", "procesamiento del agua en biofiltros"],
        "cómo se monitorea la calidad del agua tratada": ["métodos de control de calidad del agua", "cómo saber si el agua está limpia", "cómo verificar la calidad del agua tratada", "monitoreo del biofiltro", "control de calidad del biofiltro"],
        "puedo beber el agua del biofiltro": ["es potable el agua del biofiltro", "se puede consumir el agua filtrada", "es segura para beber el agua del biofiltro", "calidad del agua del biofiltro", "puedo usar el agua para consumo humano"]
    }
    sinonimos_compostaje = {
        "qué es el compostaje": ["cómo funciona el compostaje", "para qué sirve el compostaje", "qué hace el compostaje", "definición de compostaje", "concepto de compostaje", "compostaje orgánico", "proceso de compostaje", "transformación de residuos orgánicos"],
        "cómo se hace compost en aucca": ["cómo preparar compost", "proceso de compostaje en aucca", "qué se necesita para hacer compost", "pasos para hacer compost en aucca", "cómo producir compost en aucca"],
        "qué materiales se pueden compostar": ["qué se puede poner en el compost", "que va en el compost", "materiales aptos para compost", "qué residuos se pueden compostar", "ingredientes para el compost", "qué se puede usar en el compostaje", "qué se puede usar en el compost"],
        "qué no se debe compostar": ["qué no va en el compost", "materiales prohibidos en el compost", "qué evitar en el compostaje", "residuos no compostables", "qué no se puede usar para compost"],
        "cuánto tiempo tarda el compostaje": ["tiempo de descomposición del compost", "duración del compostaje", "cuánto demora hacer compost", "en cuánto tiempo se obtiene compost", "proceso temporal del compostaje"],
        "cuáles son los beneficios del compost": ["ventajas del compost", "cómo ayuda el compost", "por qué usar compost", "beneficios del compost para el suelo", "utilidad del compost"],
        "cómo se airea el compost": ["cómo oxigenar el compost", "aireación del compost", "volteo del compost", "mantener el compost aireado", "cómo mover el compost"],
        "cómo controlar el olor del compost": ["cómo evitar malos olores en el compost", "control de olores en compost", "por qué huele mal el compost", "cómo reducir el mal olor del compost", "soluciones para el mal olor del compost"],
        "cómo saber si el compost está listo": ["indicadores de compost maduro", "cómo identificar compost terminado", "cuándo está listo el compost", "señales de compost terminado", "compost listo para usar"],
        "qué tipo de compostaje se hace en aucca": ["métodos de compostaje en aucca", "técnicas de compostaje en aucca", "cómo se hace compost en aucca", "tipos de compost en aucca", "sistemas de compostaje en aucca"],
        "qué es la lombricultura": ["crianza de lombrices", "producción de humus de lombriz", "cómo funciona la lombricultura", "para qué sirve la lombricultura", "qué se obtiene de la lombricultura"],
        "cómo se hace la lombricultura": ["cómo criar lombrices", "cómo preparar una lombricompostera", "proceso de lombricultura", "manejo de lombrices para compost", "cuidados en la lombricultura"],
        "cuál es la diferencia entre compostaje aeróbico y anaeróbico": ["compostaje con oxígeno vs sin oxígeno", "comparación de métodos de compostaje", "diferencias entre tipos de compost", "cuál es mejor compostaje aeróbico o anaeróbico", "ventajas del compostaje aeróbico y anaeróbico"],
        "qué hacer si el compost está demasiado húmedo": ["cómo secar el compost", "soluciones para compost húmedo", "por qué está mojado el compost", "qué hacer con compost empapado", "cómo corregir exceso de humedad en compost"],
        "qué hacer si el compost está demasiado seco": ["cómo hidratar el compost", "soluciones para compost seco", "por qué está seco el compost", "qué hacer con compost seco", "cómo corregir falta de humedad en compost"],
        "qué herramientas se necesitan para hacer compost": ["utensilios para compostaje", "qué se usa para hacer compost", "herramientas esenciales para compost", "equipo necesario para compostar", "instrumentos de compostaje"],
        "cuál es el papel de los microorganismos en el compostaje": ["función de microorganismos en compost", "qué hacen los microorganismos en compost", "importancia de los microorganismos en compostaje", "cómo ayudan los microorganismos en compost", "microorganismos en la descomposición del compost"],
        "qué hacer si el compost tiene mal olor": ["cómo eliminar el mal olor del compost", "mal olor en compost, qué hacer", "evitar olores en compost", "por qué huele mal el compost", "cómo solucionar olores en el compost"],
        "cómo hacer compost en espacios pequeños": ["compostaje en departamentos", "compost en casa pequeña", "hacer compost en lugares reducidos", "compostaje doméstico", "cómo compostar en espacios reducidos"]
    }
    sinonimos_contenido_taller_huerta = {
        "qué es la agricultura": ["definición de agricultura", "para qué sirve la agricultura", "concepto de agricultura", "cuál es la importancia de la agricultura", "significado de la agricultura", "qué comprende la agricultura"],
        "qué es la revolución verde": ["origen de la revolución verde", "cuál es el impacto de la revolución verde", "cómo influyó la revolución verde en la agricultura", "qué cambios trajo la revolución verde", "ventajas y desventajas de la revolución verde"],
        "cómo es la producción de alimentos en Chile": ["modelo agrícola en Chile", "cómo se cultivan los alimentos en Chile", "sistema de producción agrícola en Chile", "cómo se generan los alimentos en Chile", "estructura de la agricultura en Chile"],
        "qué son los transgénicos": ["qué significa transgénico", "para qué sirven los transgénicos", "cómo se producen los transgénicos", "ventajas y desventajas de los transgénicos", "impacto de los transgénicos en la salud"],
        "qué es la agroecología": ["cómo funciona la agroecología", "para qué sirve la agroecología", "beneficios de la agroecología", "concepto de agroecología", "diferencia entre agroecología y agricultura convencional"],
        "qué es la agricultura urbana": ["definición de agricultura urbana", "cómo se practica la agricultura urbana", "ventajas de la agricultura urbana", "dónde se realiza la agricultura urbana", "ejemplos de agricultura urbana"],
        "qué es la permacultura": ["principios de la permacultura", "cómo se aplica la permacultura", "diferencia entre permacultura y agroecología", "para qué sirve la permacultura", "ejemplos de permacultura"],
        "qué es el suelo en agricultura": ["importancia del suelo en la agricultura", "qué función cumple el suelo", "cómo se cuida el suelo", "tipos de suelo en la agricultura", "factores que afectan el suelo agrícola"],
        "qué papel juega el sol en la agricultura": ["importancia del sol en la agricultura", "cómo afecta la radiación solar a los cultivos", "relación entre sol y fotosíntesis", "beneficios de la luz solar en los cultivos", "cómo proteger los cultivos del sol"],
        "cómo influye el tiempo en la agricultura": ["impacto del clima en la agricultura", "cómo afectan las estaciones a los cultivos", "relación entre temperatura y producción agrícola", "qué factores climáticos afectan la agricultura", "estrategias para adaptarse al clima en la agricultura"],
        "por qué es importante el agua en la agricultura": ["función del agua en los cultivos", "cómo afecta la falta de agua a la producción agrícola", "manejo eficiente del agua en la agricultura", "qué sistemas de riego existen", "cómo se conserva el agua en la agricultura"],
        "qué son los camellones y surcos": ["definición de camellones y surcos", "para qué sirven los camellones y surcos", "cómo se construyen los camellones", "beneficios de los camellones en la agricultura", "ejemplos de camellones y surcos"],
        "qué es un bancal profundo": ["qué son los bancales","cómo se hace un bancal profundo", "ventajas del bancal profundo", "para qué sirve un bancal profundo", "diferencias entre bancal profundo y huerta tradicional", "cómo se mantiene un bancal profundo"],
        "qué es la cero labranza": ["beneficios de la cero labranza", "cómo funciona la cero labranza", "cuál es la diferencia entre labranza y cero labranza", "qué cultivos se adaptan a la cero labranza", "impacto de la cero labranza en el suelo"],
        "cuáles son los tipos de huerta": ["diferentes estilos de huertas", "tipos de cultivos en huertas", "cómo elegir el tipo de huerta", "qué técnicas se usan en cada tipo de huerta", "cuál es la mejor huerta para el hogar"]
    }
    sinonimos.update(sinonimos_general)
    sinonimos.update(sinonimos_baño_seco)
    sinonimos.update(sinonimos_bio_filtro)
    sinonimos.update(sinonimos_compostaje)
    sinonimos.update(sinonimos_contenido_taller_huerta)

    return preguntas, sinonimos 
preguntas, sinonimos = cargar_informacion()

base_conocimiento = preguntas

knowledge = {
    "biofiltro": {k: v for k, v in preguntas.items() if "biofiltro" in k},
    "baño": {k: v for k, v in preguntas.items() if "baño seco" in k},
    "compost": {k: v for k, v in preguntas.items() if "compost" in k or "lombricultura" in k},
    "general": {k: v for k, v in preguntas.items() if k in [
        "qué es aucca", "cuál es la ubicación", "cuál es la misión", "cuál es la historia",
        "cuáles son los objetivos", "cuáles son las áreas temáticas", "cuáles son las alianzas",
        "quiénes son beneficiarios", "proyectos destacados", "financiamiento", "contacto",
        "qué talleres", "cuáles son los principios", "qué eventos", "voluntariado"
    ]},
    "taller": {k: v for k, v in preguntas.items() if k in [
        "qué es la agricultura", "qué es la revolución verde", "cómo es la producción de alimentos en Chile",
        "qué son los transgénicos", "qué es la agroecología", "qué es la agricultura urbana",
        "qué es la permacultura", "qué es el suelo en agricultura", "qué papel juega el sol en la agricultura",
        "cómo influye el tiempo en la agricultura", "por qué es importante el agua en la agricultura",
        "qué son los camellones y surcos", "qué es un bancal profundo", "qué es la cero labranza",
        "cuáles son los tipos de huerta"
    ]}
}




# ======================
# NORMALIZE TEXT FUNCTION
# ======================
def normalizar_texto(txt):
    if not isinstance(txt, str):
        txt = str(txt)
    txt = txt.lower().strip()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("utf-8")
    txt = re.sub(r"[^\w\s]", "", txt)
    return txt

# ======================
# LOAD PLANT DATA FROM CSV
# ======================
@st.cache_data
def load_listado_plantas():
    df = pd.read_csv("plantas_aucca_30_03_25.csv", sep=";", encoding="latin1").fillna("")
    if "Meses UNIRCADENAS" in df.columns:
        df = df.rename(columns={"Meses UNIRCADENAS": "Meses Siembra (Chile)"})
    for col in ["Disponible Nov 2024", "Familia", "Propiedades", "Categoria", "Nombre vulgar", "Nombre Científico"]:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    df["Nombre total"] = df["Nombre vulgar"] + " (" + df["Nombre Científico"] + ")"
    return df

plantas_df = load_listado_plantas()

# ======================
# SIDEBAR FILTERS
# ======================
st.sidebar.header("Filtros de Plantas")
avail_opts = sorted(set([x for x in plantas_df["Disponible Nov 2024"] if x]))
disp_sel = st.sidebar.selectbox("Disponibilidad en Aucca", options=["Todas"] + avail_opts)
if disp_sel == "Todas":
    plantas_filtradas = plantas_df.copy()
else:
    plantas_filtradas = plantas_df[plantas_df["Disponible Nov 2024"] == disp_sel]

def get_unique_values(df, col):
    vals = df[col].dropna().tolist()
    out = []
    for v in vals:
        for piece in re.split(r"[,\-;]", v):
            w = piece.strip().lower()
            if w and w not in out:
                out.append(w)
    return sorted(out)

mvals = get_unique_values(plantas_filtradas, "Meses Siembra (Chile)")
msel = st.sidebar.multiselect("Meses de Siembra (Chile)", options=mvals, default=[])
if not msel:
    msel = mvals
if len(msel) < len(mvals):
    plantas_filtradas = plantas_filtradas[
        plantas_filtradas["Meses Siembra (Chile)"].apply(lambda x: any(m in x.lower() for m in msel) if x else False)
    ]

cat_vals = get_unique_values(plantas_filtradas, "Categoria")
catsel = st.sidebar.multiselect("Categoría", options=cat_vals, default=[])
if not catsel:
    catsel = cat_vals
if len(catsel) < len(cat_vals):
    plantas_filtradas = plantas_filtradas[
        plantas_filtradas["Categoria"].apply(lambda x: x.lower() in [c.lower() for c in catsel] if x else False)
    ]

fij_vals = sorted(set([x for x in plantas_filtradas["Fijador de Nitrógeno"] if x]))
fij_sel = st.sidebar.selectbox("Fijador de Nitrógeno", options=["Todas"] + fij_vals)
if fij_sel != "Todas":
    plantas_filtradas = plantas_filtradas[plantas_filtradas["Fijador de Nitrógeno"] == fij_sel]

acum_vals = get_unique_values(plantas_filtradas, "Acumulador Dinámico")
acum_sel = st.sidebar.multiselect("Acumulador Dinámico", options=acum_vals, default=[])
if not acum_sel:
    acum_sel = acum_vals
if len(acum_sel) < len(acum_vals):
    plantas_filtradas = plantas_filtradas[
        plantas_filtradas["Acumulador Dinámico"].apply(lambda x: any(a in x.lower() for a in acum_sel) if x else False)
    ]

prop_vals = get_unique_values(plantas_filtradas, "Propiedades")
prop_sel = st.sidebar.multiselect("Propiedades Medicinales", options=prop_vals, default=[])
if not prop_sel:
    prop_sel = prop_vals
if len(prop_sel) < len(prop_vals):
    plantas_filtradas = plantas_filtradas[
        plantas_filtradas["Propiedades"].apply(lambda x: any(p in x.lower() for p in prop_sel) if x else False)
    ]

st.sidebar.markdown(f"**Total de plantas filtradas:** {plantas_filtradas.shape[0]}")

# ======================
# PLANT SUMMARY (Below the search bar)
# ======================
plant_summary_text = ""
if plantas_filtradas.shape[0] < plantas_df.shape[0]:
    arrp = plantas_filtradas["Nombre total"].tolist()
    plant_summary_text = f"Se encontraron {len(arrp)} plantas disponibles: " + ", ".join(arrp)
else:
    plant_summary_text = ""

# ======================
# FUNCTION: DISPLAY PLANT DETAILS (Explorer Format)
# ======================
def display_plant_details(plant):
    st.markdown(f"## {plant.get('Nombre total', '')}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🌿 Identificación")
        for fld in ["Nombre vulgar", "Nombre Científico", "Familia", "Categoria"]:
            st.write(f"**{fld}:** {plant.get(fld, '')}")
        st.markdown("### 🌱 Características y Servicios Ecosistémicos")
        for fld in ["Fijador de Nitrógeno", "Acumulador Dinámico", "Minerales", "Propiedades"]:
            st.write(f"**{fld}:** {plant.get(fld, '')}")
        st.markdown("### 📚 Guía para Cultivo")
        for fld in ["Época de siembra (CHILE)", "Método", "Profundidad de Siembra", "Tiempo de germinar",
                    "Transplante", "Distancia entre (Plantas)", "Distancia entre (hileras)",
                    "Tiempo para cosechar", "Observaciones"]:
            st.write(f"**{fld}:** {plant.get(fld, '')}")
    with c2:
        st.markdown("### 📍 Localización en Aucca")
        lat_str = str(plant.get("lat", "")).strip()
        lon_str = str(plant.get("lon", "")).strip()
        if lat_str and lon_str:
            try:
                la = float(lat_str)
                lo = float(lon_str)
                deck = pdk.Deck(
                    map_style="mapbox://styles/mapbox/satellite-v9",
                    initial_view_state={
                        "latitude": la,
                        "longitude": lo,
                        "zoom": 18.5,
                        "pitch": 0
                    },
                    layers=[
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=[plant],
                            get_position="[lon, lat]",
                            get_color="[255,165,0,160]",
                            get_radius=1
                        )
                    ]
                )
                st.pydeck_chart(deck)
            except Exception as e:
                st.write("Información de ubicación no disponible.")
        else:
            fallback = str(plant.get("ruta mapa", "")).strip()
            if fallback:
                try:
                    im = Image.open(fallback)
                    st.image(im, use_container_width=True)
                except:
                    st.write("Información de ubicación no disponible.")
            else:
                st.write("Información de ubicación no disponible.")




# ======================
# MAIN QUERY AREA
# ======================


import base64
from PIL import Image
from io import BytesIO

# Cargar y codificar la imagen como base64
def image_to_base64(img_path):
    img = Image.open(img_path)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    return img_b64

im_queltehue_b64 = image_to_base64("images/queltehue.png")

# Mostrar imagen y título juntos
st.markdown(f"""
<div style="display: flex; align-items: center;">
    <img src="data:image/png;base64,{im_queltehue_b64}" width="80" style="margin-right: 15px;">
    <h2 style="margin: 0;">Asistente Agroecológico de AUCCA</h2>
</div>
""", unsafe_allow_html=True)

st.markdown("""
Información sobre:  🏡 *AUCCA* · 🌱 *Plantas y cultivo* · 🚽 *Baño Seco* · 💧 *Biofiltro* · ♻️ *Compostaje* · 📚 *Taller huertas*
""")

# ======================
# DISPLAY TEXT SUMMARY IF FILTERS ACTIVE AND NO QUERY
# ======================
filters_active = (
    disp_sel != "Todas" or
    len(msel) < len(mvals) or
    len(catsel) < len(cat_vals) or
    fij_sel != "Todas" or
    len(acum_sel) < len(acum_vals) or
    len(prop_sel) < len(prop_vals)
)

if filters_active and st.session_state.plant_result is None and not st.session_state.last_query.strip():
    nombres = plantas_filtradas["Nombre total"].tolist()
    texto_resultado = f"Se encontraron {len(nombres)} plantas disponibles: " + ", ".join(nombres)
    st.markdown(f"#### 🌿 Resultado del filtro\n\n{texto_resultado}")


user_query = st.text_input("Ingresa tu pregunta o planta...", key="input_field")





# Clear previous results if the query text changes
if user_query != st.session_state.last_query:
    clear_results()
    st.session_state.last_query = user_query

# ======================
# AUTOMATIC SUGGESTIONS (Fuzzy & Exact)
# Only run if no plant result is selected.
# ======================
if st.session_state.plant_result is None and user_query.strip():
    norm_q = normalizar_texto(user_query.strip())
    # Build plant suggestions from filtered data.
    plant_suggestions = []
    for _, row in plantas_filtradas.iterrows():
        full_name = row["Nombre total"]
        if norm_q in normalizar_texto(row["Nombre vulgar"]) or norm_q in normalizar_texto(full_name):
            plant_suggestions.append(full_name)
    plant_suggestions = list(set(plant_suggestions))
    if plant_suggestions:
        st.markdown("### Sugerencias de Plantas:")
        for plant in plant_suggestions:
            if st.button(plant, key=f"btn_plant_{plant}"):
                selected = plantas_filtradas[plantas_filtradas["Nombre total"] == plant].iloc[0].to_dict()
                st.session_state.plant_result = selected
                st.session_state.result_display = ""
                st.session_state.related_expander = ""
                # Do not force a re-run now so that the plant_result persists.
    # Build concept suggestions from the knowledge base.
    concept_suggestions = []
    for key in base_conocimiento.keys():
        if norm_q in normalizar_texto(key):
            concept_suggestions.append(key)
    if concept_suggestions:
        st.markdown("#### 💡 Sugerencias de Conceptos:")

        # Grid settings
        cols_per_row = 6  # You can set to 4 or 5 if you prefer
        rows = [concept_suggestions[i:i+cols_per_row] for i in range(0, len(concept_suggestions), cols_per_row)]

        for row in rows:
            cols = st.columns(len(row))
            for i, concept in enumerate(row):
                with cols[i]:
                    # Custom styled button
                    btn_style = f"""
                    <style>
                        div[data-testid="stButton"] > button#{f"btn_concept_{concept}"} {{
                            background-color: #FF37D5;
                            color: white;
                            border-radius: 8px;
                            border: none;
                            padding: 0.5em 1em;
                            font-weight: bold;
                        }}
                        div[data-testid="stButton"] > button#{f"btn_concept_{concept}"}:hover {{
                            background-color: #C837A1;
                        }}
                    </style>
                    """
                    st.markdown(btn_style, unsafe_allow_html=True)

                if st.button(f"🔎 {concept.capitalize()}", key=f"btn_concept_{concept}"):
                    st.session_state.result_display = f"### 🧠 Respuesta principal:\n\n**{concept.capitalize()}**\n\n{base_conocimiento.get(concept, '')}"
                    st.session_state.plant_result = None

                    # Store related content as a list of (question, answer)
                    related_list = []
                    for cat, cat_dict in knowledge.items():
                        if concept in cat_dict:
                            related_list = [(q, a) for q, a in cat_dict.items() if q != concept]
                            break

                    # Store related content for display (in callback-compatible way)
                    related_md = ["### 📚 Información relacionada:"]
                    for q, a in related_list:
                        related_md.append(f"**🔹 {q.capitalize()}**\n\n{a}")
                    st.session_state.related_expander = "\n\n".join(related_md)

                                        
                    



# ======================
# PROCESS QUERY WHEN "Enviar" IS CLICKED (Only if no plant is selected)
# ======================
if st.session_state.plant_result is None and st.button("Enviar", key="send_btn"):
    q = user_query.strip()
    if q:
        norm_q = normalizar_texto(q)
        # Check if a month is mentioned.
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        month_found = None
        for m in months:
            if m in norm_q:
                month_found = m
                break
        if month_found:
            pmatches = plantas_filtradas[
                plantas_filtradas["Meses Siembra (Chile)"].str.lower().str.contains(month_found, na=False)
            ].to_dict(orient="records")
        elif "frutales" in norm_q:
            pmatches = plantas_filtradas[
                plantas_filtradas["Categoria"].str.lower().str.contains("frutales", na=False)
            ].to_dict(orient="records")
        else:
            pmatches = []
            for _, row in plantas_filtradas.iterrows():
                if norm_q in normalizar_texto(row["Nombre vulgar"]) or norm_q in normalizar_texto(row["Nombre total"]):
                    pmatches.append(row.to_dict())
        if pmatches:
            if len(pmatches) == 1:
                st.session_state.plant_result = pmatches[0]
            else:
                st.markdown("### Se encontraron varias plantas:")
                for plant in pmatches:
                    if st.button(plant["Nombre total"], key=f"exbtn_{plant['Nombre total']}"):
                        st.session_state.plant_result = plant
                        st.session_state.result_display = ""
                        st.session_state.related_expander = ""
        else:
            # Fuzzy matching if no exact match is found.
            all_names = plantas_filtradas["Nombre total"].tolist()
            fuzzy_matches = difflib.get_close_matches(q, all_names, n=5, cutoff=0.5)
            if fuzzy_matches:
                st.markdown("No se encontró coincidencia exacta. ¿Quizás quisiste decir:")
                for alt in fuzzy_matches:
                    if st.button(alt, key=f"fuzzy_{alt}"):
                        candidate = plantas_filtradas[plantas_filtradas["Nombre total"] == alt].iloc[0].to_dict()
                        st.session_state.plant_result = candidate
                        st.session_state.result_display = ""
                        st.session_state.related_expander = ""
            else:
                # Concept approach based on keywords.
                cat_kws = {
                    "biofiltro": ["biofiltro"],
                    "baño": ["baño", "seco"],
                    "compost": ["compost", "lombricultura"],
                    "general": ["aucca", "ubicacion", "mision", "historia", "objetivos", "talleres", "beneficiarios", "contacto"],
                    "taller": ["agricultura", "revolucion", "transgenicos", "huerta"]
                }
                matched_cat = None
                for cat, kws in cat_kws.items():
                    for wd in kws:
                        if wd in norm_q:
                            matched_cat = cat
                            break
                    if matched_cat:
                        break
                if matched_cat and matched_cat in knowledge:
                    cat_dict = knowledge[matched_cat]
                    first_k = list(cat_dict.keys())[0]

                    st.session_state.result_display = f"### 🧠 Respuesta principal:\n\n**{first_k.capitalize()}**\n\n{cat_dict[first_k]}"

                    # ✅ DEFINIR related_list antes de usarla
                    related_list = [(q, a) for q, a in cat_dict.items() if q != first_k]

                    related_md = ["### 📚 Información relacionada:"]
                    for q, a in related_list:
                        related_md.append(f"**🔹 {q.capitalize()}**\n\n{a}")
                    st.session_state.related_expander = "\n\n".join(related_md)


                else:
                    found = False
                    for kb_key, kb_val in base_conocimiento.items():
                        if norm_q in normalizar_texto(kb_key):
                            st.session_state.result_display = f"### 🧠 Respuesta principal:\n\n**{kb_key.capitalize()}**\n\n{kb_val}"
                            st.session_state.related_expander = ""
                            found = True
                            break

                    if not found:
                        keys_norm = {normalizar_texto(k): k for k in base_conocimiento.keys()}
                        close_concepts = difflib.get_close_matches(norm_q, list(keys_norm.keys()), n=1, cutoff=0.5)

                        if close_concepts:
                            best_match = keys_norm[close_concepts[0]]
                            st.session_state.result_display = f"### 🧠 Quizás quisiste decir:\n\n**{best_match.capitalize()}**\n\n{base_conocimiento[best_match]}"
                            # Mostrar relacionadas si aplica
                            related_list = []
                            for cat, cat_dict in knowledge.items():
                                if best_match in cat_dict:
                                    related_list = [(q, a) for q, a in cat_dict.items() if q != best_match]
                                    break
                            related_md = ["### 📚 Información relacionada:"]
                            for q, a in related_list:
                                related_md.append(f"**🔹 {q.capitalize()}**\n\n{a}")
                            st.session_state.related_expander = "\n\n".join(related_md)
                            found = True

                    if not found:
                        st.session_state.result_display = (
                            "Lo siento, no tengo información sobre eso. "
                            "Puedes preguntar por agroecología, compostaje, baños secos, biofiltros o escribir el nombre de una planta."
                        )
                        st.session_state.related_expander = ""




# ======================
# DISPLAY RESULTS
# ======================
if st.session_state.plant_result is not None:
    display_plant_details(st.session_state.plant_result)
elif st.session_state.result_display:
    st.markdown(st.session_state.result_display)

    # Mostrar "Leer más" SIEMPRE que haya una respuesta, aunque no tenga contenido relacionado
    with st.expander("Leer más", expanded=True):
        if st.session_state.related_expander.strip():
            st.markdown(st.session_state.related_expander, unsafe_allow_html=False)
        else:
            st.markdown("_No hay información adicional relacionada disponible._")
            
