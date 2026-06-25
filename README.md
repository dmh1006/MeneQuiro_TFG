<p align="center">
  <img src="https://raw.githubusercontent.com/dmh1006/TFG_DarioMeneses/main/assets/CabeceraEPS.png" width="900">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/dmh1006/TFG_DarioMeneses/main/assets/Logo_GIS.png" width="260">
</p>

#  MeneQuiro

### Sistema inteligente para la planificación quirúrgica basado en el análisis histórico de intervenciones y la recomendación automática de huecos

**Trabajo Fin de Grado · Ingeniería de la Salud**

**Universidad de Burgos**

---

### Optimización de la planificación quirúrgica mediante análisis histórico y recomendación inteligente de huecos

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20Application-red?logo=streamlit)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Visualization-3F4F75?logo=plotly)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite)
![OpenPyXL](https://img.shields.io/badge/OpenPyXL-Excel-green)
![License](https://img.shields.io/badge/License-Academic-lightgrey)

---

**Autoría**

Alumno: Darío Meneses

Tutores: Alejandro Merino Gomez y Daniel Sarabia Ortiz

Grado en Ingeniería de la Salud

Universidad de Burgos

</div>

---

#  Descripción

Este proyecto presenta el desarrollo de una **herramienta web inteligente para la planificación quirúrgica**, diseñada como Trabajo Fin de Grado del Grado en Ingeniería de la Salud.

La aplicación nace con el objetivo de facilitar la planificación diaria de los quirófanos mediante el análisis del histórico de intervenciones realizadas, permitiendo recomendar automáticamente los mejores huecos disponibles para nuevas cirugías.

A diferencia de un planificador tradicional, el sistema no únicamente representa la información existente, sino que utiliza los datos históricos para **estimar tiempos quirúrgicos**, **analizar la ocupación**, **buscar automáticamente el mejor quirófano** y generar una planificación optimizada.

---

#  Objetivos

Los principales objetivos del proyecto son:

- Diseñar una aplicación web intuitiva para personal sanitario.
- Automatizar parcialmente el proceso de planificación quirúrgica.
- Reducir tiempos muertos entre intervenciones.
- Minimizar conflictos de planificación.
- Aprovechar el histórico quirúrgico para realizar recomendaciones inteligentes.
- Facilitar la gestión diaria de la programación.
- Incorporar herramientas de análisis para apoyar la toma de decisiones.

---

#  Funcionalidades principales

##  Agenda quirúrgica

Visualización completa de la planificación diaria mediante un calendario interactivo organizado por quirófanos.

Permite visualizar:

- Hora de inicio
- Hora de finalización
- Procedimiento
- Cirujano
- Estado de la intervención
- Planificaciones simuladas

---

##  Propuesta inteligente de huecos

El sistema analiza automáticamente:

- Agenda del día
- Procedimientos históricos
- Duraciones medias
- Quirófanos habituales
- Tiempo disponible
- Holgura existente

Y genera automáticamente las mejores propuestas ordenadas por prioridad.

---

##  Análisis histórico

La aplicación incorpora herramientas para estudiar el comportamiento histórico del bloque quirúrgico.

Entre otras métricas:

- Número de cirugías
- Tiempo medio de intervención
- Procedimientos más frecuentes
- Variabilidad de duración
- Utilización por quirófano
- Ocupación diaria
- Tiempo muerto entre intervenciones

---

##  Catálogo inteligente de procedimientos

El sistema construye automáticamente un catálogo a partir del histórico.

Para cada procedimiento calcula:

- Duración media
- Mediana
- Desviación típica
- Número de intervenciones
- Quirófanos habituales

Además incorpora un sistema de normalización que corrige:

- Errores ortográficos
- Acentos
- Abreviaturas
- Variantes del mismo procedimiento

---

##  Simulación de planificación

Es posible añadir nuevas intervenciones sin modificar el histórico real.

La simulación incluye:

- Selección automática del mejor hueco.
- Comprobación de solapes.
- Registro del paciente.
- Cirujano.
- Anestesista.
- Eliminación individual.
- Vaciado completo.

---

##  Registro de intervenciones realizadas

Una planificación puede confirmarse posteriormente como intervención realizada.

El sistema almacena:

- Hora real
- Duración
- Observaciones
- Estado

---

##  Exportación

La aplicación permite exportar información en:

- Excel
- CSV
- PDF

---

##  Planificador de guardias

Se incluye un segundo módulo destinado a la planificación automática de guardias hospitalarias.

Características:

- Reparto equilibrado.
- Restricciones personalizadas.
- Exportación automática.
- Resumen estadístico.

---

#  Funcionamiento interno

El algoritmo sigue las siguientes fases:

```
Carga de datos
        │
        ▼
Limpieza y normalización
        │
        ▼
Construcción del catálogo
        │
        ▼
Estimación de duración
        │
        ▼
Obtención de agenda diaria
        │
        ▼
Búsqueda de huecos
        │
        ▼
Evaluación de candidatos
        │
        ▼
Propuesta ordenada
        │
        ▼
Simulación de planificación
```

---

#  Arquitectura del proyecto

```
TFG_DarioMeneses
│
├── Proyecto
│   ├── planificador_tfg.py
│   ├── planificador_guardias.py
│   ├── limpiar_csv.py
│   └── analisis_quirofano.py
│
├── Data
│   ├── 2025.xlsx
│   ├── Qº FEBRERO.xls
│   └── Base de datos
│
├── PlantillaTFG_Quarto-main
│
├── app_streamlit_quirofanos_tfg.py
│
├── requirements.txt
│
└── README.md
```

---

#  Tecnologías utilizadas

| Tecnología | Uso |
|------------|-----|
| Python | Desarrollo principal |
| Streamlit | Aplicación web |
| Pandas | Procesamiento de datos |
| Plotly | Visualización |
| SQLite | Base de datos |
| OpenPyXL | Exportación Excel |
| ReportLab | Generación PDF |
| Quarto | Memoria del TFG |

---

#  Instalación

Clonar el repositorio

```bash
git clone https://github.com/dmh1006/TFG_DarioMeneses.git
```

Entrar en el proyecto

```bash
cd TFG_DarioMeneses
```

Instalar dependencias

```bash
pip install -r requirements.txt
```

Ejecutar la aplicación

```bash
streamlit run app_streamlit_quirofanos_tfg.py
```

---

#  Posibles mejoras futuras

- Integración con PostgreSQL.
- Predicción mediante Machine Learning.
- Conexión directa con el sistema hospitalario.
- Gestión multiusuario.
- Control de permisos.
- Dashboard ejecutivo.
- Estadísticas avanzadas.
- Predicción automática de cancelaciones.
- Optimización basada en Inteligencia Artificial.

---

#  Trabajo académico

Este repositorio contiene el desarrollo íntegro del Trabajo Fin de Grado:

**"Sistema inteligente para la planificación quirúrgica mediante análisis histórico y recomendación automática de huecos"**

Grado en Ingeniería de la Salud

Universidad de Burgos

---

#  Autor

**Darío Meneses**

**En colaboración con los tutores: Alejandro Merino Gomez y Daniel Sarabia Ortiz**

Grado en Ingeniería de la Salud

Universidad de Burgos

---


