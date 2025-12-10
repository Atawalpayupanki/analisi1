"""
Módulo de almacenamiento en Excel para noticias clasificadas.

Este módulo proporciona funcionalidad para guardar datos de noticias
ya clasificadas en un archivo Excel (.xlsx) que actúa como base histórica.

Estructura de datos:
- Nombre del periódico
- Titular con enlace
- Resumen en dos frases
- Tema
- Imagen de China
- Fecha
- Descripción
- Texto completo

Autor: Sistema de Análisis de Noticias sobre China
Fecha: 2025-12-10
"""

import os
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from typing import Dict, Any


# Definición de columnas en orden exacto
COLUMNAS_EXCEL = [
    "Nombre del periódico",
    "Titular con enlace",
    "Resumen en dos frases",
    "Tema",
    "Imagen de China",
    "Fecha",
    "Descripción",
    "Texto completo"
]

NOMBRE_HOJA = "Datos"


def preparar_registro(datos_noticia: Dict[str, Any], 
                      datos_clasificacion: Dict[str, Any]) -> Dict[str, str]:
    """
    Prepara un registro combinando datos originales y datos del LLM.
    
    Args:
        datos_noticia: Diccionario con datos originales de la noticia.
            Claves esperadas: medio, fecha, titulo, enlace, descripcion, texto_completo
        datos_clasificacion: Diccionario con datos del LLM.
            Claves esperadas: tema, imagen_de_china, resumen_dos_frases
    
    Returns:
        Diccionario con todas las claves en el orden correcto para Excel.
    
    Ejemplo:
        >>> datos_noticia = {
        ...     'medio': 'El País',
        ...     'fecha': '2025-12-10',
        ...     'titulo': 'Noticia importante',
        ...     'enlace': 'https://ejemplo.com/noticia',
        ...     'descripcion': 'Descripción breve',
        ...     'texto_completo': 'Texto completo de la noticia...'
        ... }
        >>> datos_clasificacion = {
        ...     'tema': 'Economía',
        ...     'imagen_de_china': 'Positiva',
        ...     'resumen_dos_frases': 'Resumen. Segunda frase.'
        ... }
        >>> registro = preparar_registro(datos_noticia, datos_clasificacion)
    """
    from datetime import datetime
    
    # Crear titular con enlace en formato de hiperenlace de Excel
    titular_con_enlace = datos_noticia.get('titulo', '')
    enlace = datos_noticia.get('enlace', '')
    
    # Si hay enlace, crear formato de hiperenlace
    if enlace:
        titular_con_enlace = f'=HYPERLINK("{enlace}", "{titular_con_enlace}")'
    
    # Formatear fecha a DD-MM-YYYY
    fecha_original = datos_noticia.get('fecha', '')
    fecha_formateada = fecha_original
    
    if fecha_original:
        try:
            # Intentar parsear varios formatos comunes
            for formato in ['%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y']:
                try:
                    fecha_obj = datetime.strptime(fecha_original, formato)
                    fecha_formateada = fecha_obj.strftime('%d-%m-%Y')
                    break
                except ValueError:
                    continue
        except Exception:
            # Si falla el parseo, mantener fecha original
            fecha_formateada = fecha_original
    
    # Construir registro en el orden exacto de las columnas
    registro = {
        "Nombre del periódico": datos_noticia.get('medio', ''),
        "Titular con enlace": titular_con_enlace,
        "Resumen en dos frases": datos_clasificacion.get('resumen_dos_frases', ''),
        "Tema": datos_clasificacion.get('tema', ''),
        "Imagen de China": datos_clasificacion.get('imagen_de_china', ''),
        "Fecha": fecha_formateada,
        "Descripción": datos_noticia.get('descripcion', ''),
        "Texto completo": datos_noticia.get('texto_completo', '')
    }
    
    return registro


def cargar_o_crear_excel(ruta_archivo: str) -> Workbook:
    """
    Carga un archivo Excel existente o crea uno nuevo con encabezados.
    
    Args:
        ruta_archivo: Ruta completa al archivo Excel.
    
    Returns:
        Objeto Workbook de openpyxl listo para usar.
    
    Raises:
        PermissionError: Si el archivo está abierto o no hay permisos.
        OSError: Si hay problemas con la ruta o el sistema de archivos.
    """
    ruta = Path(ruta_archivo)
    
    # Crear directorio padre si no existe
    ruta.parent.mkdir(parents=True, exist_ok=True)
    
    if ruta.exists():
        # Cargar archivo existente
        try:
            wb = load_workbook(ruta_archivo)
            print(f"[OK] Archivo Excel cargado: {ruta_archivo}")
            
            # Verificar que existe la hoja esperada
            if NOMBRE_HOJA not in wb.sheetnames:
                # Si no existe, crearla
                ws = wb.create_sheet(NOMBRE_HOJA)
                ws.append(COLUMNAS_EXCEL)
                print(f"[OK] Hoja '{NOMBRE_HOJA}' creada con encabezados")
            
            return wb
            
        except PermissionError:
            raise PermissionError(
                f"No se puede abrir el archivo '{ruta_archivo}'. "
                "Asegúrate de que no esté abierto en otra aplicación."
            )
        except Exception as e:
            raise OSError(f"Error al cargar el archivo Excel: {str(e)}")
    
    else:
        # Crear nuevo archivo
        try:
            wb = Workbook()
            
            # Renombrar la hoja activa o crear nueva
            if wb.active.title == "Sheet":
                ws = wb.active
                ws.title = NOMBRE_HOJA
            else:
                ws = wb.create_sheet(NOMBRE_HOJA)
            
            # Insertar encabezados
            ws.append(COLUMNAS_EXCEL)
            
            # Ajustar ancho de columnas para mejor legibilidad
            anchos_columnas = {
                1: 20,  # Nombre del periódico
                2: 50,  # Titular con enlace
                3: 60,  # Resumen en dos frases
                4: 15,  # Tema
                5: 15,  # Imagen de China
                6: 12,  # Fecha
                7: 40,  # Descripción
                8: 80   # Texto completo
            }
            
            for col_num, ancho in anchos_columnas.items():
                col_letra = get_column_letter(col_num)
                ws.column_dimensions[col_letra].width = ancho
            
            print(f"[OK] Nuevo archivo Excel creado: {ruta_archivo}")
            print(f"[OK] Hoja '{NOMBRE_HOJA}' creada con encabezados")
            
            return wb
            
        except PermissionError:
            raise PermissionError(
                f"No hay permisos para crear el archivo en '{ruta_archivo}'. "
                "Verifica los permisos del directorio."
            )
        except Exception as e:
            raise OSError(f"Error al crear el archivo Excel: {str(e)}")


def añadir_registro_excel(registro: Dict[str, str], ruta_archivo: str) -> bool:
    """
    Añade un registro al archivo Excel sin borrar datos anteriores.
    
    Args:
        registro: Diccionario con los datos del registro a añadir.
        ruta_archivo: Ruta completa al archivo Excel.
    
    Returns:
        True si el registro se añadió correctamente, False en caso contrario.
    
    Raises:
        PermissionError: Si el archivo está abierto o no hay permisos.
        ValueError: Si el registro no contiene todas las columnas necesarias.
        OSError: Si hay problemas con la ruta o el sistema de archivos.
    """
    from openpyxl.styles import Font
    
    # Validar que el registro contiene todas las columnas
    columnas_faltantes = set(COLUMNAS_EXCEL) - set(registro.keys())
    if columnas_faltantes:
        raise ValueError(
            f"El registro no contiene las siguientes columnas: {columnas_faltantes}"
        )
    
    try:
        # Cargar o crear el archivo
        wb = cargar_o_crear_excel(ruta_archivo)
        
        # Obtener la hoja de datos
        ws = wb[NOMBRE_HOJA]
        
        # Preparar fila con valores en el orden correcto
        # IMPORTANTE: Para la columna de titular, guardamos solo el texto, no la fórmula
        fila = []
        for columna in COLUMNAS_EXCEL:
            valor = registro[columna]
            
            # Si es la columna de titular y contiene una fórmula HYPERLINK, extraer solo el texto
            if columna == "Titular con enlace" and isinstance(valor, str) and valor.startswith('=HYPERLINK'):
                # Extraer el texto del titular de la fórmula
                parts = valor.split('"')
                if len(parts) >= 4:
                    valor = parts[-2]  # El texto está en la penúltima parte
            
            fila.append(valor)
        
        # Añadir fila al final
        ws.append(fila)
        
        # Obtener el número de la fila recién añadida
        numero_fila = ws.max_row
        
        # Ahora añadir el hiperenlace de forma nativa si existe
        # Buscar si el registro original tenía un enlace
        titular_original = registro["Titular con enlace"]
        if isinstance(titular_original, str) and titular_original.startswith('=HYPERLINK'):
            # Extraer la URL de la fórmula
            parts = titular_original.split('"')
            if len(parts) >= 2:
                url = parts[1]
                
                # Obtener la celda del titular (columna B)
                celda_titular = ws.cell(row=numero_fila, column=2)
                
                # Añadir hiperenlace nativo
                celda_titular.hyperlink = url
                celda_titular.font = Font(color="0563C1", underline="single")
        
        # Guardar cambios
        wb.save(ruta_archivo)
        
        print(f"[OK] Registro añadido en la fila {numero_fila}")
        
        return True
        
    except PermissionError as e:
        print(f"[ERROR] Error de permisos: {str(e)}")
        raise
    except ValueError as e:
        print(f"[ERROR] Error de validación: {str(e)}")
        raise
    except Exception as e:
        print(f"[ERROR] Error inesperado al añadir registro: {str(e)}")
        raise OSError(f"Error al añadir registro: {str(e)}")


def guardar_noticia_en_excel(datos_noticia: Dict[str, Any],
                             datos_clasificacion: Dict[str, Any],
                             ruta_archivo: str) -> bool:
    """
    Punto de entrada principal del módulo.
    
    Combina datos de noticia y clasificación, y los guarda en Excel.
    
    Args:
        datos_noticia: Diccionario con datos originales de la noticia.
            Claves esperadas: medio, fecha, titulo, enlace, descripcion, texto_completo
        datos_clasificacion: Diccionario con datos del LLM.
            Claves esperadas: tema, imagen_de_china, resumen_dos_frases
        ruta_archivo: Ruta completa al archivo Excel donde guardar.
    
    Returns:
        True si se guardó correctamente, False en caso contrario.
    
    Ejemplo de uso:
        >>> datos_noticia = {
        ...     'medio': 'El País',
        ...     'fecha': '2025-12-10',
        ...     'titulo': 'China anuncia nuevas medidas económicas',
        ...     'enlace': 'https://elpais.com/economia/2025-12-10/china-medidas.html',
        ...     'descripcion': 'El gobierno chino presenta un paquete de estímulos',
        ...     'texto_completo': 'Beijing, 10 de diciembre...'
        ... }
        >>> datos_clasificacion = {
        ...     'tema': 'Economía',
        ...     'imagen_de_china': 'Positiva',
        ...     'resumen_dos_frases': 'China lanza estímulos económicos. Medidas buscan reactivar el consumo.'
        ... }
        >>> exito = guardar_noticia_en_excel(
        ...     datos_noticia,
        ...     datos_clasificacion,
        ...     'f:/pautalla/china/data/noticias_historico.xlsx'
        ... )
    """
    try:
        print("\n" + "="*60)
        print("GUARDANDO NOTICIA EN EXCEL")
        print("="*60)
        
        # Paso 1: Preparar registro
        print("\n[1/3] Preparando registro...")
        registro = preparar_registro(datos_noticia, datos_clasificacion)
        print(f"[OK] Registro preparado: {datos_noticia.get('titulo', 'Sin título')[:50]}...")
        
        # Paso 2: Añadir a Excel
        print("\n[2/3] Añadiendo registro a Excel...")
        resultado = añadir_registro_excel(registro, ruta_archivo)
        
        # Paso 3: Confirmación
        print("\n[3/3] Proceso completado")
        print("="*60)
        print(f"[OK] Noticia guardada exitosamente en: {ruta_archivo}")
        print("="*60 + "\n")
        
        return resultado
        
    except PermissionError as e:
        print(f"\n[ERROR] ERROR DE PERMISOS: {str(e)}")
        print("   Solución: Cierra el archivo Excel si está abierto.\n")
        return False
        
    except ValueError as e:
        print(f"\n[ERROR] ERROR DE DATOS: {str(e)}")
        print("   Solución: Verifica que los datos de entrada sean correctos.\n")
        return False
        
    except OSError as e:
        print(f"\n[ERROR] ERROR DE SISTEMA: {str(e)}")
        print("   Solución: Verifica la ruta y los permisos del directorio.\n")
        return False
        
    except Exception as e:
        print(f"\n[ERROR] ERROR INESPERADO: {str(e)}")
        print("   Contacta con el administrador del sistema.\n")
        return False


# Función auxiliar para validar datos antes de guardar (opcional)
def validar_datos_noticia(datos_noticia: Dict[str, Any]) -> tuple[bool, str]:
    """
    Valida que los datos de la noticia sean correctos.
    
    Args:
        datos_noticia: Diccionario con datos de la noticia.
    
    Returns:
        Tupla (es_valido, mensaje_error)
    """
    campos_requeridos = ['medio', 'fecha', 'titulo', 'enlace', 'descripcion', 'texto_completo']
    
    for campo in campos_requeridos:
        if campo not in datos_noticia:
            return False, f"Falta el campo requerido: {campo}"
        if not datos_noticia[campo]:
            return False, f"El campo '{campo}' está vacío"
    
    return True, ""


def validar_datos_clasificacion(datos_clasificacion: Dict[str, Any]) -> tuple[bool, str]:
    """
    Valida que los datos de clasificación sean correctos.
    
    Args:
        datos_clasificacion: Diccionario con datos del LLM.
    
    Returns:
        Tupla (es_valido, mensaje_error)
    """
    campos_requeridos = ['tema', 'imagen_de_china', 'resumen_dos_frases']
    
    for campo in campos_requeridos:
        if campo not in datos_clasificacion:
            return False, f"Falta el campo requerido: {campo}"
        if not datos_clasificacion[campo]:
            return False, f"El campo '{campo}' está vacío"
    
    return True, ""


if __name__ == "__main__":
    """
    Ejemplo de uso del módulo.
    Este bloque solo se ejecuta si el archivo se ejecuta directamente.
    """
    print("Módulo de almacenamiento Excel para noticias clasificadas")
    print("Este módulo está diseñado para ser importado, no ejecutado directamente.")
    print("\nEjemplo de uso:")
    print("""
    from excel_storage import guardar_noticia_en_excel
    
    datos_noticia = {
        'medio': 'El País',
        'fecha': '2025-12-10',
        'titulo': 'China anuncia nuevas medidas económicas',
        'enlace': 'https://elpais.com/economia/2025-12-10/china-medidas.html',
        'descripcion': 'El gobierno chino presenta un paquete de estímulos',
        'texto_completo': 'Beijing, 10 de diciembre. El gobierno chino...'
    }
    
    datos_clasificacion = {
        'tema': 'Economía',
        'imagen_de_china': 'Positiva',
        'resumen_dos_frases': 'China lanza estímulos económicos. Medidas buscan reactivar el consumo.'
    }
    
    exito = guardar_noticia_en_excel(
        datos_noticia,
        datos_clasificacion,
        'data/noticias_historico.xlsx'
    )
    """)
