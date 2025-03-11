import streamlit as st
import pandas as pd
import datetime
import requests
import json
import os
from fpdf import FPDF
import base64

# Configuración de la página con nuevo ícono de psicología
st.set_page_config(
    page_title="Evaluación Psicológica para Procedimiento Bariátrico",
    page_icon="⚕️",  # Cambio de ícono a símbolo médico/psicología
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 20px;
        text-align: center;
    }
    .section-header {
        font-size: 20px;
        font-weight: bold;
        color: #1E3A8A;
        margin-top: 30px;
        margin-bottom: 15px;
        background-color: #F3F4F6;
        padding: 10px;
        border-radius: 5px;
    }
    .info-box {
        background-color: #E1EFFE;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .stButton > button {
        background-color: #1E3A8A;
        color: white;
        font-weight: bold;
    }
    
    /* Estilo para mejorar la visualización de tablas en PDF */
    .pdf-table {
        width: 100%;
        border-collapse: collapse;
    }
    .pdf-table th, .pdf-table td {
        border: 1px solid #ddd;
        padding: 8px;
    }
    .pdf-table th {
        background-color: #f2f2f2;
    }
</style>
""", unsafe_allow_html=True)

# Función para mejorar el texto con la API de Anthropic
def mejorar_texto_con_anthropic(texto_original, api_key):
    # Código original sin cambios
    if not api_key or not texto_original:
        return texto_original, "Se requiere una API key válida y texto para procesar."
    
    try:
        headers = {
            "x-api-key": api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": f"Por favor, corrige errores gramaticales y mejora la redacción del siguiente texto para un informe psicológico, manteniendo toda la información original pero haciéndolo más profesional y claro:\n\n{texto_original}"}
            ]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data["content"][0]["text"], None
        else:
            return texto_original, f"Error al procesar el texto: {response.status_code} - {response.text}"
    
    except Exception as e:
        return texto_original, f"Error al conectar con la API: {str(e)}"

# Función para generar el informe en PDF mejorado con mejor uso del espacio horizontal
def generar_pdf(datos):
    # Limpieza y validación de datos
    datos_limpios = {}
    
    # Asegurar que todos los campos existan con valores predeterminados
    for campo in [
        'nombre_completo', 'run', 'fecha_nacimiento', 'edad', 'email', 'telefono',
        'domicilio', 'prevision', 'escolaridad', 'ocupacion', 'sexo', 'psicologa',
        'datos_procedimiento', 'fecha_procedimiento', 'familia_nuclear',
        'situacion_conyugal_padres', 'estado_civil', 'hijos', 'redes_apoyo',
        'enfermedades_familia', 'antecedentes_natales', 'enfermedades_infancia',
        'enfermedades_actuales', 'operaciones', 'antecedentes_salud_mental',
        'estado_salud_mental', 'repitencias', 'rendimiento_academico',
        'comportamiento_escolar', 'consumo_alcohol', 'consumo_tabaco',
        'consumo_marihuana', 'consumo_otras_drogas', 'peso_maximo', 'peso_minimo',
        'peso_ideal', 'altura', 'arfid', 'comedor_emocional', 'anorexia',
        'comedor_nocturno', 'bulimia', 'picoteador', 't_atracon', 'food_craving',
        'factores_origen', 'razones_cambiar', 'paciente_apto', 'observaciones',
        'rut_psicologa'
    ]:
        if campo not in datos or datos[campo] is None:
            datos_limpios[campo] = ""
        else:
            # Convertir números a strings para seguridad
            if isinstance(datos[campo], (int, float)):
                datos_limpios[campo] = str(datos[campo])
            else:
                datos_limpios[campo] = datos[campo]
    
    # Limpieza específica de textos de la API
    for campo in ['antecedentes_natales', 'factores_origen', 'razones_cambiar', 'observaciones']:
        texto = datos_limpios[campo]
        
        # Eliminar frases como "Aquí está el texto corregido" y similares
        frases_a_eliminar = [
            "Aquí está el texto corregido y mejorado:",
            "El texto se puede reformular",
            "Esta versión reformulada",
            "Informe Psicológico",
            "La redacción es más clara",
            "A continuación, presento una versión revisada"
        ]
        
        for frase in frases_a_eliminar:
            if frase in texto:
                texto = texto.replace(frase, "").strip()
        
        # Si sigue siendo muy largo o tiene estructura extraña, usar un valor predeterminado
        if not texto.strip():
            if campo == 'antecedentes_natales':
                texto = "Sin antecedentes relevantes."
            elif campo == 'factores_origen':
                texto = "Se identifican factores relacionados con hábitos alimenticios inadecuados."
            elif campo == 'razones_cambiar':
                texto = "Mejorar calidad de vida y estado de salud general."
            elif campo == 'observaciones':
                texto = "Sin observaciones relevantes que destacar."
        
        datos_limpios[campo] = texto
    
    # Definir clase PDF con métodos mejorados
    class PDF(FPDF):
        def header(self):
        # Verificar si estamos en la primera página
            if self.page_no() == 1:
                self.set_font('Arial', 'B', 15)
                self.cell(0, 10, 'INFORME PSICOLÓGICO PARA PROCEDIMIENTO BARIÁTRICO', 0, 1, 'C')
                self.ln(2)  # Reducido espacio para aprovechar mejor el área
    
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
    
        def add_section_title(self, title):
            self.set_font('Arial', 'B', 12)
            self.ln(5)
            self.cell(0, 10, title, 0, 1)
            self.ln(2)
        
        def check_page_break(self, height=30):
            """Verifica si hay suficiente espacio en la página actual, si no, añade una nueva página."""
            if self.get_y() > self.h - height:
                self.add_page()
        
        # Método para campos emparejados con espaciado explícito
        def add_field_pair(self, label1, value1, label2, value2, col1_x=10, val1_x=55, col2_x=110, val2_x=145):
            """Crea un par de campos con posicionamiento flexible."""
            y_pos = self.get_y()
    
    # Primera etiqueta
            self.set_font('Arial', 'B', 10)
            self.set_xy(col1_x, y_pos)
            self.cell(val1_x - col1_x, 6, label1, 0, 0)
    
    # Primer valor
            self.set_font('Arial', '', 10)
            self.set_xy(val1_x, y_pos)
            self.cell(col2_x - val1_x, 6, " " + str(value1), 0, 0)
    
    # Segunda etiqueta
            self.set_font('Arial', 'B', 10)
            self.set_xy(col2_x, y_pos)
            self.cell(val2_x - col2_x, 6, label2, 0, 0)
    
    # Segundo valor
            self.set_font('Arial', '', 10)
            self.set_xy(val2_x, y_pos)
            self.cell(0, 6, " " + str(value2), 0, 1)
    
            return self.get_y()
        # Para textos largos con etiqueta
        def add_long_field(self, label, value):
            # Etiqueta en línea separada
            self.set_font('Arial', 'B', 10)
            self.cell(0, 6, label, 0, 1)
            
            # Valor
            self.set_font('Arial', '', 10)
            self.multi_cell(0, 6, value, 0, 'L')
            self.ln(2)
        
        # Crear tabla mejorada
        def add_table(self, headers, data, widths=None):
            if widths is None:
                page_width = self.w - 20
                widths = [page_width / len(headers)] * len(headers)
            
            # Encabezados
            self.set_font('Arial', 'B', 10)
            self.set_fill_color(240, 240, 240)
            
            for i, header in enumerate(headers):
                self.cell(widths[i], 8, header, 1, 0, 'C', 1)
            self.ln()
            
            # Datos
            self.set_font('Arial', '', 10)
            for row in data:
                for i, cell in enumerate(row):
                    self.cell(widths[i], 8, str(cell), 1, 0, 'C')
                self.ln()
            
            self.ln(4)
        
        def formatear_rut(self, rut):
            if not rut or not isinstance(rut, str) or len(rut.strip()) < 2:
                return ""
                
            rut = rut.replace(".", "").replace("-", "").strip()
            if len(rut) < 2:
                return rut
                
            dv = rut[-1]
            num = rut[:-1]
            
            formato = ""
            while len(num) > 3:
                formato = "." + num[-3:] + formato
                num = num[:-3]
            formato = num + formato
            
            return formato + "-" + dv
    
    # Generar el PDF con la nueva estructura
    pdf = PDF()
    pdf.add_page()
    
    # Datos del paciente
    pdf.add_section_title('I. DATOS DEL PACIENTE')
    
    # Usar posicionamiento absoluto para garantizar alineación
    pdf.add_field_pair("Nombre:", datos_limpios['nombre_completo'], 
                     "RUN:", pdf.formatear_rut(datos_limpios['run']))
    
    pdf.add_field_pair("F. Nac.:", datos_limpios['fecha_nacimiento'], 
                     "Edad:", f"{datos_limpios['edad']} Años")
    
    pdf.add_field_pair("Email:", datos_limpios['email'], 
                     "Teléfono:", datos_limpios['telefono'])
    
    # Domicilio (campo individual)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 6, "Domicilio:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, datos_limpios['domicilio'], 0, 1)
    
    pdf.add_field_pair("Previsión:", datos_limpios['prevision'], 
                     "Escolaridad:", datos_limpios['escolaridad'])
    
    pdf.add_field_pair("Profesión:", datos_limpios['ocupacion'], 
                     "Sexo:", datos_limpios['sexo'])
    
    # Psicóloga (campo individual)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 6, "Psicóloga:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, datos_limpios['psicologa'], 0, 1)
    
    pdf.add_field_pair("Procedimiento:", datos_limpios['datos_procedimiento'], 
                     "Fecha:", datos_limpios['fecha_procedimiento'])
    
    # Antecedentes familiares
    pdf.add_section_title('II. ANTECEDENTES FAMILIARES')
    
    # Familia nuclear
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 6, "Familia Nuclear:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, datos_limpios['familia_nuclear'], 0, 1)
    
    pdf.add_field_pair("Estado Civil Padres:", datos_limpios['situacion_conyugal_padres'], 
                     "Estado Civil:", datos_limpios['estado_civil'])
    
    pdf.add_field_pair("Hijos:", datos_limpios['hijos'], 
                     "Redes de Apoyo:", datos_limpios['redes_apoyo'])
    
    # Enfermedades familiares (etiqueta larga en línea separada)
    pdf.add_long_field("Enfermedades de importancia/Trastornos mentales/Adicciones familiares:", 
                     datos_limpios['enfermedades_familia'])
    
    # Antecedentes mórbidos
    pdf.check_page_break()
    pdf.add_section_title('III. ANTECEDENTES MÓRBIDOS')
    
    pdf.add_long_field("Antecedentes pre, peri y post natales:", 
                     datos_limpios['antecedentes_natales'])
    
    pdf.add_long_field("Enfermedades importantes en infancia y adolescencia:", 
                     datos_limpios['enfermedades_infancia'])
    
    pdf.add_long_field("Enfermedades actuales:", 
                     datos_limpios['enfermedades_actuales'])
    
    pdf.add_long_field("Operaciones:", datos_limpios['operaciones'])
    
    # Estado de salud mental
    pdf.check_page_break()
    pdf.add_section_title('IV. ESTADO DE SALUD MENTAL')
    
    pdf.add_long_field("Antecedentes de Salud Mental:", 
                     datos_limpios['antecedentes_salud_mental'])
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 6, "Estado de salud mental:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, datos_limpios['estado_salud_mental'], 0, 1)
    
    # Historia escolar
    pdf.check_page_break()
    pdf.add_section_title('V. HISTORIA ESCOLAR')
    
    pdf.add_field_pair("Repitencias:", datos_limpios['repitencias'], 
                 "Rendimiento Académico:", datos_limpios['rendimiento_academico'],
                 col2_x=90, val2_x=135)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 6, "Comportamiento Escolar:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, datos_limpios['comportamiento_escolar'], 0, 1)
    
    # Abuso o dependencias de sustancias
    pdf.check_page_break()
    pdf.add_section_title('VI. ABUSO O DEPENDENCIAS DE SUSTANCIAS')
    
    # Tabla de sustancias
    headers = ["Sustancia", "Consumo"]
    data = [
        ["Alcohol", datos_limpios['consumo_alcohol']],
        ["Tabaco", datos_limpios['consumo_tabaco']],
        ["Marihuana", datos_limpios['consumo_marihuana']],
        ["Otras drogas", datos_limpios['consumo_otras_drogas']]
    ]
    widths = [75, 105]
    
    pdf.add_table(headers, data, widths)
    
    # Trastornos de la conducta alimentarios
    pdf.check_page_break()
    pdf.add_section_title('VII. TRASTORNOS DE LA CONDUCTA ALIMENTARIOS')
    
    # Datos de peso y altura - todos en la misma página
    pdf.add_field_pair("Peso máximo:", f"{datos_limpios['peso_maximo']} kg", 
                     "Peso mínimo:", f"{datos_limpios['peso_minimo']} kg")
    
    pdf.add_field_pair("Peso ideal:", f"{datos_limpios['peso_ideal']} kg", 
                     "Altura:", f"{datos_limpios['altura']} m")
    
    # Tabla de trastornos
    pdf.ln(4)
    headers = ["Trastorno", "Estado", "Trastorno", "Estado"]
    data = [
        ["ARFID", datos_limpios['arfid'], "Comedor Emocional", datos_limpios['comedor_emocional']],
        ["Anorexia Nerviosa", datos_limpios['anorexia'], "Comedor Nocturno", datos_limpios['comedor_nocturno']],
        ["Bulimia Nerviosa", datos_limpios['bulimia'], "Picoteador", datos_limpios['picoteador']],
        ["Trastorno por Atracón", datos_limpios['t_atracon'], "Food Craving", datos_limpios['food_craving']]
    ]
    widths = [55, 25, 55, 45]
    
    pdf.add_table(headers, data, widths)
    
    # Consciencia del problema
    pdf.add_page()  # Nueva página para esta sección importante
    pdf.add_section_title('VIII. CONSCIENCIA DEL PROBLEMA Y NIVEL DE MOTIVACIÓN PARA EL CAMBIO')
    
    pdf.add_long_field("Análisis de factores que dieron origen y perpetúan el problema:", 
                     datos_limpios['factores_origen'])
    
    pdf.add_long_field("Razones para cambiar:", datos_limpios['razones_cambiar'])
    
    # Paciente apto destacado
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(60, 6, "Paciente apto para procedimiento:", 0, 0)
    pdf.set_font('Arial', 'B', 12)  # Más grande para destacar
    pdf.cell(0, 6, datos_limpios['paciente_apto'], 0, 1)
    
    # Observaciones
    pdf.ln(5)
    pdf.add_section_title('IX. OBSERVACIONES')
    
    if datos_limpios['observaciones']:
        pdf.multi_cell(0, 6, datos_limpios['observaciones'], 0, 'L')
    else:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, "Sin observaciones relevantes que destacar.", 0, 1)
    
    # Firma y datos de la psicóloga
    pdf.ln(20)
    
    # Línea para firma
    x_center = pdf.w / 2
    pdf.line(x_center - 35, pdf.get_y(), x_center + 35, pdf.get_y())
    pdf.ln(5)
    
    # Datos de la psicóloga
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, datos_limpios['psicologa'], 0, 1, 'C')
    
    if datos_limpios['rut_psicologa']:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Rut: {pdf.formatear_rut(datos_limpios['rut_psicologa'])}", 0, 1, 'C')
    else:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, "Rut:", 0, 1, 'C')
    
    pdf.cell(0, 6, "Psicóloga", 0, 1, 'C')
    
    # Generar el PDF
    return pdf.output(dest='S').encode('latin1')

# Función para descargar el PDF
def get_pdf_download_link(pdf_bytes, filename):
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Descargar Informe PDF</a>'
    return href

# Inicializar el estado de la sesión
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'anthropic_response' not in st.session_state:
    st.session_state.anthropic_response = None
if 'anthropic_error' not in st.session_state:
    st.session_state.anthropic_error = None
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None

# Función para avanzar al siguiente paso
def next_step():
    st.session_state.step += 1

# Función para retroceder al paso anterior
def prev_step():
    st.session_state.step -= 1

# Encabezado principal
st.markdown('<div class="main-header">EVALUACIÓN PSICOLÓGICA PARA PROCEDIMIENTO BARIÁTRICO</div>', unsafe_allow_html=True)

# Barra lateral para navegación y configuración
with st.sidebar:
    
    st.image("https://cdn-icons-png.flaticon.com/512/4076/4076478.png", width=100)  # Ícono de psicología/salud mental
    st.markdown("### Navegación")
    if st.button("Datos del Paciente", disabled=st.session_state.step == 1):
        st.session_state.step = 1
    if st.button("Antecedentes Familiares", disabled=st.session_state.step == 2):
        st.session_state.step = 2
    if st.button("Antecedentes Mórbidos", disabled=st.session_state.step == 3):
        st.session_state.step = 3
    if st.button("Salud Mental", disabled=st.session_state.step == 4):
        st.session_state.step = 4
    if st.button("Historia Escolar", disabled=st.session_state.step == 5):
        st.session_state.step = 5
    if st.button("Abuso de Sustancias", disabled=st.session_state.step == 6):
        st.session_state.step = 6
    if st.button("Trastornos Alimentarios", disabled=st.session_state.step == 7):
        st.session_state.step = 7
    if st.button("Motivación para el Cambio", disabled=st.session_state.step == 8):
        st.session_state.step = 8
    if st.button("Revisión y Generación", disabled=st.session_state.step == 9):
        st.session_state.step = 9
    
    st.divider()
    
    st.markdown("### Configuración API")
    api_key = st.text_input("API Key de Anthropic", type="password", help="Introduce tu API key de Anthropic para mejorar la redacción")
    
    st.divider()
    
    st.markdown("### Acerca de")
    st.markdown("Esta aplicación ayuda a los profesionales de la psicología a realizar evaluaciones para procedimientos bariátricos, siguiendo un formato estandarizado.")

# PASO 1: DATOS DEL PACIENTE
if st.session_state.step == 1:
    st.markdown('<div class="section-header">I. DATOS DEL PACIENTE</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        nombre_completo = st.text_input("Nombre Completo", value=st.session_state.form_data.get('nombre_completo', ''))
        fecha_nacimiento = st.date_input("Fecha de Nacimiento", value=datetime.datetime.strptime(st.session_state.form_data.get('fecha_nacimiento', '25 Mayo 1982'), '%d %B %Y') if 'fecha_nacimiento' in st.session_state.form_data else datetime.date(1982, 5, 25), format="DD/MM/YYYY")
        domicilio = st.text_input("Domicilio", value=st.session_state.form_data.get('domicilio', ''))
        email = st.text_input("Email", value=st.session_state.form_data.get('email', ''))
        fecha_evaluacion = st.date_input("Fecha de Evaluación", value=datetime.datetime.strptime(st.session_state.form_data.get('fecha_evaluacion', '14-02-2025'), '%d-%m-%Y') if 'fecha_evaluacion' in st.session_state.form_data else datetime.date.today(), format="DD/MM/YYYY")
        escolaridad = st.selectbox("Escolaridad", ["Básica Incompleta", "Básica Completa", "Media Incompleta", "Media Completa", "Técnica Incompleta", "Técnica Completa", "Universitaria Incompleta", "Universitaria Completa"], index=["Básica Incompleta", "Básica Completa", "Media Incompleta", "Media Completa", "Técnica Incompleta", "Técnica Completa", "Universitaria Incompleta", "Universitaria Completa"].index(st.session_state.form_data.get('escolaridad', "Media Completa")))
        sexo = st.selectbox("Sexo", ["Femenino", "Masculino", "No Binario", "Prefiero no decir"], index=["Femenino", "Masculino", "No Binario", "Prefiero no decir"].index(st.session_state.form_data.get('sexo', "Femenino")))
    
    with col2:
        run = st.text_input("R.U.N.", value=st.session_state.form_data.get('run', ''))
        # Calcular edad automáticamente
        today = datetime.date.today()
        edad = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        st.text_input("Edad (años)", value=str(edad), disabled=True)
        telefono = st.text_input("Teléfono", value=st.session_state.form_data.get('telefono', ''))
        prevision = st.selectbox("Previsión", ["Fonasa", "Isapre", "Particular", "Otra"], index=["Fonasa", "Isapre", "Particular", "Otra"].index(st.session_state.form_data.get('prevision', "Fonasa")))
        ocupacion = st.text_input("Profesión/Ocupación", value=st.session_state.form_data.get('ocupacion', ''))
        psicologa = st.text_input("Psicólogo/a", value=st.session_state.form_data.get('psicologa', ''))
        rut_psicologa = st.text_input("RUT Psicólogo/a", value=st.session_state.form_data.get('rut_psicologa', ''))
    
    st.markdown("#### Datos del Procedimiento")
    col1, col2 = st.columns(2)
    
    with col1:
        datos_procedimiento = st.text_input("Procedimiento y Doctor", value=st.session_state.form_data.get('datos_procedimiento', ''))
    
    with col2:
        fecha_procedimiento = st.text_input("Fecha/Estado", value=st.session_state.form_data.get('fecha_procedimiento', 'En evaluación'))
    
    # Guardar datos en la sesión
    if st.button("Continuar"):
        st.session_state.form_data.update({
            'nombre_completo': nombre_completo,
            'run': run,
            'fecha_nacimiento': fecha_nacimiento.strftime('%d %B %Y'),
            'edad': edad,
            'domicilio': domicilio,
            'email': email,
            'telefono': telefono,
            'fecha_evaluacion': fecha_evaluacion.strftime('%d-%m-%Y'),
            'prevision': prevision,
            'escolaridad': escolaridad,
            'ocupacion': ocupacion,
            'sexo': sexo,
            'psicologa': psicologa,
            'rut_psicologa': rut_psicologa,
            'datos_procedimiento': datos_procedimiento,
            'fecha_procedimiento': fecha_procedimiento
        })
        next_step()

# PASO 2: ANTECEDENTES FAMILIARES
elif st.session_state.step == 2:
    st.markdown('<div class="section-header">II. ANTECEDENTES FAMILIARES</div>', unsafe_allow_html=True)
    
    familia_nuclear = st.text_area("Familia Nuclear (composición)", value=st.session_state.form_data.get('familia_nuclear', ''), height=100)
    
    col1, col2 = st.columns(2)
    
    with col1:
        situacion_conyugal_padres = st.selectbox("Situación Conyugal de los Padres", ["Casados", "Separados", "Divorciados", "Viudo/a", "Convivencia", "No Aplica"], index=["Casados", "Separados", "Divorciados", "Viudo/a", "Convivencia", "No Aplica"].index(st.session_state.form_data.get('situacion_conyugal_padres', "Casados")))
        estado_civil = st.selectbox("Estado Civil del Paciente", ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Convivencia"], index=["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Convivencia"].index(st.session_state.form_data.get('estado_civil', "Soltero/a")))
    
    with col2:
        hijos = st.number_input("Número de Hijos", min_value=0, value=int(st.session_state.form_data.get('hijos', 0)))
        redes_apoyo = st.text_input("Redes de Apoyo", value=st.session_state.form_data.get('redes_apoyo', ''))
    
    enfermedades_familia = st.text_area("¿Existe alguna enfermedad de importancia en la familia? ¿Trastornos mentales y/o adicciones?", value=st.session_state.form_data.get('enfermedades_familia', 'Sin antecedentes relevantes.'), height=100)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Atrás"):
            prev_step()
    
    with col2:
        if st.button("Continuar", key="continuar_2"):
            st.session_state.form_data.update({
                'familia_nuclear': familia_nuclear,
                'situacion_conyugal_padres': situacion_conyugal_padres,
                'estado_civil': estado_civil,
                'hijos': hijos,
                'redes_apoyo': redes_apoyo,
                'enfermedades_familia': enfermedades_familia
            })
            next_step()

# PASO 3: ANTECEDENTES MÓRBIDOS
elif st.session_state.step == 3:
    st.markdown('<div class="section-header">III. ANTECEDENTES MÓRBIDOS</div>', unsafe_allow_html=True)
    
    antecedentes_natales = st.text_area("Antecedentes pre, peri y post natales", value=st.session_state.form_data.get('antecedentes_natales', ''), height=150)
    enfermedades_infancia = st.text_area("Enfermedades importantes en la infancia y adolescencia", value=st.session_state.form_data.get('enfermedades_infancia', 'Sin antecedentes relevantes.'), height=100)
    enfermedades_actuales = st.text_area("Enfermedades actuales", value=st.session_state.form_data.get('enfermedades_actuales', 'Sin antecedentes relevantes.'), height=100)
    operaciones = st.text_area("Operaciones", value=st.session_state.form_data.get('operaciones', ''), height=100)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Atrás", key="atras_3"):
            prev_step()
    
    with col2:
        if st.button("Continuar", key="continuar_3"):
            st.session_state.form_data.update({
                'antecedentes_natales': antecedentes_natales,
                'enfermedades_infancia': enfermedades_infancia,
                'enfermedades_actuales': enfermedades_actuales,
                'operaciones': operaciones
            })
            next_step()

# PASO 4: ESTADO DE SALUD MENTAL
elif st.session_state.step == 4:
    st.markdown('<div class="section-header">IV. ESTADO DE SALUD MENTAL</div>', unsafe_allow_html=True)
    
    antecedentes_salud_mental = st.text_area("Antecedentes de Salud Mental", value=st.session_state.form_data.get('antecedentes_salud_mental', '-'), height=150)
    
    estado_salud_mental = st.selectbox("Estado de salud mental", ["Estable", "Inestable", "En tratamiento", "Otro"], index=["Estable", "Inestable", "En tratamiento", "Otro"].index(st.session_state.form_data.get('estado_salud_mental', "Estable")))
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Atrás", key="atras_4"):
            prev_step()
    
    with col2:
        if st.button("Continuar", key="continuar_4"):
            st.session_state.form_data.update({
                'antecedentes_salud_mental': antecedentes_salud_mental,
                'estado_salud_mental': estado_salud_mental
            })
            next_step()

# PASO 5: HISTORIA ESCOLAR
elif st.session_state.step == 5:
    st.markdown('<div class="section-header">V. HISTORIA ESCOLAR</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        repitencias = st.radio("Repitencias", ["No", "Sí"], index=0 if st.session_state.form_data.get('repitencias', "No") == "No" else 1)
    
    with col2:
        rendimiento_academico = st.selectbox("Rendimiento Académico", ["Excelente", "Bueno", "Regular", "Deficiente"], index=["Excelente", "Bueno", "Regular", "Deficiente"].index(st.session_state.form_data.get('rendimiento_academico', "Excelente")))
    
    with col3:
        comportamiento_escolar = st.selectbox("Comportamiento Escolar", ["Excelente", "Bueno", "Regular", "Deficiente"], index=["Excelente", "Bueno", "Regular", "Deficiente"].index(st.session_state.form_data.get('comportamiento_escolar', "Bueno")))
    
    if repitencias == "Sí":
        repitencias_detalles = st.text_area("Detalle las repitencias (cursos, motivos)", value=st.session_state.form_data.get('repitencias_detalles', ''), height=100)
    else:
        repitencias_detalles = ""
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Atrás", key="atras_5"):
            prev_step()
    
    with col2:
        if st.button("Continuar", key="continuar_5"):
            st.session_state.form_data.update({
                'repitencias': repitencias,
                'repitencias_detalles': repitencias_detalles,
                'rendimiento_academico': rendimiento_academico,
                'comportamiento_escolar': comportamiento_escolar
            })
            next_step()

# PASO 6: ABUSO O DEPENDENCIAS DE SUSTANCIAS
elif st.session_state.step == 6:
    st.markdown('<div class="section-header">VI. ABUSO O DEPENDENCIAS DE SUSTANCIAS</div>', unsafe_allow_html=True)
    
    st.markdown("#### Ingestión de:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        consumo_alcohol = st.radio("Alcohol", ["No", "Sí", "Ocasionalmente"], index=2 if st.session_state.form_data.get('consumo_alcohol', "Ocasionalmente") == "Ocasionalmente" else (1 if st.session_state.form_data.get('consumo_alcohol', "No") == "Sí" else 0))
        if consumo_alcohol != "No":
            detalles_alcohol = st.text_input("Detalles del consumo de alcohol", value=st.session_state.form_data.get('detalles_alcohol', 'Piña colada o Pisco sour'))
        else:
            detalles_alcohol = ""
        
        consumo_marihuana = st.radio("Marihuana", ["No", "Sí", "Ocasionalmente"], index=2 if st.session_state.form_data.get('consumo_marihuana', "No") == "Ocasionalmente" else (1 if st.session_state.form_data.get('consumo_marihuana', "No") == "Sí" else 0))
        if consumo_marihuana != "No":
            detalles_marihuana = st.text_input("Detalles del consumo de marihuana", value=st.session_state.form_data.get('detalles_marihuana', ''))
        else:
            detalles_marihuana = ""
    
    with col2:
        consumo_tabaco = st.radio("Tabaco", ["No", "Sí", "Ocasionalmente"], index=2 if st.session_state.form_data.get('consumo_tabaco', "No") == "Ocasionalmente" else (1 if st.session_state.form_data.get('consumo_tabaco', "No") == "Sí" else 0))
        if consumo_tabaco != "No":
            detalles_tabaco = st.text_input("Detalles del consumo de tabaco", value=st.session_state.form_data.get('detalles_tabaco', ''))
        else:
            detalles_tabaco = ""
        
        consumo_otras_drogas = st.radio("Otras drogas", ["No", "Sí"], index=1 if st.session_state.form_data.get('consumo_otras_drogas', "No") == "Sí" else 0)
        if consumo_otras_drogas == "Sí":
            detalles_otras_drogas = st.text_input("Especifique otras drogas", value=st.session_state.form_data.get('detalles_otras_drogas', ''))
        else:
            detalles_otras_drogas = ""
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Atrás", key="atras_6"):
            prev_step()
    
    with col2:
        if st.button("Continuar", key="continuar_6"):
            st.session_state.form_data.update({
                'consumo_alcohol': consumo_alcohol,
                'detalles_alcohol': detalles_alcohol,
                'consumo_tabaco': consumo_tabaco,
                'detalles_tabaco': detalles_tabaco,
                'consumo_marihuana': consumo_marihuana,
                'detalles_marihuana': detalles_marihuana,
                'consumo_otras_drogas': consumo_otras_drogas,
                'detalles_otras_drogas': detalles_otras_drogas
            })
            next_step()

# PASO 7: TRASTORNOS DE LA CONDUCTA ALIMENTARIOS
elif st.session_state.step == 7:
    st.markdown('<div class="section-header">VII. TRASTORNOS DE LA CONDUCTA ALIMENTARIOS</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        peso_maximo = st.number_input("Peso máximo (kg)", min_value=0.0, value=float(st.session_state.form_data.get('peso_maximo', 94)))
    
    with col2:
        peso_minimo = st.number_input("Peso mínimo adulto (kg)", min_value=0.0, value=float(st.session_state.form_data.get('peso_minimo', 68)))
    
    with col3:
        peso_ideal = st.number_input("Peso ideal (kg)", min_value=0.0, value=float(st.session_state.form_data.get('peso_ideal', 65)))
    
    with col4:
        altura = st.number_input("Altura (m)", min_value=0.0, step=0.01, value=float(st.session_state.form_data.get('altura', 1.60)))
    
    st.markdown("#### Trastornos Alimentarios:")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        arfid = st.radio("ARFID", ["No", "Sí"], index=1 if st.session_state.form_data.get('arfid', "No") == "Sí" else 0, key="arfid")
        anorexia = st.radio("Anorexia Nerviosa", ["No", "Sí"], index=1 if st.session_state.form_data.get('anorexia', "No") == "Sí" else 0, key="anorexia")
    
    with col2:
        comedor_emocional = st.radio("Comedor Emocional", ["No", "Sí"], index=1 if st.session_state.form_data.get('comedor_emocional', "No") == "Sí" else 0, key="comedor_emocional")
        comedor_nocturno = st.radio("Comedor Nocturno", ["No", "Sí"], index=1 if st.session_state.form_data.get('comedor_nocturno', "Si") == "Sí" else 0, key="comedor_nocturno")
    
    with col3:
        bulimia = st.radio("Bulimia Nerviosa", ["No", "Sí"], index=1 if st.session_state.form_data.get('bulimia', "No") == "Sí" else 0, key="bulimia")
        picoteador = st.radio("Picoteador", ["No", "Sí"], index=1 if st.session_state.form_data.get('picoteador', "Si") == "Sí" else 0, key="picoteador")
    
    with col4:
        t_atracon = st.radio("Trastorno por Atracón", ["No", "Sí"], index=1 if st.session_state.form_data.get('t_atracon', "No") == "Sí" else 0, key="t_atracon")
        food_craving = st.radio("Food Craving", ["No", "Sí"], index=1 if st.session_state.form_data.get('food_craving', "No") == "Sí" else 0, key="food_craving")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Atrás", key="atras_7"):
            prev_step()
    
    with col2:
        if st.button("Continuar", key="continuar_7"):
            st.session_state.form_data.update({
                'peso_maximo': peso_maximo,
                'peso_minimo': peso_minimo,
                'peso_ideal': peso_ideal,
                'altura': altura,
                'arfid': arfid,
                'comedor_emocional': comedor_emocional,
                'anorexia': anorexia,
                'comedor_nocturno': comedor_nocturno,
                'bulimia': bulimia,
                'picoteador': picoteador,
                't_atracon': t_atracon,
                'food_craving': food_craving
            })
            next_step()

# PASO 8: CONSCIENCIA DEL PROBLEMA Y NIVEL DE MOTIVACIÓN PARA EL CAMBIO
elif st.session_state.step == 8:
    st.markdown('<div class="section-header">VIII. CONSCIENCIA DEL PROBLEMA Y NIVEL DE MOTIVACIÓN PARA EL CAMBIO</div>', unsafe_allow_html=True)
    
    factores_origen = st.text_area("Análisis de factores que dieron origen y perpetúan el problema", value=st.session_state.form_data.get('factores_origen', ''), height=200)
    
    razones_cambiar = st.text_area("Razones para cambiar", value=st.session_state.form_data.get('razones_cambiar', ''), height=150)
    
    paciente_apto = st.radio("Paciente apto para procedimiento", ["SI", "NO", "SI, CON SEGUIMIENTO"], index=2 if st.session_state.form_data.get('paciente_apto', "SI, CON SEGUIMIENTO") == "SI, CON SEGUIMIENTO" else (1 if st.session_state.form_data.get('paciente_apto', "") == "NO" else 0))
    
    observaciones = st.text_area("Observaciones", value=st.session_state.form_data.get('observaciones', ''), height=150)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Atrás", key="atras_8"):
            prev_step()
    
    with col2:
        if st.button("Continuar", key="continuar_8"):
            st.session_state.form_data.update({
                'factores_origen': factores_origen,
                'razones_cambiar': razones_cambiar,
                'paciente_apto': paciente_apto,
                'observaciones': observaciones
            })
            next_step()

# PASO 9: REVISIÓN Y GENERACIÓN
elif st.session_state.step == 9:
    st.markdown('<div class="section-header">REVISIÓN Y GENERACIÓN DE INFORME</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="info-box">Revise la información ingresada antes de generar el informe. Si desea mejorar la redacción, asegúrese de tener configurada la API key de Anthropic.</div>', unsafe_allow_html=True)
    
    # Mostrar datos ingresados en formato de tabla
    st.markdown("### Resumen de la Información Ingresada")
    
    with st.expander("I. DATOS DEL PACIENTE"):
        datos_paciente = {
            "Nombre Completo": st.session_state.form_data.get('nombre_completo', ''),
            "R.U.N.": st.session_state.form_data.get('run', ''),
            "Fecha de Nacimiento": st.session_state.form_data.get('fecha_nacimiento', ''),
            "Edad": st.session_state.form_data.get('edad', ''),
            "Domicilio": st.session_state.form_data.get('domicilio', ''),
            "Email": st.session_state.form_data.get('email', ''),
            "Teléfono": st.session_state.form_data.get('telefono', ''),
            "Escolaridad": st.session_state.form_data.get('escolaridad', ''),
            "Profesión/Ocupación": st.session_state.form_data.get('ocupacion', '')
        }
        st.table(pd.DataFrame(list(datos_paciente.items()), columns=['Campo', 'Valor']))
    
    with st.expander("II. ANTECEDENTES FAMILIARES"):
        antecedentes_familiares = {
            "Familia Nuclear": st.session_state.form_data.get('familia_nuclear', ''),
            "Situación Conyugal Padres": st.session_state.form_data.get('situacion_conyugal_padres', ''),
            "Estado Civil": st.session_state.form_data.get('estado_civil', ''),
            "Hijos": st.session_state.form_data.get('hijos', ''),
            "Redes de Apoyo": st.session_state.form_data.get('redes_apoyo', ''),
            "Enfermedades Familia": st.session_state.form_data.get('enfermedades_familia', '')
        }
        st.table(pd.DataFrame(list(antecedentes_familiares.items()), columns=['Campo', 'Valor']))
    
    # Otras secciones expandibles para revisar
    with st.expander("III. ANTECEDENTES MÓRBIDOS"):
        antecedentes_morbidos = {
            "Antecedentes pre, peri y post natales": st.session_state.form_data.get('antecedentes_natales', ''),
            "Enfermedades en infancia y adolescencia": st.session_state.form_data.get('enfermedades_infancia', ''),
            "Enfermedades actuales": st.session_state.form_data.get('enfermedades_actuales', ''),
            "Operaciones": st.session_state.form_data.get('operaciones', '')
        }
        st.table(pd.DataFrame(list(antecedentes_morbidos.items()), columns=['Campo', 'Valor']))
    
    with st.expander("IV-V. SALUD MENTAL E HISTORIA ESCOLAR"):
        salud_mental_escolar = {
            "Antecedentes Salud Mental": st.session_state.form_data.get('antecedentes_salud_mental', ''),
            "Estado Salud Mental": st.session_state.form_data.get('estado_salud_mental', ''),
            "Repitencias": st.session_state.form_data.get('repitencias', ''),
            "Rendimiento Académico": st.session_state.form_data.get('rendimiento_academico', ''),
            "Comportamiento Escolar": st.session_state.form_data.get('comportamiento_escolar', '')
        }
        st.table(pd.DataFrame(list(salud_mental_escolar.items()), columns=['Campo', 'Valor']))
    
    with st.expander("VI. ABUSO O DEPENDENCIAS DE SUSTANCIAS"):
        sustancias = {
            "Alcohol": st.session_state.form_data.get('consumo_alcohol', ''),
            "Tabaco": st.session_state.form_data.get('consumo_tabaco', ''),
            "Marihuana": st.session_state.form_data.get('consumo_marihuana', ''),
            "Otras drogas": st.session_state.form_data.get('consumo_otras_drogas', '')
        }
        st.table(pd.DataFrame(list(sustancias.items()), columns=['Sustancia', 'Consumo']))
    
    with st.expander("VII. TRASTORNOS DE LA CONDUCTA ALIMENTARIOS"):
        alimentarios = {
            "Peso máximo": st.session_state.form_data.get('peso_maximo', ''),
            "Peso mínimo": st.session_state.form_data.get('peso_minimo', ''),
            "Peso ideal": st.session_state.form_data.get('peso_ideal', ''),
            "Altura": st.session_state.form_data.get('altura', ''),
            "ARFID": st.session_state.form_data.get('arfid', ''),
            "Comedor Emocional": st.session_state.form_data.get('comedor_emocional', ''),
            "Anorexia": st.session_state.form_data.get('anorexia', ''),
            "Comedor Nocturno": st.session_state.form_data.get('comedor_nocturno', ''),
            "Bulimia": st.session_state.form_data.get('bulimia', ''),
            "Picoteador": st.session_state.form_data.get('picoteador', ''),
            "Trastorno Atracón": st.session_state.form_data.get('t_atracon', ''),
            "Food Craving": st.session_state.form_data.get('food_craving', '')
        }
        st.table(pd.DataFrame(list(alimentarios.items()), columns=['Campo', 'Valor']))
    
    with st.expander("VIII-IX. CONSCIENCIA DEL PROBLEMA Y OBSERVACIONES"):
        problema_motivacion = {
            "Factores de origen": st.session_state.form_data.get('factores_origen', ''),
            "Razones para cambiar": st.session_state.form_data.get('razones_cambiar', ''),
            "Paciente apto": st.session_state.form_data.get('paciente_apto', ''),
            "Observaciones": st.session_state.form_data.get('observaciones', '')
        }
        st.table(pd.DataFrame(list(problema_motivacion.items()), columns=['Campo', 'Valor']))
    
    # Opciones para mejorar el texto con Anthropic
    st.markdown("### Mejorar la Redacción")
    
    mejorar_opciones = st.multiselect(
        "Seleccione las secciones para mejorar la redacción",
        ["Antecedentes Natales", "Factores de Origen", "Razones para Cambiar", "Observaciones"]
    )
    
    if st.button("Mejorar Redacción Seleccionada") and mejorar_opciones:
        if not api_key:
            st.warning("Debe ingresar una API key de Anthropic para mejorar la redacción.")
        else:
            with st.spinner("Mejorando la redacción con IA..."):
                # Procesar cada sección seleccionada
                for opcion in mejorar_opciones:
                    if opcion == "Antecedentes Natales":
                        texto_original = st.session_state.form_data.get('antecedentes_natales', '')
                        texto_mejorado, error = mejorar_texto_con_anthropic(texto_original, api_key)
                        if error:
                            st.error(f"Error al mejorar Antecedentes Natales: {error}")
                        else:
                            st.session_state.form_data['antecedentes_natales'] = texto_mejorado
                            st.success("✅ Antecedentes Natales mejorado")
                    
                    elif opcion == "Factores de Origen":
                        texto_original = st.session_state.form_data.get('factores_origen', '')
                        texto_mejorado, error = mejorar_texto_con_anthropic(texto_original, api_key)
                        if error:
                            st.error(f"Error al mejorar Factores de Origen: {error}")
                        else:
                            st.session_state.form_data['factores_origen'] = texto_mejorado
                            st.success("✅ Factores de Origen mejorado")
                    
                    elif opcion == "Razones para Cambiar":
                        texto_original = st.session_state.form_data.get('razones_cambiar', '')
                        texto_mejorado, error = mejorar_texto_con_anthropic(texto_original, api_key)
                        if error:
                            st.error(f"Error al mejorar Razones para Cambiar: {error}")
                        else:
                            st.session_state.form_data['razones_cambiar'] = texto_mejorado
                            st.success("✅ Razones para Cambiar mejorado")
                    
                    elif opcion == "Observaciones":
                        texto_original = st.session_state.form_data.get('observaciones', '')
                        texto_mejorado, error = mejorar_texto_con_anthropic(texto_original, api_key)
                        if error:
                            st.error(f"Error al mejorar Observaciones: {error}")
                        else:
                            st.session_state.form_data['observaciones'] = texto_mejorado
                            st.success("✅ Observaciones mejorado")
    
    # Generación del informe
    st.markdown("### Generar Informe PDF")
    
    if st.button("Generar Informe PDF"):
        with st.spinner("Generando informe..."):
            try:
                pdf_bytes = generar_pdf(st.session_state.form_data)
                st.session_state.pdf_bytes = pdf_bytes
                st.success("✅ Informe generado correctamente!")
                st.markdown(get_pdf_download_link(pdf_bytes, "Informe_Psicologico.pdf"), unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error al generar el PDF: {str(e)}")
    
    if st.session_state.pdf_bytes is not None:
        st.markdown(get_pdf_download_link(st.session_state.pdf_bytes, "Informe_Psicologico.pdf"), unsafe_allow_html=True)
    
    if st.button("Atrás", key="atras_9"):
        prev_step()
    
    if st.button("Nueva Evaluación"):
        st.session_state.step = 1
        st.session_state.form_data = {}
        st.session_state.anthropic_response = None
        st.session_state.anthropic_error = None
        st.session_state.pdf_bytes = None
        st.experimental_rerun()