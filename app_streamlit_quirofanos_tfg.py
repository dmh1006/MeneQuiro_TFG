from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
import os
import tempfile
from datetime import date

from Proyecto.planificador_tfg import (
    agenda_dia,
    analisis_procedimientos,
    construir_catalogo_quirurgico,
    cargar_datos,
    obtener_agenda_combinada,
    ocupacion_por_dia_quirofano,
    preparar_dataset_funcional,
    proponer_huecos,
    resumen_general,
    tiempos_muertos,
    uso_quirofanos,
)

from Proyecto.planificador_guardias import (
    PERSONAS,
    FESTIVOS,
    generar_planificacion,
    construir_dataframe_planificacion,
    construir_dataframe_resumen,
    exportar_excel,
)

st.set_page_config(
    page_title="Planificación de quirófanos · TFG",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def cargar_base() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = cargar_datos()
    df_real = preparar_dataset_funcional(df)
    catalogo = construir_catalogo_quirurgico(df_real)
    return df, df_real, catalogo


def inicializar_estado() -> None:
    if "cirugias_anadidas" not in st.session_state:
        st.session_state.cirugias_anadidas = []


# ----------------------------------------------------------
# UTILIDADES VISUALES
# ----------------------------------------------------------

def minutos_desde_referencia(ts: pd.Timestamp, referencia: pd.Timestamp) -> float:
    return (ts - referencia).total_seconds() / 60


def figura_timeline_agenda(agenda: pd.DataFrame, fecha: pd.Timestamp, titulo: str) -> go.Figure:
    """
    Genera una agenda diaria estilo panel de quirófanos:
    - una fila por quirófano
    - bloques horizontales por cirugía
    - información relevante dentro del bloque
    - rejilla horaria marcada
    """
    fecha = pd.to_datetime(fecha)
    inicio_bloque = pd.Timestamp(f"{fecha.strftime('%Y-%m-%d')} 08:00:00")
    fin_bloque = pd.Timestamp(f"{fecha.strftime('%Y-%m-%d')} 20:00:00")

    fig = go.Figure()

    if agenda.empty:
        fig.update_layout(
            title=titulo,
            template="plotly_white",
            height=500,
            xaxis_title="Hora del día",
            yaxis_title="Quirófano",
        )
        fig.add_annotation(
            text="No hay cirugías registradas para este día.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    data = agenda.copy()
    data["inicio_dt"] = pd.to_datetime(data["inicio_dt"], errors="coerce")
    data["fin_dt"] = pd.to_datetime(data["fin_dt"], errors="coerce")
    data = data.dropna(subset=["quirofano", "inicio_dt", "fin_dt"]).copy()

    # Campos principales
    if "procedimiento_base" not in data.columns:
        if "procedimiento" in data.columns:
            data["procedimiento_base"] = data["procedimiento"]
        else:
            data["procedimiento_base"] = "Sin nombre"

    if "fuente" not in data.columns:
        data["fuente"] = "Histórico"

    # Campos opcionales que queremos enseñar
    columnas_opcionales = [
        "cirujano_principal",
        "anestesista_principal",
        "servicio",
        "tipo_caso",
        "turno",
        "ambulatorio",
        "anestesia",
    ]
    for col in columnas_opcionales:
        if col not in data.columns:
            data[col] = ""

    data["duracion_min"] = (
        (data["fin_dt"] - data["inicio_dt"]).dt.total_seconds() / 60
    ).round()

    quirofanos = sorted(data["quirofano"].astype(str).unique().tolist())

    # Paleta visual más seria
    colores = {
        "Histórico": "#A7C7E7",
        "Propuesta añadida": "#2F6DB3",
    }

    # Fondo tipo panel por cada quirófano
    for q in quirofanos:
        fig.add_trace(
            go.Bar(
                x=[(fin_bloque - inicio_bloque).total_seconds() / 3600],
                y=[q],
                base=[inicio_bloque],
                orientation="h",
                marker=dict(
                    color="rgba(210, 210, 210, 0.22)",
                    line=dict(width=0),
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # Dibujar cada cirugía
    leyendas_ya_puestas = set()

    for _, fila in data.sort_values(["quirofano", "inicio_dt"]).iterrows():
        duracion_horas = (fila["fin_dt"] - fila["inicio_dt"]).total_seconds() / 3600
        fuente = fila["fuente"]
        color = colores.get(fuente, "#90A4AE")

        procedimiento = str(fila["procedimiento_base"]) if pd.notna(fila["procedimiento_base"]) else "Sin nombre"
        cirujano = str(fila["cirujano_principal"]) if pd.notna(fila["cirujano_principal"]) else ""
        anestesista = str(fila["anestesista_principal"]) if pd.notna(fila["anestesista_principal"]) else ""
        servicio = str(fila["servicio"]) if pd.notna(fila["servicio"]) else ""
        tipo_caso = str(fila["tipo_caso"]) if pd.notna(fila["tipo_caso"]) else ""
        anestesia = str(fila["anestesia"]) if pd.notna(fila["anestesia"]) else ""

        # Texto visible dentro del bloque
        texto_bloque = procedimiento
        if len(texto_bloque) > 26:
            texto_bloque = texto_bloque[:26] + "..."

        if duracion_horas >= 1.2 and cirujano:
            texto_bloque += f"<br><sup>{cirujano}</sup>"

        # Hover detallado
        hover = (
            f"<b>{procedimiento}</b><br>"
            f"Quirófano: {fila['quirofano']}<br>"
            f"Inicio: {fila['inicio_dt'].strftime('%H:%M')}<br>"
            f"Fin: {fila['fin_dt'].strftime('%H:%M')}<br>"
            f"Duración: {int(fila['duracion_min'])} min<br>"
        )

        if servicio:
            hover += f"Servicio: {servicio}<br>"
        if cirujano:
            hover += f"Cirujano: {cirujano}<br>"
        if anestesista:
            hover += f"Anestesista: {anestesista}<br>"
        if anestesia:
            hover += f"Anestesia: {anestesia}<br>"
        if tipo_caso:
            hover += f"Tipo de caso: {tipo_caso}<br>"

        hover += f"Origen: {fuente}<extra></extra>"

        nombre_leyenda = fuente if fuente not in leyendas_ya_puestas else None
        if fuente not in leyendas_ya_puestas:
            leyendas_ya_puestas.add(fuente)

        fig.add_trace(
            go.Bar(
                x=[duracion_horas],
                y=[str(fila["quirofano"])],
                base=[fila["inicio_dt"]],
                orientation="h",
                marker=dict(
                    color=color,
                    line=dict(color="rgba(40,40,40,0.35)", width=1),
                ),
                text=[texto_bloque],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=11, color="black"),
                name=nombre_leyenda,
                legendgroup=fuente,
                showlegend=nombre_leyenda is not None,
                hovertemplate=hover,
            )
        )

    # Líneas verticales por hora
    for hora in range(8, 21):
        x_hora = pd.Timestamp(f"{fecha.strftime('%Y-%m-%d')} {hora:02d}:00:00")
        fig.add_vline(
            x=x_hora,
            line_width=1,
            line_dash="solid",
            line_color="rgba(100,100,100,0.20)",
            layer="below",
        )

    # Líneas secundarias cada 30 min
    for hora in range(8, 20):
        x_media = pd.Timestamp(f"{fecha.strftime('%Y-%m-%d')} {hora:02d}:30:00")
        fig.add_vline(
            x=x_media,
            line_width=1,
            line_dash="dot",
            line_color="rgba(120,120,120,0.12)",
            layer="below",
        )

    fig.update_layout(
        title=titulo,
        template="plotly_white",
        barmode="overlay",
        height=max(500, 90 * len(quirofanos) + 140),
        margin=dict(l=40, r=20, t=60, b=40),
        legend_title="Origen",
        plot_bgcolor="#F2F2F2",
        paper_bgcolor="white",
        font=dict(size=12),
    )

    fig.update_xaxes(
        range=[inicio_bloque, fin_bloque],
        tickformat="%H:%M",
        dtick=60 * 60 * 1000,
        title="Hora del día",
        showgrid=False,
    )

    fig.update_yaxes(
        title="Quirófano",
        autorange="reversed",
        categoryorder="array",
        categoryarray=quirofanos,
        showgrid=False,
    )

    return fig


def figura_ocupacion_diaria(df_ocup: pd.DataFrame) -> go.Figure:
    fig = px.imshow(
        df_ocup,
        text_auto='.0f',
        aspect='auto',
        labels=dict(x="Quirófano", y="Fecha", color="% ocupación"),
    )
    fig.update_layout(height=700, template="plotly_white", margin=dict(l=10, r=10, t=40, b=10))
    return fig


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "agenda") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

# ----------------------------------------------------------
# FUNCIONES AUXILIARES DEL PLANIFICADOR DE GUARDIAS
# ----------------------------------------------------------

def parsear_festivos(texto_festivos: str) -> set[date]:
    festivos = set()

    for linea in texto_festivos.splitlines():
        linea = linea.strip()
        if not linea:
            continue

        try:
            festivos.add(pd.to_datetime(linea, dayfirst=True).date())
        except Exception:
            st.warning(f"No se ha podido interpretar el festivo: {linea}")

    return festivos


def exportar_guardias_excel_bytes(df_plan: pd.DataFrame, df_resumen: pd.DataFrame) -> bytes:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.close()

    try:
        exportar_excel(df_plan, df_resumen, tmp.name)

        with open(tmp.name, "rb") as f:
            contenido = f.read()

    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

    return contenido


def colorear_guardias(row):
    colores = {
        "laborable": "background-color: #EAF2F8",
        "viernes": "background-color: #D4E6F1",
        "sabado": "background-color: #FCF3CF",
        "domingo": "background-color: #FADBD8",
        "festivo": "background-color: #F5CBA7",
    }

    return [colores.get(row["tipo_dia"], "") for _ in row]


# ----------------------------------------------------------
# APP
# ----------------------------------------------------------

def main() -> None:
    inicializar_estado()
    _, df_real, catalogo = cargar_base()

    st.title("🏥 Planificador quirúrgico inteligente")
    st.caption("Prototipo funcional orientado a TFG: análisis histórico, propuesta de huecos y simulación de agenda.")

    with st.sidebar:
        st.header("Configuración")
        fechas_disponibles = sorted(df_real["fecha"].dt.date.unique())
        fecha_sel = st.date_input(
            "Fecha de trabajo",
            value=fechas_disponibles[0],
            min_value=fechas_disponibles[0],
            max_value=fechas_disponibles[-1],
        )
        procedimientos = sorted(catalogo["procedimiento_base"].tolist())
        procedimiento_sel = st.selectbox("Procedimiento a planificar", procedimientos)
        max_resultados = st.slider("Número de propuestas", 1, 10, 5)
        quirofanos_disponibles = sorted(df_real["quirofano"].dropna().astype(str).unique())
        filtro_qx = st.multiselect(
            "Restringir a quirófanos",
            options=quirofanos_disponibles,
            default=quirofanos_disponibles,
        )

    fecha_ts = pd.to_datetime(fecha_sel)
    agenda_historica = agenda_dia(df_real, fecha_ts)
    agenda_combinada = obtener_agenda_combinada(df_real, fecha_ts, st.session_state.cirugias_anadidas)
    propuestas = proponer_huecos(
        df_real=df_real,
        catalogo=catalogo,
        procedimiento=procedimiento_sel,
        fecha=fecha_ts,
        quirofanos_validos=filtro_qx,
        max_resultados=max_resultados,
    )

    # KPIs
    kpis = resumen_general(df_real)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Cirugías", kpis["n_cirugias"])
    c2.metric("Quirófanos", kpis["n_quirofanos"])
    c3.metric("Servicios", kpis["n_servicios"])
    c4.metric("Horas analizadas", kpis["tiempo_total_horas"])
    c5.metric("Duración media (min)", kpis["duracion_media_min"])
    c6.metric("Urgencias (%)", kpis["pct_urgencias"])

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Planificación diaria",
    "Análisis histórico",
    "Ocupación mensual",
    "Exportación",
    "Planificador de guardias",
])

    with tab1:
        left, right = st.columns([1.1, 0.9])

        with left:
            st.subheader(f"Agenda del día · {fecha_ts.strftime('%d/%m/%Y')}")
            render_agenda_visual(
                agenda_combinada,
                fecha_ts,
                "Agenda combinada (histórico + simulación)"
            )
        with right:
            st.subheader("Propuestas de hueco")
            if propuestas.empty:
                st.warning("No se han encontrado huecos válidos para ese procedimiento con los filtros actuales.")
            else:
                propuestas_view = propuestas.copy()
                propuestas_view["inicio"] = propuestas_view["inicio"].dt.strftime("%H:%M")
                propuestas_view["fin_estimado"] = propuestas_view["fin_estimado"].dt.strftime("%H:%M")
                st.dataframe(
                    propuestas_view[[
                        "quirofano",
                        "inicio",
                        "fin_estimado",
                        "duracion_necesaria",
                        "duracion_disponible",
                        "holgura_min",
                        "es_quirofano_habitual",
                    ]],
                    use_container_width=True,
                    hide_index=True,
                )

                idx = st.selectbox(
                    "Selecciona propuesta para añadir a la simulación",
                    options=list(propuestas.index),
                    format_func=lambda i: f"{propuestas.loc[i, 'quirofano']} · {propuestas.loc[i, 'inicio'].strftime('%H:%M')} - {propuestas.loc[i, 'fin_estimado'].strftime('%H:%M')}",
                )
                col_p1, col_p2, col_p3 = st.columns(3)

                with col_p1:
                    paciente_sim = st.text_input(
                        "Paciente",
                        key="paciente_sim",
                        placeholder="Nombre y apellidos del paciente",
                    )

                with col_p2:
                    cirujano_sim = st.text_input(
                        "Cirujano principal",
                        key="cirujano_sim",
                        placeholder="Nombre del cirujano",
                    )

                with col_p3:
                    anestesista_sim = st.text_input(
                        "Anestesista principal",
                        key="anestesista_sim",
                        placeholder="Nombre del anestesista",
                    )

                # EVITAMOS A TODA COSTA QUE HAYA SOLAPAMIENTOS
                if st.button("Añadir cirugía a la agenda", type="primary"):
                    fila = propuestas.loc[idx].to_dict()

                    nueva = {
                        "fecha": fecha_ts,
                        "quirofano": fila["quirofano"],
                        "inicio_dt": pd.to_datetime(fila["inicio"]),
                        "fin_dt": pd.to_datetime(fila["fin_estimado"]),
                        "procedimiento_base": fila["procedimiento"],
                        "duracion_min": fila["duracion_necesaria"],
                        "holgura_min": fila.get("holgura_min", None),
                        "fuente": "Propuesta añadida",
                        "es_quirofano_habitual": fila.get("es_quirofano_habitual", None),
                        "paciente": paciente_sim,
                        "cirujano_principal": cirujano_sim,
                        "anestesista_principal": anestesista_sim,
                    }

                    agenda_actual = obtener_agenda_combinada(
                        df_real,
                        fecha_ts,
                        st.session_state.cirugias_anadidas,
                    )

                    inicio_nuevo = pd.to_datetime(nueva["inicio_dt"])
                    fin_nuevo = pd.to_datetime(nueva["fin_dt"])
                    quirofano_nuevo = str(nueva["quirofano"])

                    agenda_q = agenda_actual[
                        agenda_actual["quirofano"].astype(str) == quirofano_nuevo
                    ].copy()

                    hay_solape = False

                    if not agenda_q.empty:
                        agenda_q["inicio_dt"] = pd.to_datetime(agenda_q["inicio_dt"])
                        agenda_q["fin_dt"] = pd.to_datetime(agenda_q["fin_dt"])

                        for _, existente in agenda_q.iterrows():
                            inicio_existente = existente["inicio_dt"]
                            fin_existente = existente["fin_dt"]

                            if inicio_nuevo < fin_existente and fin_nuevo > inicio_existente:
                                hay_solape = True
                                break

                    if hay_solape:
                        st.error(
                            f"No se puede añadir la cirugía porque se solapa con otra en {quirofano_nuevo}."
                        )
                    else:
                        st.session_state.cirugias_anadidas.append(nueva)
                        st.success("Cirugía añadida a la simulación de agenda.")
                        st.rerun()

                if st.session_state.cirugias_anadidas and st.button("Vaciar simulación"):
                    st.session_state.cirugias_anadidas = []
                    st.success("Simulación reiniciada.")
                    st.rerun()

            st.markdown("---")
            st.subheader("Cirugías simuladas")

            if st.session_state.cirugias_anadidas:
                sim = pd.DataFrame(st.session_state.cirugias_anadidas).copy()

                sim["inicio_dt"] = pd.to_datetime(sim["inicio_dt"]).dt.strftime("%Y-%m-%d %H:%M")
                sim["fin_dt"] = pd.to_datetime(sim["fin_dt"]).dt.strftime("%Y-%m-%d %H:%M")

                columnas_mostrar = [
                    "paciente",
                    "procedimiento_base",
                    "quirofano",
                    "inicio_dt",
                    "fin_dt",
                    "cirujano_principal",
                    "anestesista_principal",
                    "holgura_min",
                ]

                columnas_mostrar = [col for col in columnas_mostrar if col in sim.columns]
    with tab2:
        st.subheader("Procedimientos más frecuentes")
        proc = analisis_procedimientos(df_real)
        st.dataframe(proc.head(20), use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            top_proc = proc.head(10).copy()
            fig_proc = px.bar(
                top_proc,
                x="n_cirugias",
                y="procedimiento_base",
                orientation="h",
                title="Top 10 procedimientos por volumen",
            )
            fig_proc.update_layout(template="plotly_white", height=450, yaxis_title="")
            st.plotly_chart(fig_proc, use_container_width=True)

        with c2:
            uso = uso_quirofanos(df_real)
            fig_uso = px.bar(
                uso,
                x="quirofano",
                y="horas_ocupadas",
                title="Horas ocupadas por quirófano",
            )
            fig_uso.update_layout(template="plotly_white", height=450)
            st.plotly_chart(fig_uso, use_container_width=True)

        st.subheader("Tiempos muertos entre cirugías")
        gaps = tiempos_muertos(df_real)
        gaps_validos = gaps["tiempo_muerto_min"].notna() & (gaps["tiempo_muerto_min"] >= 0)
        st.metric("Tiempo muerto medio (min)", round(gaps.loc[gaps_validos, "tiempo_muerto_min"].mean(), 2))
        fig_gap = px.histogram(
            gaps.loc[gaps_validos],
            x="tiempo_muerto_min",
            nbins=30,
            title="Distribución de tiempos muertos",
        )
        fig_gap.update_layout(template="plotly_white", height=420)
        st.plotly_chart(fig_gap, use_container_width=True)

    with tab3:

    # ==============================
    # PANEL VISUAL DE OCUPACIÓN
    # ==============================

    st.subheader("Resumen visual de ocupación por quirófano")

    df_ocupacion = df_real.copy()

    df_ocupacion["fecha"] = pd.to_datetime(df_ocupacion["fecha"])
    df_ocupacion["mes"] = df_ocupacion["fecha"].dt.to_period("M").astype(str)

    # Horario planificable aproximado: 08:00-20:00 = 720 min
    MINUTOS_DIA = 720

    resumen_qx = (
        df_ocupacion
        .groupby("quirofano")
        .agg(
            cirugias=("procedimiento_base", "count"),
            minutos_ocupados=("duracion_min", "sum"),
            duracion_media=("duracion_min", "mean"),
            dias_activos=("fecha", "nunique"),
        )
        .reset_index()
    )

    with tab4:
        st.subheader("Exportar resultados")
        vista_exportacion = st.selectbox("Vista a exportar", ["Día actual", "Mes completo"])

        if vista_exportacion == "Día actual":
            agenda_export = agenda_combinada.copy()
            nombre_base = f"planificacion_diaria_{fecha_ts.strftime('%Y_%m_%d')}"
        else:
            agenda_export = df_real.copy()
            if st.session_state.cirugias_anadidas:
                extra = pd.DataFrame(st.session_state.cirugias_anadidas).copy()
                if not extra.empty:
                    extra["fecha"] = pd.to_datetime(extra["fecha"])
                    extra["inicio_dt"] = pd.to_datetime(extra["inicio"])
                    extra["fin_dt"] = pd.to_datetime(extra["fin_estimado"])
                    extra["duracion_min"] = (extra["fin_dt"] - extra["inicio_dt"]).dt.total_seconds() / 60
                    extra["procedimiento_base"] = extra["procedimiento"]
                    extra["fuente"] = "Propuesta añadida"
                    for col in agenda_export.columns:
                        if col not in extra.columns:
                            extra[col] = pd.NA
                    extra = extra[agenda_export.columns]
                    agenda_export = pd.concat([agenda_export, extra], ignore_index=True)
            nombre_base = "planificacion_mensual_febrero_2026"

        st.dataframe(agenda_export.head(30), use_container_width=True, hide_index=True)

        csv_bytes = agenda_export.to_csv(index=False).encode("utf-8-sig")
        xlsx_bytes = to_excel_bytes(agenda_export)

        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "Descargar CSV",
                data=csv_bytes,
                file_name=f"{nombre_base}.csv",
                mime="text/csv",
            )
        with d2:
            st.download_button(
                "Descargar Excel",
                data=xlsx_bytes,
                file_name=f"{nombre_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.info("Exportación para la planificación del equipo de quirofano")

    with tab5:
        st.subheader("Planificador anual de guardias de quirófano")

        col_g1, col_g2 = st.columns([0.7, 1.3])

        with col_g1:
            anio_guardias = st.number_input(
                "Año de planificación",
                min_value=2025,
                max_value=2035,
                value=2026,
                step=1,
            )

            personas_texto = st.text_area(
                "Miembros del equipo",
                value="\n".join(PERSONAS),
                height=260,
                help="Introduce un nombre por línea.",
            )

        with col_g2:
            festivos_texto = st.text_area(
                "Festivos",
                value="\n".join(sorted([f.strftime("%d/%m/%Y") for f in FESTIVOS])),
                height=260,
                help="Introduce un festivo por línea. Formato recomendado: dd/mm/aaaa.",
            )

        personas_guardias = [
            p.strip()
            for p in personas_texto.splitlines()
            if p.strip()
        ]

        festivos_guardias = parsear_festivos(festivos_texto)

        indisponibilidades_guardias = {
            persona: set()
            for persona in personas_guardias
        }

        if st.button("Generar planificación de guardias", type="primary"):
            try:
                asignaciones, stats = generar_planificacion(
                    anio=int(anio_guardias),
                    personas=personas_guardias,
                    festivos=festivos_guardias,
                    indisponibilidades=indisponibilidades_guardias,
                )

                df_plan_guardias = construir_dataframe_planificacion(
                    asignaciones,
                    festivos_guardias,
                )

                df_resumen_guardias = construir_dataframe_resumen(stats)

                st.session_state["df_plan_guardias"] = df_plan_guardias
                st.session_state["df_resumen_guardias"] = df_resumen_guardias
                st.session_state["excel_guardias"] = exportar_guardias_excel_bytes(
                    df_plan_guardias,
                    df_resumen_guardias,
                )

                st.success("Planificación de guardias generada correctamente.")

            except Exception as e:
                st.error(f"No se ha podido generar la planificación: {e}")

        if "df_plan_guardias" in st.session_state:
            df_plan_guardias = st.session_state["df_plan_guardias"]
            df_resumen_guardias = st.session_state["df_resumen_guardias"]

            st.markdown("---")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Días planificados", len(df_plan_guardias))
            c2.metric("Personas", len(personas_guardias))
            c3.metric("Guardias totales", len(df_plan_guardias) * 2)
            c4.metric("Festivos", df_plan_guardias["es_festivo"].eq("Sí").sum())

            meses_disponibles = sorted(pd.to_datetime(df_plan_guardias["fecha"]).dt.month.unique())

            mes_sel = st.selectbox(
                "Mes a visualizar",
                options=meses_disponibles,
                format_func=lambda m: {
                    1: "Enero",
                    2: "Febrero",
                    3: "Marzo",
                    4: "Abril",
                    5: "Mayo",
                    6: "Junio",
                    7: "Julio",
                    8: "Agosto",
                    9: "Septiembre",
                    10: "Octubre",
                    11: "Noviembre",
                    12: "Diciembre",
            }.get(m, str(m)),
            )

            df_mes = df_plan_guardias[
                pd.to_datetime(df_plan_guardias["fecha"]).dt.month == mes_sel
            ].copy()

            df_mes["fecha"] = pd.to_datetime(df_mes["fecha"]).dt.strftime("%d/%m/%Y")

            st.subheader("Visualizador mensual de guardias")

            st.dataframe(
                df_mes.style.apply(colorear_guardias, axis=1),
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Resumen por persona")

            st.dataframe(
                df_resumen_guardias,
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "Descargar planificación de guardias en Excel",
                data=st.session_state["excel_guardias"],
                file_name=f"planificacion_guardias_quirofano_{int(anio_guardias)}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        

# ----------------------------------------------------------
# RENDER DE VISUALIZACIÓN
# ----------------------------------------------------------


def render_agenda_visual(agenda: pd.DataFrame, fecha: pd.Timestamp, titulo: str):
    fecha = pd.to_datetime(fecha)
    inicio_jornada = pd.Timestamp(f"{fecha.strftime('%Y-%m-%d')} 07:00:00")
    fin_jornada = pd.Timestamp(f"{fecha.strftime('%Y-%m-%d')} 20:00:00")
    minutos_totales = int((fin_jornada - inicio_jornada).total_seconds() / 60)

    st.subheader(titulo)

    if agenda.empty:
        st.info("No hay cirugías registradas para este día.")
        return

    data = agenda.copy()
    data["inicio_dt"] = pd.to_datetime(data["inicio_dt"], errors="coerce")
    data["fin_dt"] = pd.to_datetime(data["fin_dt"], errors="coerce")
    data = data.dropna(subset=["quirofano", "inicio_dt", "fin_dt"]).copy()

    if "procedimiento_base" not in data.columns:
        data["procedimiento_base"] = data.get("procedimiento", "Sin nombre")

    for col in [
        "paciente",
        "cirujano_principal",
        "anestesista_principal",
        "servicio",
        "anestesia",
        "fuente",
    ]:
        if col not in data.columns:
            data[col] = ""

    quirofanos = sorted(data["quirofano"].astype(str).unique().tolist())

    # Escala visual
    px_por_minuto = 1.55
    ancho_tiempo = int(minutos_totales * px_por_minuto)
    ancho_label = 70
    altura_fila = 64

    # Cabecera horaria
    horas_html = ""
    for hora in range(7, 21):
        left = int((hora - 7) * 60 * px_por_minuto)
        horas_html += f"""
        <div class="hour-line" style="left:{left}px;"></div>
        <div class="hour-text" style="left:{left + 2}px;">{hora}:00</div>
        """

    filas_html = ""

    for q in quirofanos:
        agenda_q = data[data["quirofano"].astype(str) == q].sort_values("inicio_dt")
        bloques_html = ""

        for _, fila in agenda_q.iterrows():
            inicio = fila["inicio_dt"]
            fin = fila["fin_dt"]

            inicio_vis = max(inicio, inicio_jornada)
            fin_vis = min(fin, fin_jornada)

            if fin_vis <= inicio_jornada or inicio_vis >= fin_jornada:
                continue

            left_min = (inicio_vis - inicio_jornada).total_seconds() / 60
            width_min = (fin_vis - inicio_vis).total_seconds() / 60

            left_px = int(left_min * px_por_minuto)
            width_px = max(46, int(width_min * px_por_minuto))

            procedimiento = str(fila.get("procedimiento_base", "") or "Sin nombre")
            cirujano = str(fila.get("cirujano_principal", "") or "")
            anestesista = str(fila.get("anestesista_principal", "") or "")
            fuente = str(fila.get("fuente", "Histórico") or "Histórico")
            paciente = str(fila.get("paciente", "") or "")

            if width_px < 95:
                texto = f"{inicio.strftime('%H:%M')}"
            elif width_px < 150:
                texto = f"{procedimiento[:18]}<br>{inicio.strftime('%H:%M')}-{fin.strftime('%H:%M')}"
            else:
                texto = (
                    f"{procedimiento[:28]}<br>"
                    f"{inicio.strftime('%H:%M')}-{fin.strftime('%H:%M')}<br>"
                    f"{cirujano[:24]}"
                )

            clase = "block-propuesta" if fuente == "Propuesta añadida" else "block-historico"

            tooltip = (
                f"{procedimiento} | "
                f"{inicio.strftime('%H:%M')} - {fin.strftime('%H:%M')} | "
                f"Cirujano: {cirujano} | "
                f"Anestesista: {anestesista}"
            )

            bloques_html += f"""
            <div class="surgery-block {clase}"
                 style="left:{left_px}px; width:{width_px}px;"
                 title="{tooltip}">
                {texto}
            </div>
            """

        filas_html += f"""
        <div class="row-wrap">
            <div class="row-label">{q}</div>
            <div class="row-track">
                {bloques_html}
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: #ffffff;
        }}

        .scheduler {{
            width: 100%;
            overflow-x: auto;
            border: 1px solid #d7d7d7;
            border-radius: 8px;
            background: #ececec;
            padding: 12px;
            box-sizing: border-box;
        }}

        .inner {{
            min-width: {ancho_label + ancho_tiempo + 30}px;
        }}

        .header {{
            display: flex;
            margin-bottom: 8px;
        }}

        .header-left {{
            width: {ancho_label}px;
            min-width: {ancho_label}px;
        }}

        .header-time {{
            position: relative;
            width: {ancho_tiempo}px;
            min-width: {ancho_tiempo}px;
            height: 28px;
            background: #cfcfcf;
            border-radius: 4px;
        }}

        .hour-line {{
            position: absolute;
            top: 0;
            width: 1px;
            height: 100%;
            background: #8f8f8f;
        }}

        .hour-text {{
            position: absolute;
            top: 3px;
            font-size: 11px;
            color: #333;
        }}

        .row-wrap {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}

        .row-label {{
            width: {ancho_label}px;
            min-width: {ancho_label}px;
            text-align: center;
            font-weight: 700;
            font-size: 14px;
            color: #222;
        }}

        .row-track {{
            position: relative;
            width: {ancho_tiempo}px;
            min-width: {ancho_tiempo}px;
            height: {altura_fila}px;
            background:
                repeating-linear-gradient(
                    to right,
                    #bdbdbd 0px,
                    #bdbdbd 1px,
                    transparent 1px,
                    transparent {int(px_por_minuto * 60)}px
                ),
                #d9d9d9;
            border-radius: 3px;
            overflow: hidden;
        }}

        .surgery-block {{
            position: absolute;
            top: 10px;
            height: 42px;
            border: 1px solid rgba(0,0,0,0.25);
            box-sizing: border-box;
            padding: 3px 5px;
            font-size: 10px;
            line-height: 1.15;
            color: #111;
            overflow: hidden;
            white-space: normal;
        }}

        .block-historico {{
            background: #f6b100;
        }}

        .block-propuesta {{
            background: #7CFC00;
        }}
    </style>
    </head>
    <body>
        <div class="scheduler">
            <div class="inner">
                <div class="header">
                    <div class="header-left"></div>
                    <div class="header-time">
                        {horas_html}
                    </div>
                </div>

                {filas_html}
            </div>
        </div>
    </body>
    </html>
    """

    alto = 120 + len(quirofanos) * (altura_fila + 8)
    components.html(html, height=max(220, alto), scrolling=True)


if __name__ == "__main__":
    main()
