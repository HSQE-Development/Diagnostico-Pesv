from datetime import datetime
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches


def replace_text_in_paragraph(paragraph, search_text, replace_text):
    if search_text in paragraph.text:
        inline = paragraph.runs
        for item in inline:
            if search_text in item.text:
                item.text = item.text.replace(search_text, replace_text)
                if search_text == "{{CONSULTOR_NOMBRE}}":
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
    flotas: list,
):
    """
    Inserta una tabla en el documento justo después del párrafo que contiene el placeholder.

    :param doc: Documento Word en el que se insertará la tabla.
    :param placeholder: Palabra clave para encontrar la ubicación de la tabla.
    :param fecha: Fecha de elaboración.
    :param empresa: Nombre de la empresa.
    :param nit: NIT de la empresa.
    :param actividades: Actividades de la empresa.
    :param flotas: Lista de diccionarios con información de la flota de vehículos.
    """
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            # Insertar la tabla después del párrafo que contiene el placeholder
            index = paragraph._element.getparent().index(paragraph._element)

            # Crear la tabla con el formato especificado
            table = doc.add_table(rows=5, cols=12)
            table.style = "Table Grid"

            # Configurar el ancho de las columnas (opcional)
            for col in table.columns:
                col.width = Inches(2)

            # Agregar encabezado para "CARACTERIZACION DE LA EMPRESA"
            heading_row = table.rows[0].cells
            heading_row[0].text = "CARACTERIZACION DE LA EMPRESA"
            heading_row[0].merge(heading_row[1])
            heading_row[0].merge(heading_row[2])
            heading_row[0].merge(heading_row[3])
            heading_row[0].merge(heading_row[4])
            heading_row[0].merge(heading_row[5])
            heading_row[0].merge(heading_row[6])
            heading_row[0].merge(heading_row[7])
            heading_row[0].merge(heading_row[8])
            heading_row[0].merge(heading_row[9])
            heading_row[0].merge(heading_row[10])
            heading_row[0].merge(heading_row[11])

            # Agregar fila con fecha, empresa, nit y actividades
            row_cells = table.rows[1].cells
            row_cells[0].text = "Fecha de elaboración"
            row_cells[0].merge(row_cells[1])
            row_cells[2].text = fecha
            row_cells[2].merge(row_cells[3])
            row_cells[4].text = "Empresa"
            row_cells[4].merge(row_cells[5])
            row_cells[6].text = empresa
            row_cells[6].merge(row_cells[7])

            row_cells = table.rows[2].cells
            row_cells[0].text = "Fecha de elaboración"
            row_cells[0].merge(row_cells[1])
            row_cells[2].text = fecha
            row_cells[2].merge(row_cells[3])
            row_cells[4].text = "Empresa"
            row_cells[4].merge(row_cells[5])
            row_cells[6].text = empresa
            row_cells[6].merge(row_cells[7])

            # Agregar fila con NIT y actividades
            row_cells = table.rows[2].cells
            row_cells[0].text = "Nit"
            row_cells[0].merge(row_cells[1])
            row_cells[2].text = nit
            row_cells[2].merge(row_cells[3])
            row_cells[4].text = "Actividades"
            row_cells[4].merge(row_cells[5])
            row_cells[6].text = actividades
            row_cells[6].merge(row_cells[7])

            # Agregar fila para Flota de vehículos
            flota_header_row = table.rows[3].cells
            flota_header_row[0].text = "Flota de vehículos"
            flota_header_row[1].text = ""
            flota_header_row[2].text = ""
            flota_header_row[3].text = ""
            flota_header_row[0].merge(flota_header_row[1])
            flota_header_row[0].merge(flota_header_row[2])
            flota_header_row[0].merge(flota_header_row[3])
            flota_header_row[0].merge(flota_header_row[4])
            flota_header_row[0].merge(flota_header_row[5])
            flota_header_row[0].merge(flota_header_row[6])
            flota_header_row[0].merge(flota_header_row[7])

            flota_rows_row = table.rows[4].cells
            flota_rows_row[0].text = "FLOTA DE VEHICULOS AUTOMOTORES"
            flota_rows_row[1].text = "Cantidad Propios"
            flota_rows_row[2].text = "Cantidad Terceros"
            flota_rows_row[3].text = "Cantidad Arrendados"
            flota_rows_row[4].text = "Cantidad Contratistas"
            flota_rows_row[5].text = "Cantidad Intermediación"
            flota_rows_row[6].text = "Cantidad Leasing"
            flota_rows_row[7].text = "Cantidad Renting"

            # Insertar datos de flota
            for flota in flotas:
                row_cells = table.add_row().cells
                row_cells[0].text = ""
                row_cells[1].text = flota.get("nombre", "")
                row_cells[2].text = str(flota.get("cant1", "0"))
                row_cells[3].text = str(flota.get("cant2", "0"))

            # Mover la tabla a la posición deseada
            table._element.getparent().insert(index + 1, table._element)
            return  # Salir después de insertar la tabla para evitar múltiples inserciones
