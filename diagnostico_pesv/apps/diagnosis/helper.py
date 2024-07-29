from datetime import datetime
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.table import _Cell
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.drawing.image import Image
import pandas as pd


def replace_text_in_paragraph(paragraph, search_text, replace_text):
    if search_text in paragraph.text:
        inline = paragraph.runs
        for item in inline:
            if search_text in item.text:
                item.text = item.text.replace(search_text, replace_text)
                if search_text == "{{CONSULTOR_NOMBRE}}":
                    item.bold = True
                if search_text == "{{MISIONALIDAD_NAME}}":
                    item.bold = True
                if search_text == "{{MISIONALIDAD_ID}}":
                    item.bold = True
                if search_text == "{{NIVEL_PESV}}":
                    item.bold = True
                if search_text == "{{QUANTITY_VEHICLES}}":
                    item.bold = True
                if search_text == "{{QUANTITY_DRIVERS}}":
                    item.bold = True


def replace_text_in_table(table, search_text, replace_text):
    for row in table.rows:
        for cell in row.cells:
            replace_text_in_paragraphs(cell.paragraphs, search_text, replace_text)


def replace_text_in_paragraphs(paragraphs, search_text, replace_text):
    for paragraph in paragraphs:
        replace_text_in_paragraph(paragraph, search_text, replace_text)


def replace_placeholders_in_document(doc: Document, placeholders: dict):
    # Reemplaza los marcadores en todos los párrafos
    for paragraph in doc.paragraphs:
        for placeholder, replacement in placeholders.items():
            replace_text_in_paragraph(paragraph, placeholder, replacement)


def format_nit(nit):
    # Convierte el valor a cadena y elimina caracteres no numéricos
    nit_string = "".join(filter(str.isdigit, str(nit)))

    # Verifica que la longitud sea de 10 dígitos
    if len(nit_string) != 10:
        raise ValueError("El NIT debe tener 10 dígitos.")

    # Aplica el formato XXXXXXXXX-X
    formatted_nit = f"{nit_string[:9]}-{nit_string[9]}"

    return formatted_nit


def get_current_month_and_year():
    # Obtiene la fecha y hora actuales
    now = datetime.now()

    # Traducciones de nombres de meses al español
    meses_en_espanol = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]

    # Obtiene el mes en número (1-12) y lo traduce al nombre del mes en español
    numero_mes = now.month
    nombre_mes = meses_en_espanol[numero_mes - 1]
    año_actual = now.year

    return nombre_mes, año_actual


def insert_table_after_placeholder(doc: Document, placeholder: str, table_data: list):
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            index = paragraph._element.getparent().index(paragraph._element)
            table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
            table.style = "Table Grid"
            for i, row_data in enumerate(table_data):
                row = table.rows[i]
                for j, cell_data in enumerate(row_data):
                    cell = row.cells[j]
                    cell.text = cell_data
            table._element.getparent().insert(index + 1, table._element)
            return


def insert_table_after_placeholder(
    doc: Document,
    placeholder: str,
    fecha: str,
    empresa: str,
    nit: str,
    actividades: str,
    vehicle_questions: list,
    fleet_data: list,
    driver_questions,
    driver_data,
    com_size,
    segment,
    contact,
    certification,
):
    """
    Inserta una tabla en el documento justo después del párrafo que contiene el placeholder.

    :param doc: Documento Word en el que se insertará la tabla.
    :param placeholder: Palabra clave para encontrar la ubicación de la tabla.
    :param fecha: Fecha de elaboración.
    :param empresa: Nombre de la empresa.
    :param nit: NIT de la empresa.
    :param actividades: Actividades de la empresa.
    :param vehicle_questions: Lista de preguntas sobre vehículos.
    :param fleet_data: Lista de datos de la flota.
    """
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            # Insertar la tabla después del párrafo que contiene el placeholder
            index = paragraph._element.getparent().index(paragraph._element)

            # Crear la tabla con el formato especificado
            table = doc.add_table(rows=1, cols=12)
            table.style = "Table Grid"

            # Configurar el ancho de las columnas (opcional)
            for col in table.columns:
                col.width = Inches(2)

            # Agregar encabezado para "CARACTERIZACION DE LA EMPRESA"
            heading_row = table.rows[0].cells
            heading_row[0].text = "CARACTERIZACION DE LA EMPRESA"
            heading_row[0].merge(heading_row[11])

            # Agregar fila con fecha y empresa
            row_cells = table.add_row().cells
            row_cells[0].text = "Fecha de elaboración"
            row_cells[0].merge(row_cells[1])
            row_cells[2].text = fecha
            row_cells[2].merge(row_cells[5])
            row_cells[6].text = "Empresa"
            row_cells[6].merge(row_cells[7])
            row_cells[8].text = empresa
            row_cells[8].merge(row_cells[11])

            # Agregar fila con NIT y actividades
            row_cells = table.add_row().cells
            row_cells[0].text = "Nit"
            row_cells[0].merge(row_cells[1])
            row_cells[2].text = nit
            row_cells[2].merge(row_cells[5])
            row_cells[6].text = "Actividades"
            row_cells[6].merge(row_cells[7])
            row_cells[8].text = actividades
            row_cells[8].merge(row_cells[11])

            # Agregar fila con NIT y actividades
            row_cells = table.add_row().cells
            row_cells[0].text = "Tamaño de la empresa"
            row_cells[0].merge(row_cells[1])
            row_cells[2].text = com_size
            row_cells[2].merge(row_cells[5])
            row_cells[6].text = "Segmento al que pertenece"
            row_cells[6].merge(row_cells[7])
            row_cells[8].text = segment
            row_cells[8].merge(row_cells[11])

            # Agregar fila con NIT y actividades
            row_cells = table.add_row().cells
            row_cells[0].text = "Contacto"
            row_cells[0].merge(row_cells[1])
            row_cells[2].text = contact
            row_cells[2].merge(row_cells[5])
            row_cells[6].text = "Certificaciones adquiridas (Normas ISO)"
            row_cells[6].merge(row_cells[7])
            row_cells[8].text = certification or "NINGUNA"
            row_cells[8].merge(row_cells[11])

            # Agregar fila para Flota de vehículos
            flota_header_row = table.add_row().cells
            flota_header_row[0].text = "Flota de vehículos"
            flota_header_row[0].merge(flota_header_row[11])

            flota_rows_row = table.add_row().cells
            flota_rows_row[0].text = "FLOTA DE VEHICULOS AUTOMOTORES"
            flota_rows_row[0].merge(flota_rows_row[4])
            flota_rows_row[5].text = "Cantidad Propios"
            flota_rows_row[6].text = "Cantidad Terceros"
            flota_rows_row[7].text = "Cantidad Arrendados"
            flota_rows_row[8].text = "Cantidad Contratistas"
            flota_rows_row[9].text = "Cantidad Intermediación"
            flota_rows_row[10].text = "Cantidad Leasing"
            flota_rows_row[11].text = "Cantidad Renting"

            # Variables para almacenar los totales
            total_propio = 0
            total_tercero = 0
            total_arrendado = 0
            total_contratista = 0
            total_intermediacion = 0
            total_leasing = 0
            total_renting = 0

            # Insertar datos de flota
            for vehicle_question in vehicle_questions:
                row_cells = table.add_row().cells
                row_cells[0].text = vehicle_question.name
                row_cells[0].merge(row_cells[4])
                fleet = next(
                    (
                        f
                        for f in fleet_data
                        if f.vehicle_question.id == vehicle_question.id
                    ),
                    None,
                )
                quantity_propio = fleet.quantity_owned if fleet else 0
                quantity_tercero = fleet.quantity_third_party if fleet else 0
                quantity_arrendado = fleet.quantity_arrended if fleet else 0
                quantity_contratista = fleet.quantity_contractors if fleet else 0
                quantity_intermediacion = fleet.quantity_intermediation if fleet else 0
                quantity_leasing = fleet.quantity_leasing if fleet else 0
                quantity_renting = fleet.quantity_renting if fleet else 0

                row_cells[5].text = str(quantity_propio)
                row_cells[6].text = str(quantity_tercero)
                row_cells[7].text = str(quantity_arrendado)
                row_cells[8].text = str(quantity_contratista)
                row_cells[9].text = str(quantity_intermediacion)
                row_cells[10].text = str(quantity_leasing)
                row_cells[11].text = str(quantity_renting)

                # Sumar cantidades a los totales
                total_propio += quantity_propio
                total_tercero += quantity_tercero
                total_arrendado += quantity_arrendado
                total_contratista += quantity_contratista
                total_intermediacion += quantity_intermediacion
                total_leasing += quantity_leasing
                total_renting += quantity_renting

                total = (
                    total_propio
                    + total_tercero
                    + total_arrendado
                    + total_contratista
                    + total_intermediacion
                    + total_leasing
                    + total_renting
                )

            # Agregar fila con los totales
            total_row = table.add_row().cells
            total_row[0].text = "Total Vehiculos".upper()
            total_row[0].merge(total_row[4])
            total_row[5].text = str(total)
            total_row[5].merge(total_row[6])
            total_row[5].merge(total_row[7])
            total_row[5].merge(total_row[8])
            total_row[5].merge(total_row[9])
            total_row[5].merge(total_row[10])
            total_row[5].merge(total_row[11])

            # Agregar fila para Conductores
            driver_header_row = table.add_row().cells
            driver_header_row[0].text = (
                "Personas que conducen con fines misionales".upper()
            )
            driver_header_row[0].merge(driver_header_row[8])
            driver_header_row[9].text = "Cantidad"
            driver_header_row[9].merge(driver_header_row[11])
            total_conductores = 0
            # Datos de conductores
            for driver_question in driver_questions:
                driver_data_row = table.add_row().cells
                driver_data_row[0].text = driver_question.name
                driver_data_row[0].merge(driver_data_row[8])
                driver = next(
                    (
                        f
                        for f in driver_data
                        if f.driver_question.id == driver_question.id
                    ),
                    None,
                )
                quantity = driver.quantity if driver else 0
                driver_data_row[9].text = str(quantity)
                driver_data_row[9].merge(driver_data_row[11])
                total_conductores += quantity
            # Agregar fila con los totales
            total_driver_row = table.add_row().cells
            total_driver_row[0].text = "Total Conductores".upper()
            total_driver_row[0].merge(total_driver_row[8])
            total_driver_row[9].text = str(total_conductores)
            total_driver_row[9].merge(total_driver_row[11])
            # Mover la tabla a la posición deseada
            table._element.getparent().insert(index + 1, table._element)
            return  # Salir después de insertar la tabla para evitar múltiples inserciones


def insert_table_results(doc: Document, placeholder: str, filtered_data):
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            index = paragraph._element.getparent().index(paragraph._element)
            table = doc.add_table(rows=1, cols=6)
            table.style = "Table Grid"

            # Estilo de la tabla
            table.autofit = True
            for row in table.rows:
                for cell in row.cells:
                    cell.text = ""
                    cell.paragraphs[0].runs[0].font.size = Pt(10)  # Tamaño de fuente
                    cell.paragraphs[0].runs[0].font.name = "Arial"  # Tipo de fuente
                    cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(
                        0, 0, 0
                    )  # Color de texto
                    cell.paragraphs[0].paragraph_format.alignment = (
                        WD_ALIGN_PARAGRAPH.CENTER
                    )  # Alineación

            # Quitar bordes de la tabla
            # tbl = table._tbl
            # tblPr = tbl.tblPr
            # tblBorders = OxmlElement("w:tblBorders")
            # for border_name in ["top", "left", "bottom", "right", "insideH", "insideV"]:
            #     border = OxmlElement(f"w:{border_name}")
            #     border.set(qn("w:val"), "none")
            #     tblBorders.append(border)
            # tblPr.append(tblBorders)

            # Estilo de la fila de encabezado
            heading_row = table.rows[0].cells
            heading_row[0].text = "PASO PESV"
            heading_row[1].text = "REQUISITO"
            heading_row[1].merge(heading_row[5])

            for cell in heading_row:
                cell._element.get_or_add_tcPr().append(
                    parse_xml(r'<w:shd {} w:fill="D3D3D3"/>'.format(nsdecls("w")))
                )  # Fondo gris suave
                cell._element.get_or_add_tcPr().append(
                    parse_xml(
                        r'<w:bdr {} w:bottom="1pt" w:space="0" w:val="single"/>'.format(
                            nsdecls("w")
                        )
                    )
                )  # Borde inferior negro
            for data in filtered_data:
                for steps in data["steps"]:
                    step_number = str(steps["step"])
                    for requirement in steps["requirements"]:
                        step_row = table.add_row().cells
                        step_row[0].text = str(steps["step"])  # Paso
                        step_row[1].text = str(requirement["requirement_name"])
                        for cell in step_row:
                            cell._element.get_or_add_tcPr().append(
                                parse_xml(
                                    r'<w:shd {} w:fill="002C4F"/>'.format(nsdecls("w"))
                                )
                            )
                            cell._element.get_or_add_tcPr().append(
                                parse_xml(
                                    r'<w:bdr {} w:bottom="1pt" w:space="0" w:val="single"/>'.format(
                                        nsdecls("w")
                                    )
                                )
                            )
                        step_row[1].merge(step_row[5])
                        step_row = table.add_row().cells
                        step_row[0].text = "Criterio de verificación"
                        step_row[0].merge(step_row[4])
                        step_row[5].text = "Nivel de Cumplimiento"
                        for cell in step_row:
                            cell._element.get_or_add_tcPr().append(
                                parse_xml(
                                    r'<w:shd {} w:fill="F5F5F5"/>'.format(nsdecls("w"))
                                )
                            )
                        question_number = 1
                        for question in requirement["questions"]:
                            question_row = table.add_row().cells
                            question_cell = question_row[0]
                            para = question_cell.add_paragraph()
                            # Run para la numeración en negrita
                            run_number = para.add_run(
                                f"{step_number}.{question_number} "
                            )
                            run_number.bold = True
                            run_text = para.add_run(question["question_name"])
                            question_cell.merge(question_row[4])
                            question_row[5].text = question["compliance"]
                            for cell in question_row:
                                # Crear un elemento de borde inferior
                                bottom_border = OxmlElement("w:bottom")
                                bottom_border.set(
                                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val",
                                    "single",
                                )
                                cell._element.get_or_add_tcPr().append(bottom_border)
                            question_number += 1
            table._element.getparent().insert(index + 1, table._element)
            return  # Salir después de insertar la tabla para evitar múltiples inserciones


def apply_bullets(paragraph):
    """Aplica viñetas al párrafo usando XML."""
    p = paragraph._element
    pPr = p.get_or_add_pPr()
    numPr = OxmlElement("w:numPr")
    numId = OxmlElement("w:numId")
    numId.set(qn("w:val"), "1")  # Utiliza el ID de numeración predeterminado
    numPr.append(numId)
    pPr.append(numPr)


def insert_table_recomendations(
    doc: Document, placeholder: str, recomendaciones_agrupadas
):
    VALID_STEPS = {
        "P": "PLANEAR",
        "H": "HACER",
        "V": "VERIFICAR",
        "A": "ACTUAR",
    }
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            index = paragraph._element.getparent().index(paragraph._element)
            table = doc.add_table(rows=1, cols=6)
            table.style = "Table Grid"

            # Estilo de la tabla
            table.autofit = True
            for row in table.rows:
                for cell in row.cells:
                    cell.text = ""
                    cell.paragraphs[0].runs[0].font.size = Pt(10)  # Tamaño de fuente
                    cell.paragraphs[0].runs[0].font.name = "Arial"  # Tipo de fuente
                    cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(
                        0, 0, 0
                    )  # Color de texto
                    cell.paragraphs[0].paragraph_format.alignment = (
                        WD_ALIGN_PARAGRAPH.CENTER
                    )  # Alineación

            # Encabezado de la tabla
            heading_row = table.rows[0].cells
            heading_row[0].text = "CICLO PESV"
            heading_row[0].merge(heading_row[5])
            for cell in heading_row:
                cell._element.get_or_add_tcPr().append(
                    parse_xml(r'<w:shd {} w:fill="D3D3D3"/>'.format(nsdecls("w")))
                )  # Fondo gris suave
                cell._element.get_or_add_tcPr().append(
                    parse_xml(
                        r'<w:bdr {} w:bottom="1pt" w:space="0" w:val="single"/>'.format(
                            nsdecls("w")
                        )
                    )
                )  # Borde inferior negro

            # Insertar datos por ciclo
            for item in recomendaciones_agrupadas:
                ciclo = VALID_STEPS.get(item["cycle"].upper(), "Otros").upper()
                recomendaciones = item["recomendations"]
                row = table.add_row().cells
                row[0].text = ciclo
                cell = row[1]
                cell.paragraphs[0].clear()  # Limpiar cualquier texto existente

                for recomendacion in recomendaciones:
                    p = cell.add_paragraph(recomendacion)
                    apply_bullets(p)
                row[1].merge(row[5])
                for cell in row:
                    bottom_border = OxmlElement("w:bottom")
                    bottom_border.set(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val",
                        "single",
                    )
                    cell._element.get_or_add_tcPr().append(bottom_border)

            table._element.getparent().insert(index + 1, table._element)
            return  # Salir después de insertar la tabla para evitar múltiples inserciones


def set_vertical_cell_direction(cell: _Cell, direction: str, align_center: bool = True):
    # direction: tbRl -- top to bottom, btLr -- bottom to top
    assert direction in ("tbRl", "btLr")
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    textDirection = OxmlElement("w:textDirection")
    textDirection.set(qn("w:val"), direction)  # btLr tbRl
    tcPr.append(textDirection)
    # Configuración de la alineación vertical
    if align_center:
        vAlign = OxmlElement("w:vAlign")
        vAlign.set(qn("w:val"), "center")
        tcPr.append(vAlign)


def merge_cells_vertically(cell):
    """Combine vertical cells in the given cell."""
    cell._tc.get_or_add_tcPr().append(OxmlElement("w:vMerge"))


def insert_table_conclusion(
    doc: Document, placeholder: str, datas_by_cycle, sizeName: str
):
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            index = paragraph._element.getparent().index(paragraph._element)
            table = doc.add_table(rows=1, cols=8)
            table.style = "Table Grid"

            heading_row = table.rows[0].cells
            heading_row[0].text = (
                f"ESTRUCTURA DE PONDERACIÓN \n NIVEL {sizeName} - PESV"
            )
            heading_row[0].merge(heading_row[7])

            title_row = table.add_row().cells
            title_row[0].text = "FASE"
            title_row[1].text = "PASO"
            title_row[2].text = "DESCRIPCIÓN"
            title_row[2].merge(title_row[5])
            title_row[6].text = "% PASO"
            title_row[7].text = "% FASE"

            VALID_STEPS = {
                "P": "PLANEAR",
                "H": "HACER",
                "V": "VERIFICAR",
                "A": "ACTUAR",
            }

            # # Recorrer y agregar filas para cada fase
            for cycle in datas_by_cycle:
                phase_name = VALID_STEPS.get(cycle["cycle"].upper(), "Otros").upper()
                for i, requerimiento in enumerate(cycle["steps"]):
                    cells = table.add_row().cells
                    if i == 0:
                        percentage = round(cycle["cycle_percentage"], 2)
                        set_vertical_cell_direction(cells[0], "tbRl")
                        cells[0].text = phase_name
                        cells[7].text = f"{percentage}%"
                    cells[1].text = str(requerimiento["step"])
                    for requirement in requerimiento["requirements"]:
                        cells[2].text = str(requirement["requirement_name"])
                        cells[2].merge(cells[5])
                    req_percentage = round(requerimiento["percentage"], 2)
                    cells[6].text = f"{req_percentage}%"

                start_idx = len(table.rows) - len(cycle["steps"])
                end_idx = len(table.rows) - 1
                for row_idx in range(start_idx, end_idx + 1):
                    table.cell(row_idx, 0).merge(table.cell(end_idx, 0))
                    table.cell(row_idx, 7).merge(table.cell(end_idx, 7))

            table._element.getparent().insert(index + 1, table._element)
            return  # Salir después de insertar la tabla para evitar múltiples inserciones


def insert_table_conclusion_articulated(
    doc: Document, placeholder: str, datas_by_cycle, sizeName: str
):
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            index = paragraph._element.getparent().index(paragraph._element)
            table = doc.add_table(rows=1, cols=8)
            table.style = "Table Grid"
            heading_row = table.rows[0].cells
            heading_row[0].text = (
                f"ESTRUCTURA DE PONDERACIÓN \n NIVEL {sizeName} - PESV - ARTICULACIONES"
            )
            heading_row[0].merge(heading_row[7])
            title_row = table.add_row().cells
            title_row[0].text = "FASE"
            title_row[1].text = "PASO"
            title_row[2].text = "DESCRIPCIÓN"
            title_row[2].merge(title_row[5])
            title_row[6].text = "NIVEL CUMPLIMIENTO"
            title_row[6].merge(title_row[7])
            for cycle_data in datas_by_cycle:
                cycle = cycle_data["cycle"]
                for step_data in cycle_data["steps"]:
                    step = step_data["step"]
                    for requirement_data in step_data["requirements"]:
                        requirement_name = requirement_data["requirement_name"]
                        # Obtener la última pregunta
                        last_question = requirement_data["questions"][-1]
                        last_question_name = last_question["question_name"]
                        last_compliance = last_question["compliance"]

                        row_cells = table.add_row().cells
                        row_cells[0].text = cycle
                        row_cells[1].text = str(step)
                        row_cells[2].text = f"{requirement_name} - {last_question_name}"
                        row_cells[2].merge(row_cells[5])
                        row_cells[6].text = last_compliance
            table._element.getparent().insert(index + 1, table._element)
            return  # Salir después de insertar la tabla para evitar múltiples inserciones


def insert_table_conclusion_percentage(
    doc: Document, placeholder: str, counts, perecentaje
):
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            index = paragraph._element.getparent().index(paragraph._element)
            table = doc.add_table(rows=1, cols=5)
            table.style = "Table Grid"
            heading_row = table.rows[0].cells
            heading_row[0].text = "TOTAL ITEMS"
            heading_row[1].text = "CUMPLE"
            heading_row[2].text = "NO CUMPLE"
            heading_row[3].text = "CUMPLE PARCIALMENTE"
            heading_row[3].text = "NO APLICA"
            heading_row[4].text = "PORCENTJAE CUMPLIMIENTO"

            total_items = counts[0]["count"] + counts[1]["count"] + counts[2]["count"]

            title_row = table.add_row().cells
            title_row[0].text = str(total_items)
            title_row[1].text = str(counts[0]["count"])  # Cumple
            title_row[2].text = str(counts[1]["count"])  # No Cumple
            title_row[3].text = str(counts[2]["count"])  # Cumple Parcialmente
            title_row[3].text = str(counts[3]["count"])  # No Aplica
            title_row[4].text = f"{perecentaje}%"
            table._element.getparent().insert(index + 1, table._element)
            return  # Salir después de insertar la tabla para evitar múltiples inserciones


def insert_image_after_placeholder(doc, placeholder, image_path):
    # Iterar sobre todos los párrafos en el documento
    for para in doc.paragraphs:
        if placeholder in para.text:
            # Crear un nuevo párrafo para la imagen
            new_paragraph = para.insert_paragraph_before()
            run = new_paragraph.add_run()
            run.add_picture(image_path, width=Inches(5))
            # Eliminar el párrafo original con el placeholder
            para.clear()  # Eliminar el texto del párrafo pero mantener el párrafo
            break


def create_radar_chart(datas_by_cycle):
    labels = ["PLANEAR", "HACER", "ACTUAR", "VERIFICAR"]  # 5 categorías
    stats = []  # Valores para cada categoría
    for item in datas_by_cycle:
        stats.append([round(item["cycle_percentage"], 2)])
    # Número de categorías
    num_vars = len(labels)

    # Ángulos para cada categoría
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    # Añadir el primer ángulo al final para cerrar el gráfico
    stats += stats[:1]
    angles += angles[:1]

    # Crear la gráfica de telaraña
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, stats, color="blue", alpha=0.25)  # Rellenar el área bajo la curva

    # Configurar los límites radiales
    ax.set_ylim(0, 100)

    # Añadir etiquetas
    ax.set_thetagrids(
        np.degrees(angles[:-1]), labels
    )  # Usar angles[:-1] para evitar duplicar la última etiqueta

    # Guardar como imagen PNG
    image_file = "telarana.png"
    plt.savefig(image_file, bbox_inches="tight")

    # Mostrar la gráfica (opcional, según se necesite)
    # plt.show()

    return image_file


def create_bar_chart(datas_by_cycle):
    wb = openpyxl.Workbook()
    ws = wb.active
    data = [["Paso PESV", "Porcentage"]]
    for item in datas_by_cycle:
        for steps in item["steps"]:
            step = steps["step"]
            percentage = steps["percentage"]
            data.append([step, percentage])
    for row in data:
        ws.append(row)
    chart = BarChart()
    chart.title = "NIVEL DEL CUMPLIMIENTO DEL PESV"
    chart.x_axis.title = "Paso PESV"
    chart.y_axis.title = "Porcentage"
    data = Reference(ws, min_col=2, min_row=1, max_col=2, max_row=len(data))
    categories = Reference(ws, min_col=1, min_row=2, max_row=len(data))
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    ws.add_chart(chart, "E5")
    excel_file = "chart.xlsx"
    wb.save(excel_file)

    df = pd.read_excel(excel_file)
    fig, ax = plt.subplots()
    df.plot(kind="bar", x="Paso PESV", y="Porcentage", ax=ax)
    ax.set_title("NIVEL DEL CUMPLIMIENTO DEL PESV")
    ax.set_xlabel("Paso PESV")
    ax.set_ylabel("Porcentage")
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    image_file = "chart.png"
    with open(image_file, "wb") as f:
        f.write(img_buffer.getvalue())

    return image_file
