# Plantilla TFG GIS UBU – Quarto

> Plantilla [Quarto](https://quarto.org/) para la **Memoria** y la **Documentación Técnica (Anexos)** del
> Trabajo Fin de Grado 
> Grado en Ingeniería de la Salud
> Universidad de Burgos.
>

# Índice

- [Estructura de archivos](#estructura-de-archivos)
- [Primeros pasos](#primeros-pasos)

- [Software necesario si trabajas con RStudio / Positron](#software-necesario-si-trabajas-con-rstudio--positron)
  - [Instalar R](#1-instalar-r)
  - [Instalar Quarto](#2-instalar-quarto)
  - [Instalar RStudio o Positron](#3-instalar-rstudio-o-positron)
  - [Instalar LaTeX](#4-instalar-latex)
  - [Instalar paquetes de R necesarios](#5-instalar-paquetes-de-r-necesarios)
  - [Instalar Python](#6-instalar-python)

- [Software necesario si trabajas con Visual Studio Code](#software-necesario-si-trabajas-con-visual-studio-code)
  - [Instalar Visual Studio Code](#1-instalar-visual-studio-code)
  - [Instalar Quarto](#2-instalar-quarto-1)
  - [Instalar LaTeX](#4-instalar-latex-1)
  - [Instalar R](#4-instalar-r-solo-si-vas-a-ejecutar-código-r)
  - [Instalar Python](#5-instalar-python)
  - [Instalar extensiones de VS Code](#6-instalar-extensiones-de-vs-code)

- [Manejo de la plantilla](#manejo-de-la-plantilla)
  - [Introduce tus datos personales](#paso-1--introduce-tus-datos-personales)
  - [Compilar el PDF](#paso-2--compila-el-pdf)

- [Cómo escribir tu TFG](#cómo-escribir-tu-tfg)
  - [Texto normal](#texto-normal)
  - [Citar bibliografía](#citar-bibliografía)
  - [Incluir una tabla generada con R](#incluir-una-tabla-generada-con-r)
  - [Incluir una figura generada con R](#incluir-una-figura-generada-con-r)
  - [Mostrar u ocultar código](#mostrar-u-ocultar-el-código-r-en-el-pdf)
  - [Incluir una imagen](#incluir-una-imagen-clásica-no-generada-con-r)

- [Preguntas frecuentes](#preguntas-frecuentes)

- [Notas técnicas](#notas-técnicas-para-usuarios-avanzados)

- [Autoría y agradecimientos](#autoría-y-agradecimientos)



## Estructura de archivos

```
PlantillaTFG_Quarto/
├── memoria.qmd
├── anexos.qmd
├── preambulo_memoria.tex
├── preambulo_anexos.tex
├── bibliografia.bib
├── bibliografiaAnexos.bib
├── README.md
├── memoria.pdf
├── anexos.pdf
├── img/
│   ├── CabeceraEPS.png
│   └── Logo_GIS.png
└── qmd/
    ├── 1_introduccion.qmd
    ├── 2_objetivos.qmd
    ├── 3_teoricos.qmd
    ├── 4_metodologia.qmd
    ├── 5_resultados.qmd
    ├── 6_discusion.qmd
    ├── 7_conclusiones.qmd
    ├── 8_lineas_futuras.qmd
    ├── A_planificacion.qmd
    ├── B_diseno.qmd
    ├── C_requisitos.qmd
    ├── D_manual_usuario.qmd
    ├── E_manual_programador.qmd
    ├── F_datos.qmd
    ├── G_experimental.qmd
    ├── H_ODS.qmd
    └── I_prompts.qmd
```

Los archivos dentro de **`qmd/`** contienen los **capítulos del TFG** que se
incluyen automáticamente dentro de `memoria.qmd` y `anexos.qmd`.

---

# Primeros pasos

1. Instalar el software necesario (ver secciones siguientes).
2. Introducir tus datos personales en:
   - `preambulo_memoria.tex`
   - `preambulo_anexos.tex`
3. Compilar el documento pulsando **Render** sobre:
   - `memoria.qmd`
   - `anexos.qmd`

---

# Software necesario si trabajas con RStudio / Positron

## 1. Instalar R

Descargar desde:

[cran.r-project.org](https://cran.r-project.org) 

Se recomienda una versión **≥ 4.3**.


## 2. Instalar Quarto

Descargar desde:

[quarto.org/docs/download](https://quarto.org/docs/download/) 

Comprobar instalación:

```bash
quarto check
```


## 3. Instalar RStudio o Positron

RStudio
[RStudio](https://posit.co/download/rstudio-desktop/)

Positron
[posit.co](https://positron.posit.co/download.html) 


## 4. Instalar LaTeX

Es necesario para generar el PDF.

***Windows***:

[MiKTeX](https://miktex.org)

***Linux / Mac***:

[TeX Live](https://tug.org/texlive)

Se recomienda instalar la versión completa.

## 5. Instalar paquetes de R necesarios

Abrir la consola de R y ejecutar:
```R
# El listado de paquetes necesarios dependerá de cada proyecto
install.packages(c(
  "knitr",
  "dplyr",
  "ggplot2",
  "tidyr",
  .
  .
  .

))
```

## 6. Instalar Python

Python es necesario si quieres ejecutar código Python dentro del documento Quarto.

Descargar desde:

https://www.python.org/downloads/

Se recomienda instalar una versión **≥ 3.10**.

Durante la instalación en Windows marca la opción:
`Add Python to PATH`


Para comprobar la instalación abre una terminal y ejecuta:

```bash
python --version
```
o
```bash
python3 --version
```
Si deseas usar Python dentro de Quarto desde RStudio, instala también el paquete de R:
```R
install.packages("reticulate")
```

---

# Software necesario si trabajas con Visual Studio Code

## 1. Instalar Visual Studio Code

Descargar desde:

https://code.visualstudio.com

## 2. Instalar Quarto

Descargar desde:

https://quarto.org/docs/download/

Comprobar instalación ejecutando:
```bash
quarto check
```

## 4. Instalar LaTeX

Es necesario para generar el PDF.

*Windows*:

MiKTeX
https://miktex.org

*Linux / Mac*:

TeX Live
https://tug.org/texlive

Se recomienda instalar la versión completa.


## 4. Instalar R (solo si vas a ejecutar código R)

Descargar desde:

https://cran.r-project.org

Después instalar los paquetes necesarios:
```R
install.packages(c(
  "knitr",
  "dplyr",
  "ggplot2",
  "tidyr"
))
```

## 5. Instalar Python

Necesario si vas a ejecutar código Python dentro de documentos `.qmd`.

Descargar desde:

https://www.python.org/downloads/

Se recomienda una versión **≥ 3.10**.

Durante la instalación en Windows marca:

`Add Python to PATH`

Comprobar instalación:

```bash
python --version
```

## 6. Instalar extensiones de VS Code

Abrir el panel de extensiones:

`Ctrl + Shift + X`

Instalar:

- Quarto → soporte para documentos .qmd

- LaTeX Workshop → soporte para LaTeX

- R → integración con R (opcional)

- Python (Microsoft)

- Pylance

---

# MANEJO DE LA PLANTILLA

## Paso 1 — Introduce tus datos personales

Abre **`preambulo_memoria.tex`** y busca el bloque señalado con el comentario
`EDITAR ESTOS DATOS`. Cambia los valores por los tuyos:

```latex
% ── EDITAR ESTOS DATOS ──────────────────────────────────────
\newcommand{\nombre}{María García López}          % Tu nombre completo
\newcommand{\nombreTutor}{Juan Pérez Martínez}    % Nombre del tutor/a 1
\newcommand{\nombreTutorb}{Ana Sánchez Ruiz}      % Nombre del tutor/a 2
\newcommand{\dni}{12345678A}                      % Tu DNI
% ────────────────────────────────────────────────────────────
```

Después abre el **primer bloque `{=latex}`** de `memoria.qmd` y cambia el título:

```latex
\title{Detección automática de arritmias mediante aprendizaje profundo}
```

Repite exactamente lo mismo en **`preambulo_anexos.tex`** y en `anexos.qmd`.

> ⚠️ Si solo tienes **un tutor**, comenta la línea `\tutorb` en el preámbulo y
> en la portada cambia `Tutores:` por `Tutor:` en la línea correspondiente.


---

## Paso 2 — Compila el PDF

La plantilla genera el PDF a partir de los archivos `.qmd` utilizando **Quarto**.  
Se puede compilar desde **RStudio / Positron** o desde **Visual Studio Code**.

### RStudio/Positron

#### 1. Abrir el proyecto

Abrir RStudio o Positron y seleccionar: `File → Open File`

Abrir el archivo:

`memoria.qmd` o `anexos.qmd`



#### 2. Renderizar el documento

En la parte superior del editor aparecerá el botón:

`Render`

Pulsarlo para generar el PDF.


#### 3. Archivo generado

Tras la compilación se generará: `memoria.pdf` o `anexos.pdf` en la misma carpeta del proyecto.


#### 4. Compilar desde la terminal (opcional)

También puede ejecutarse desde la consola:

```bash
quarto render memoria.qmd --to pdf
quarto render anexos.qmd --to pdf
```

> * Existe la opción de cambiar el argumento `--to pdf` para incluir un renderizado en formato word `--to .docx` (cuidado con el formato).

---

### VScode

#### 1. Abrir la carpeta del proyecto

En VS Code seleccionar: `File → Open Folder` y abrir la carpeta del proyecto.


#### 2. Abrir el documento:
Abrir el archivo: `memoria.qmd` o `anexos.qmd`



#### 3. Renderizar el documento

En la parte superior del editor aparecerá el botón:

`Render`

Pulsarlo para generar el PDF.



#### 4. Archivo generado

Tras la compilación se generará: `memoria.pdf` o `anexos.pdf` en la misma carpeta del proyecto.



#### 5. Compilar desde la terminal (opcional)

Abrir la terminal en VS Code: `Terminal → New Terminal`

```bash
quarto render memoria.qmd
quarto render anexos.qmd
```



# Cómo escribir tu TFG

## Texto normal
Escribe en Markdown directamente después de cada bloque `{=latex}` que marca
el inicio de un capítulo. Por ejemplo:

```markdown
```{=latex}
\capitulo{2}{Objetivos}
```

En este apartado se definen los **objetivos** del trabajo...

## Objetivo general

```markdown
Desarrollar un sistema capaz de...
```

## Citar bibliografía
Añade tus referencias en `bibliografia.bib` y cítalas en el texto con:

```markdown
Como señalan [@bortolot2005], los métodos basados en LiDAR...
```

El estilo de cita es **APA** (autor, año) y la bibliografía se genera
automáticamente al final del documento.

## Incluir una tabla generada con R

```r
#| label: tbl-mi-tabla
#| tbl-cap: "Descripción de la tabla"

library(knitr)
mi_datos |>
  kable(booktabs = TRUE, format = "latex")
```

## Incluir una figura generada con R (o Python adaptando el código)

```r
#| label: fig-mi-figura
#| fig-cap: "Descripción de la figura"

library(ggplot2)
ggplot(mis_datos, aes(x = variable1, y = variable2)) +
  geom_point() +
  theme_minimal()
```

## Mostrar u ocultar el código (R/Python) en el PDF
- El código es **visible por defecto** en esta plantilla (`echo: true`).
- Para ocultar el código de un chunk concreto añade `#| echo: false` al inicio.
- Para ocultar el código de todo el documento, cambia `echo: true` a
  `echo: false` en la sección `knitr > opts_chunk` del YAML.

> * Más información de las opciones en pdf de Quarto la puedes encontrar [aquí](https://quarto.org/docs/output-formats/pdf-basics.html)

## Incluir una imagen clásica (no generada con R/Python)
Coloca la imagen en la carpeta `img/` y usa:

```latex
```{=latex}
\imagen{img/mi_esquema.png}{Descripción de la imagen}{0.8}
```

El tercer parámetro (`0.8`) es la escala relativa al ancho de página (entre 0 y 1).


---

# Preguntas frecuentes

- **¿Por qué el `title:` del YAML está como `" "` (espacio en blanco)?**
Para evitar que Quarto genere una portada automática que se solaparía con la
portada personalizada de la UBU. El título real del TFG se pone dentro del
bloque `{=latex}` al inicio del documento.

- **¿Por qué hay archivos `.tex` además de los `.qmd`?**
La portada, los índices y los estilos de la plantilla UBU requieren comandos
LaTeX avanzados que no se pueden configurar solo desde el YAML de Quarto. Los
preámbulos `.tex` contienen toda esa lógica y se cargan automáticamente al
compilar.

- **El PDF sale con errores de paquetes LaTeX que no encuentra.**
Asegúrate de tener TeX Live o MiKTeX en versión **completa**. Si usas TeX Live
puedes instalar paquetes concretos con:
```bash
tlmgr install memoir booktabs microtype lmodern
```

---

# Notas técnicas (para usuarios avanzados)

- Se usa la clase **`memoir`** con estilo de capítulos `bianchi`, igual que la
  plantilla LaTeX original de la UBU.
- Los comandos `\capitulo{}{}` y `\apendice{}{}` están definidos en los
  preámbulos `.tex` y se invocan desde bloques `{=latex}`.
- Motor de compilación: **pdflatex**. Si necesitas soporte Unicode avanzado
  (fuentes especiales, caracteres no latinos), cambia en el YAML:
  `pdf-engine: xelatex`.
- Los índices (TOC, LOF, LOT) se gestionan manualmente desde un bloque
  `{=latex}` para mantener el orden correcto con la clase `memoir`.

---
<br>

---

# Autoría y Agradecimientos

Esta plantilla ha sido elaborada por los profesores [Antonio Canepa](https://investigacion.ubu.es/investigadores/35040/detalle) y [David García](https://investigacion.ubu.es/investigadores/326207/detalle), con la colaboración de los profesores miembros del tribunal [Sonia Ramos](https://investigacion.ubu.es/investigadores/35462/detalle) y [Pedro Luis Sánchez](https://investigacion.ubu.es/investigadores/35529/detalle).