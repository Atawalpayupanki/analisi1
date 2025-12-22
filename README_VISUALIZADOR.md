# 📊 Visualizador de Datos - Guía Rápida

## ¿Qué es?

Una herramienta web interactiva para analizar visualmente tus noticias clasificadas sobre China. Permite ver estadísticas, gráficos y filtrar datos de forma intuitiva.

## Cómo Usar

### Opción 1: Desde la GUI (Recomendado)
1. Abre la aplicación principal
2. Haz clic en **"📊 VISUALIZADOR DE DATOS"**
3. ¡Listo! Se abrirá en tu navegador

### Opción 2: Desde Python
```bash
python abrir_visualizador.py
```

### Opción 3: Directamente
Abre el archivo `visualizador.html` en tu navegador

## Características Principales

### 🔍 Filtros
- **Tema**: Geopolítica, Economía, Tecnología, etc.
- **Imagen de China**: Positiva, Negativa, Neutral, Amenaza
- **Procedencia**: España, China, etc.
- **Medio**: El País, ABC, El Mundo, etc.
- **Búsqueda**: Busca palabras en titulares

### 📊 Visualizaciones
- **Estadísticas**: Total noticias, temas, medios
- **Gráfico de Temas**: Top 10 temas más frecuentes
- **Gráfico de Imagen**: Distribución de percepciones
- **Gráfico de Procedencia**: Origen de las noticias
- **Gráfico de Medios**: Top 10 medios

### 💾 Exportación
- Exporta datos filtrados a CSV
- Incluye todos los campos relevantes
- Nombre automático con fecha

## Ejemplo de Uso

1. **Selecciona** "Negativa" en "Imagen de China"
2. **Haz clic** en "Aplicar Filtros"
3. **Observa** los gráficos actualizados
4. **Revisa** la tabla de resultados
5. **Exporta** si necesitas los datos

## Requisitos

- Navegador web moderno (Chrome, Firefox, Edge, Safari)
- Archivo `data/noticias_china.csv` debe existir
- JavaScript habilitado

## Archivos Creados

- `visualizador.html` - Herramienta principal
- `abrir_visualizador.py` - Script Python
- Botón integrado en `src/gui.py`

## Documentación Completa

Ver `visualizador_docs.md` en la carpeta de artifacts para más detalles.

---

**¡Disfruta analizando tus datos! 📊✨**
