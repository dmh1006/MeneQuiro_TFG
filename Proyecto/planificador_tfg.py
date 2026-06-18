from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "quirofano_2025_limpio.csv"


# ==========================================================
# CARGA Y PREPARACIÓN
# ==========================================================

from pathlib import Path
import pandas as pd


def cargar_datos():
    """
    Carga el dataset limpio de quirófano buscando el CSV en varias rutas posibles.
    """
    base_dir = Path(__file__).resolve().parent
    root_dir = base_dir.parent

    rutas_posibles = [
        base_dir / "quirofano_2025_limpio.csv",
        root_dir / "quirofano_2025_limpio.csv",
        base_dir / "Data" / "quirofano_2025_limpio.csv",
        root_dir / "Data" / "quirofano_2025_limpio.csv",
        root_dir / "Proyecto" / "quirofano_2025_limpio.csv",
    ]

    data_path = None
    for ruta in rutas_posibles:
        if ruta.exists():
            data_path = ruta
            break

    if data_path is None:
        raise FileNotFoundError(
            "No se encontró 'quirofano_febrero_limpio.csv'. "
            f"Rutas revisadas: {[str(r) for r in rutas_posibles]}"
        )

    df = pd.read_csv(data_path, parse_dates=["fecha", "inicio_dt", "fin_dt"])
    return df


def filtrar_cirugias_reales(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina cirugías suspendidas y registros sin tiempos válidos."""
    salida = df.loc[
        (~df["esta_suspendida"].fillna(False))
        & df["inicio_dt"].notna()
        & df["fin_dt"].notna()
    ].copy()

    salida = salida[salida["duracion_min"].fillna(0) > 0].copy()
    return salida


def normalizar_procedimiento(texto: str) -> str:
    if pd.isna(texto):
        return "DESCONOCIDO"

    texto = str(texto).strip().upper()

    reemplazos = {
        "APENDICECTOMIA POR LAPAROSCOPIA": "APENDICECTOMIA LAPAROSCOPICA",
        "RESECCION DE VESICULA BILIAR, ABORDAJE ENDOSCOPICO PERCUTA": "COLECISTECTOMIA LAPAROSCOPICA",
        "SUPLEMENTO EN REGION INGUINAL, DERECHA, CON SUSTITUTO SINT": "HERNIA INGUINAL DERECHA",
        "SUPLEMENTO EN REGION INGUINAL, IZQUIERDA, CON SUSTITUTO SI": "HERNIA INGUINAL IZQUIERDA",
        "SUPLEMENTO EN REGION INGUINAL, BILATERAL, CON SUSTITUTO S": "HERNIA INGUINAL BILATERAL",
    }

    return reemplazos.get(texto, texto)


def preparar_dataset_funcional(df: pd.DataFrame) -> pd.DataFrame:
    df_real = filtrar_cirugias_reales(df)
    df_real["procedimiento_base"] = df_real["procedimiento"].apply(normalizar_procedimiento)
    df_real["fecha_str"] = df_real["fecha"].dt.strftime("%Y-%m-%d")
    df_real["mes"] = df_real["fecha"].dt.to_period("M").astype(str)
    return df_real


# ==========================================================
# MÉTRICAS Y ANÁLISIS
# ==========================================================

def resumen_general(df_real: pd.DataFrame) -> dict:
    """Devuelve KPIs resumidos del bloque quirúrgico."""
    tiempo_total_horas = df_real["duracion_min"].sum() / 60
    duracion_media = df_real["duracion_min"].mean()
    urgencias = int(df_real["es_urgencia"].fillna(False).sum())

    return {
        "n_cirugias": int(len(df_real)),
        "n_quirofanos": int(df_real["quirofano"].nunique()),
        "n_servicios": int(df_real["servicio"].nunique()),
        "tiempo_total_horas": round(float(tiempo_total_horas), 2),
        "duracion_media_min": round(float(duracion_media), 2),
        "pct_urgencias": round(100 * urgencias / max(len(df_real), 1), 2),
    }


def analisis_procedimientos(df_real: pd.DataFrame) -> pd.DataFrame:
    return (
        df_real.groupby("procedimiento_base")
        .agg(
            n_cirugias=("procedimiento_base", "count"),
            duracion_media=("duracion_min", "mean"),
            duracion_mediana=("duracion_min", "median"),
            desviacion=("duracion_min", "std"),
            pct_urgencias=("es_urgencia", lambda x: 100 * x.fillna(False).mean()),
        )
        .sort_values(["n_cirugias", "duracion_mediana"], ascending=[False, True])
        .round(2)
        .reset_index()
    )


def uso_quirofanos(df_real: pd.DataFrame) -> pd.DataFrame:
    return (
        df_real.groupby("quirofano")
        .agg(
            n_cirugias=("quirofano", "count"),
            horas_ocupadas=("duracion_min", lambda x: x.sum() / 60),
            duracion_media_min=("duracion_min", "mean"),
        )
        .sort_values("n_cirugias", ascending=False)
        .round(2)
        .reset_index()
    )


def tiempos_muertos(df_real: pd.DataFrame) -> pd.DataFrame:
    df_gap = df_real.sort_values(["fecha", "quirofano", "inicio_dt"]).copy()
    df_gap["fin_anterior"] = df_gap.groupby(["fecha", "quirofano"])["fin_dt"].shift(1)
    df_gap["tiempo_muerto_min"] = (
        df_gap["inicio_dt"] - df_gap["fin_anterior"]
    ).dt.total_seconds() / 60
    return df_gap


def ocupacion_por_dia_quirofano(
    df_real: pd.DataFrame,
    hora_inicio_bloque: str = "08:00",
    hora_fin_bloque: str = "20:00",
) -> pd.DataFrame:
    """Calcula ocupación diaria por quirófano frente a un bloque teórico."""
    ini_h, ini_m = map(int, hora_inicio_bloque.split(":"))
    fin_h, fin_m = map(int, hora_fin_bloque.split(":"))
    minutos_bloque = (fin_h * 60 + fin_m) - (ini_h * 60 + ini_m)

    ocup = (
        df_real.groupby(["fecha", "quirofano"])
        .agg(min_ocupados=("duracion_min", "sum"), n_cirugias=("quirofano", "count"))
        .reset_index()
    )
    ocup["min_bloque"] = minutos_bloque
    ocup["ocupacion_pct"] = (100 * ocup["min_ocupados"] / minutos_bloque).round(2)
    ocup["fecha_str"] = ocup["fecha"].dt.strftime("%Y-%m-%d")
    return ocup.sort_values(["fecha", "quirofano"]).reset_index(drop=True)


# ==========================================================
# CATÁLOGO QUIRÚRGICO
# ==========================================================

def construir_catalogo_quirurgico(df_real: pd.DataFrame) -> pd.DataFrame:
    """
    Genera un catálogo operativo con estimación de tiempo planificable.
    La duración planificable se basa en mediana + preparación + post + buffer.
    """
    catalogo = (
        df_real.groupby("procedimiento_base")
        .agg(
            n_casos=("procedimiento_base", "count"),
            duracion_media_min=("duracion_min", "mean"),
            duracion_mediana_min=("duracion_min", "median"),
            p75_min=("duracion_min", lambda x: np.percentile(x, 75)),
            desviacion_min=("duracion_min", "std"),
            pct_urgencias=("es_urgencia", lambda x: 100 * x.fillna(False).mean()),
            quirofanos_habituales=("quirofano", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))),
        )
        .round(2)
        .reset_index()
        .sort_values("n_casos", ascending=False)
    )

    catalogo["prep_min"] = 15
    catalogo["post_min"] = 10
    catalogo["buffer_variabilidad_min"] = (catalogo["desviacion_min"].fillna(0) * 0.5).round(0)
    catalogo["duracion_planificable_min"] = (
        catalogo["duracion_mediana_min"].fillna(0)
        + catalogo["prep_min"]
        + catalogo["post_min"]
        + catalogo["buffer_variabilidad_min"]
    ).round(0)

    return catalogo.reset_index(drop=True)


def obtener_ficha_procedimiento(catalogo: pd.DataFrame, procedimiento: str) -> pd.Series:
    proc_norm = normalizar_procedimiento(procedimiento)
    fila = catalogo[catalogo["procedimiento_base"] == proc_norm]
    if fila.empty:
        raise ValueError(f"No se encontró el procedimiento: {procedimiento}")
    return fila.iloc[0]


def estimar_nueva_cirugia(catalogo: pd.DataFrame, procedimiento: str) -> dict:
    ficha = obtener_ficha_procedimiento(catalogo, procedimiento)
    return {
        "procedimiento": ficha["procedimiento_base"],
        "n_casos_historicos": int(ficha["n_casos"]),
        "duracion_mediana_min": float(ficha["duracion_mediana_min"]),
        "duracion_media_min": float(ficha["duracion_media_min"]),
        "p75_min": float(ficha["p75_min"]),
        "prep_min": float(ficha["prep_min"]),
        "post_min": float(ficha["post_min"]),
        "buffer_variabilidad_min": float(ficha["buffer_variabilidad_min"]),
        "duracion_planificable_min": float(ficha["duracion_planificable_min"]),
        "quirofanos_habituales": ficha["quirofanos_habituales"],
        "pct_urgencias": float(ficha["pct_urgencias"]),
    }


# ==========================================================
# PLANIFICACIÓN DIARIA
# ==========================================================

def agenda_dia(df_real: pd.DataFrame, fecha: str | pd.Timestamp) -> pd.DataFrame:
    fecha = pd.to_datetime(fecha).normalize()
    df_real = df_real.copy()
    df_real["fecha"] = pd.to_datetime(df_real["fecha"], errors="coerce")
    df_real["inicio_dt"] = pd.to_datetime(df_real["inicio_dt"], errors="coerce")
    df_real["fin_dt"] = pd.to_datetime(df_real["fin_dt"], errors="coerce")

    fecha = pd.to_datetime(fecha).normalize()

    agenda = (
        df_real[df_real["fecha"].dt.normalize() == fecha]
        .sort_values(["quirofano", "inicio_dt"])
        .copy()
    )
    return agenda


def calcular_huecos_quirofano(
    agenda_qx: pd.DataFrame,
    fecha: str | pd.Timestamp,
    hora_inicio_bloque: str = "08:00",
    hora_fin_bloque: str = "20:00",
) -> list[dict]:
    fecha = pd.to_datetime(fecha).strftime("%Y-%m-%d")
    inicio_bloque = pd.Timestamp(f"{fecha} {hora_inicio_bloque}")
    fin_bloque = pd.Timestamp(f"{fecha} {hora_fin_bloque}")
    agenda_qx = agenda_qx.sort_values("inicio_dt").copy()

    huecos: list[dict] = []

    if agenda_qx.empty:
        return [{
            "inicio_hueco": inicio_bloque,
            "fin_hueco": fin_bloque,
            "duracion_hueco_min": (fin_bloque - inicio_bloque).total_seconds() / 60,
        }]

    primera_inicio = agenda_qx.iloc[0]["inicio_dt"]
    gap_inicial = (primera_inicio - inicio_bloque).total_seconds() / 60
    if gap_inicial > 0:
        huecos.append({
            "inicio_hueco": inicio_bloque,
            "fin_hueco": primera_inicio,
            "duracion_hueco_min": gap_inicial,
        })

    for i in range(len(agenda_qx) - 1):
        fin_actual = agenda_qx.iloc[i]["fin_dt"]
        inicio_siguiente = agenda_qx.iloc[i + 1]["inicio_dt"]
        gap = (inicio_siguiente - fin_actual).total_seconds() / 60
        if gap > 0:
            huecos.append({
                "inicio_hueco": fin_actual,
                "fin_hueco": inicio_siguiente,
                "duracion_hueco_min": gap,
            })

    ultimo_fin = agenda_qx.iloc[-1]["fin_dt"]
    gap_final = (fin_bloque - ultimo_fin).total_seconds() / 60
    if gap_final > 0:
        huecos.append({
            "inicio_hueco": ultimo_fin,
            "fin_hueco": fin_bloque,
            "duracion_hueco_min": gap_final,
        })

    return huecos


def proponer_huecos(
    df_real: pd.DataFrame,
    catalogo: pd.DataFrame,
    procedimiento: str,
    fecha: str | pd.Timestamp,
    hora_inicio_bloque: str = "08:00",
    hora_fin_bloque: str = "20:00",
    quirofanos_validos: Iterable[str] | None = None,
    max_resultados: int = 5,
) -> pd.DataFrame:
    """Devuelve huecos candidatos ordenados de mejor a peor."""
    ficha = estimar_nueva_cirugia(catalogo, procedimiento)
    duracion_necesaria = ficha["duracion_planificable_min"]

    agenda = agenda_dia(df_real, fecha).copy()
    if quirofanos_validos is not None:
        quirofanos_validos = list(quirofanos_validos)
        agenda = agenda[agenda["quirofano"].isin(quirofanos_validos)].copy()

    preferidos = [q.strip() for q in str(ficha["quirofanos_habituales"]).split(",") if q.strip()]

    universo = sorted(df_real["quirofano"].dropna().astype(str).unique())
    if quirofanos_validos is not None:
        universo = [q for q in universo if q in quirofanos_validos]

    candidatos: list[dict] = []
    for qx in universo:
        agenda_qx = agenda[agenda["quirofano"] == qx].copy()
        huecos = calcular_huecos_quirofano(
            agenda_qx=agenda_qx,
            fecha=fecha,
            hora_inicio_bloque=hora_inicio_bloque,
            hora_fin_bloque=hora_fin_bloque,
        )

        for h in huecos:
            if h["duracion_hueco_min"] >= duracion_necesaria:
                score = 0
                score += 100 if qx in preferidos else 0
                score -= abs(h["duracion_hueco_min"] - duracion_necesaria)
                score -= (h["inicio_hueco"].hour * 60 + h["inicio_hueco"].minute) / 1000

                candidatos.append({
                    "procedimiento": ficha["procedimiento"],
                    "quirofano": qx,
                    "inicio": h["inicio_hueco"],
                    "fin_estimado": h["inicio_hueco"] + pd.Timedelta(minutes=duracion_necesaria),
                    "duracion_necesaria": duracion_necesaria,
                    "duracion_disponible": h["duracion_hueco_min"],
                    "holgura_min": h["duracion_hueco_min"] - duracion_necesaria,
                    "es_quirofano_habitual": qx in preferidos,
                    "score": round(score, 3),
                })

    if not candidatos:
        return pd.DataFrame()

    candidatos_df = pd.DataFrame(candidatos).sort_values(
        by=["es_quirofano_habitual", "holgura_min", "inicio"],
        ascending=[False, True, True],
    )

    return candidatos_df.head(max_resultados).reset_index(drop=True)


def obtener_agenda_combinada(df_real, fecha_sel, cirugias_anadidas):
    """
    Combina la agenda histórica del día con las cirugías simuladas añadidas
    por el usuario, dejando una estructura homogénea para representar y analizar.
    Revision

    Parámetros
    ----------
    df_real : pd.DataFrame
        Dataset histórico de cirugías.
    fecha_sel : str o pd.Timestamp
        Fecha seleccionada.
    cirugias_anadidas : list[dict]
        Lista de cirugías simuladas añadidas en la sesión.

    Retornos
    --------
    pd.DataFrame
        Agenda combinada del día con columnas homogéneas.
    """
    fecha_ts = pd.to_datetime(fecha_sel).normalize()

    # -----------------------------
    # AGENDA HISTÓRICA
    # -----------------------------
    agenda_real = df_real.copy()

    agenda_real["fecha"] = pd.to_datetime(agenda_real["fecha"]).dt.normalize()
    agenda_real = agenda_real[agenda_real["fecha"] == fecha_ts].copy()

    if "inicio_dt" in agenda_real.columns:
        agenda_real["inicio_dt"] = pd.to_datetime(agenda_real["inicio_dt"])
    elif "inicio" in agenda_real.columns:
        agenda_real["inicio_dt"] = pd.to_datetime(agenda_real["inicio"])
    else:
        agenda_real["inicio_dt"] = pd.NaT

    if "fin_dt" in agenda_real.columns:
        agenda_real["fin_dt"] = pd.to_datetime(agenda_real["fin_dt"])
    elif "fin_estimado" in agenda_real.columns:
        agenda_real["fin_dt"] = pd.to_datetime(agenda_real["fin_estimado"])
    elif "fin" in agenda_real.columns:
        agenda_real["fin_dt"] = pd.to_datetime(agenda_real["fin"])
    else:
        agenda_real["fin_dt"] = pd.NaT

    if "procedimiento_base" not in agenda_real.columns:
        if "procedimiento" in agenda_real.columns:
            agenda_real["procedimiento_base"] = agenda_real["procedimiento"]
        else:
            agenda_real["procedimiento_base"] = "Sin nombre"

    if "duracion_min" not in agenda_real.columns:
        agenda_real["duracion_min"] = (
            (agenda_real["fin_dt"] - agenda_real["inicio_dt"]).dt.total_seconds() / 60
        )

    agenda_real["fuente"] = "Histórico"

    columnas_base = [
        "fecha",
        "quirofano",
        "inicio_dt",
        "fin_dt",
        "procedimiento_base",
        "duracion_min",
        "fuente",
        "holgura_min",
        "es_quirofano_habitual",
        "paciente",
        "cirujano_principal",
        "anestesista_principal",
        "servicio",
        "tipo_caso",
        "anestesia",
    ]

    for col in columnas_base:
        if col not in agenda_real.columns:
            agenda_real[col] = None

    agenda_real = agenda_real[columnas_base].copy()

    # -----------------------------
    # AGENDA SIMULADA
    # -----------------------------
    if cirugias_anadidas:
        agenda_sim = pd.DataFrame(cirugias_anadidas).copy()
    else:
        agenda_sim = pd.DataFrame(columns=columnas_base)

    for col in columnas_base:
        if col not in agenda_sim.columns:
            agenda_sim[col] = None

    if not agenda_sim.empty:
        agenda_sim["fecha"] = pd.to_datetime(agenda_sim["fecha"]).dt.normalize()
        agenda_sim["inicio_dt"] = pd.to_datetime(agenda_sim["inicio_dt"])
        agenda_sim["fin_dt"] = pd.to_datetime(agenda_sim["fin_dt"])

        agenda_sim = agenda_sim[agenda_sim["fecha"] == fecha_ts].copy()

    agenda_sim = agenda_sim[columnas_base].copy()

    # -----------------------------
    # UNIÓN FINAL
    # -----------------------------
    agenda = pd.concat([agenda_real, agenda_sim], ignore_index=True)

    agenda["inicio_dt"] = pd.to_datetime(agenda["inicio_dt"], errors="coerce")
    agenda["fin_dt"] = pd.to_datetime(agenda["fin_dt"], errors="coerce")

    agenda = agenda.dropna(subset=["quirofano", "inicio_dt", "fin_dt"])
    agenda = agenda.sort_values(["quirofano", "inicio_dt"]).reset_index(drop=True)

    return agenda

def hay_solape_en_quirofano(
    agenda: pd.DataFrame,
    quirofano: str,
    inicio_nuevo: pd.Timestamp,
    fin_nuevo: pd.Timestamp,
) -> bool:
    """
    Comprueba si una nueva cirugía se solapa con alguna ya existente
    en el mismo quirófano.
    """
    if agenda.empty:
        return False

    agenda_q = agenda[agenda["quirofano"].astype(str) == str(quirofano)].copy()

    if agenda_q.empty:
        return False

    agenda_q["inicio_dt"] = pd.to_datetime(agenda_q["inicio_dt"])
    agenda_q["fin_dt"] = pd.to_datetime(agenda_q["fin_dt"])

    for _, fila in agenda_q.iterrows():
        inicio_existente = fila["inicio_dt"]
        fin_existente = fila["fin_dt"]

        # Hay solape si el nuevo empieza antes de que termine el existente
        # y termina después de que empiece el existente.
        if inicio_nuevo < fin_existente and fin_nuevo > inicio_existente:
            return True

    return False

# ==========================================================
# EXPORTACIÓN
# ==========================================================

def exportar_agenda_csv(df_agenda: pd.DataFrame, ruta_salida: Path | str) -> Path:
    ruta_salida = Path(ruta_salida)
    df_agenda.to_csv(ruta_salida, index=False)
    return ruta_salida


if __name__ == "__main__":
    df = cargar_datos()
    df_real = preparar_dataset_funcional(df)
    catalogo = construir_catalogo_quirurgico(df_real)

    print("=== RESUMEN GENERAL ===")
    print(resumen_general(df_real))
    print("\n=== EJEMPLO DE PROPUESTA ===")
    ejemplo = proponer_huecos(df_real, catalogo, "APENDICECTOMIA LAPAROSCOPICA", "2026-02-02")
    print(ejemplo.head().to_string(index=False))
