from pathlib import Path
import pandas as pd
from typing import Optional, List

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "Data" / "quirofano_2025_limpio.csv"


def cargar_datos() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["fecha", "inicio_dt", "fin_dt"])
    return df


def filtrar_cirugias_reales(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df["esta_suspendida"]].copy()


def analisis_procedimientos(df_real: pd.DataFrame) -> pd.DataFrame:
    stats = (
        df_real.groupby("procedimiento")
        .agg(
            n_cirugias=("procedimiento", "count"),
            duracion_media=("duracion_min", "mean"),
            duracion_mediana=("duracion_min", "median"),
            desviacion=("duracion_min", "std")
        )
        .sort_values("n_cirugias", ascending=False)
        .round(2)
    )

    print("\n=== TOP PROCEDIMIENTOS ===")
    print(stats.head(15).to_string())

    return stats


def uso_quirofanos(df_real: pd.DataFrame) -> pd.Series:
    uso = df_real["quirofano"].value_counts()

    print("\n=== USO DE QUIROFANOS ===")
    print(uso.to_string())

    return uso


def tiempos_muertos(df_real: pd.DataFrame) -> pd.DataFrame:
    df_gap = df_real.sort_values(["quirofano", "fecha", "inicio_dt"]).copy()

    df_gap["fin_anterior"] = df_gap.groupby(["quirofano", "fecha"])["fin_dt"].shift(1)

    df_gap["tiempo_muerto"] = (
        df_gap["inicio_dt"] - df_gap["fin_anterior"]
    ).dt.total_seconds() / 60

    tiempo_medio = df_gap["tiempo_muerto"].dropna().mean()

    print("\n=== TIEMPO MUERTO MEDIO ENTRE CIRUGIAS (MISMO DIA) ===")
    print(round(tiempo_medio, 2), "min")

    return df_gap


def normalizar_procedimiento(texto: str) -> str:
    if pd.isna(texto):
        return "DESCONOCIDO"

    texto = str(texto).strip().upper()

    reemplazos = {
        "APENDICECTOMIA POR LAPAROSCOPIA": "APENDICECTOMIA LAPAROSCOPICA",
        "APENDICECTOMIA LAPAROSCOPICA": "APENDICECTOMIA LAPAROSCOPICA",
        "RESECCION DE VESICULA BILIAR, ABORDAJE ENDOSCOPICO PERCUTA": "COLECISTECTOMIA LAPAROSCOPICA",
        "SUPLEMENTO EN REGION INGUINAL, DERECHA, CON SUSTITUTO SINT": "HERNIA INGUINAL DERECHA",
        "SUPLEMENTO EN REGION INGUINAL, IZQUIERDA, CON SUSTITUTO SI": "HERNIA INGUINAL IZQUIERDA",
        "SUPLEMENTO EN REGION INGUINAL, BILATERAL, CON SUSTITUTO S": "HERNIA INGUINAL BILATERAL",
    }

    return reemplazos.get(texto, texto)


def preparar_dataset_funcional(df: pd.DataFrame) -> pd.DataFrame:
    df_real = filtrar_cirugias_reales(df)
    df_real["procedimiento_base"] = df_real["procedimiento"].apply(normalizar_procedimiento)
    return df_real


def construir_catalogo_quirurgico(df_real: pd.DataFrame) -> pd.DataFrame:
    catalogo = (
        df_real.groupby("procedimiento_base")
        .agg(
            n_casos=("procedimiento_base", "count"),
            duracion_media_min=("duracion_min", "mean"),
            duracion_mediana_min=("duracion_min", "median"),
            desviacion_min=("duracion_min", "std"),
            quirofanos_habituales=("quirofano", lambda x: ", ".join(sorted(set(x.astype(str)))))
        )
        .sort_values("n_casos", ascending=False)
        .round(2)
        .reset_index()
    )

    # Estimación operativa simple
    catalogo["prep_min"] = 15
    catalogo["post_min"] = 10
    catalogo["buffer_variabilidad_min"] = (
        catalogo["desviacion_min"].fillna(0) * 0.5
    ).round(0)

    catalogo["duracion_planificable_min"] = (
        catalogo["duracion_mediana_min"].fillna(0)
        + catalogo["prep_min"]
        + catalogo["post_min"]
        + catalogo["buffer_variabilidad_min"]
    ).round(0)

    return catalogo


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
        "prep_min": float(ficha["prep_min"]),
        "post_min": float(ficha["post_min"]),
        "buffer_variabilidad_min": float(ficha["buffer_variabilidad_min"]),
        "duracion_planificable_min": float(ficha["duracion_planificable_min"]),
        "quirofanos_habituales": ficha["quirofanos_habituales"],
    }



def agenda_dia(df_real: pd.DataFrame, fecha: str) -> pd.DataFrame:

    fecha = pd.to_datetime(fecha)

    agenda = (
        df_real[df_real["fecha"] == fecha]
        .sort_values(["quirofano", "inicio_dt"])
        .copy()
    )

    return agenda


def calcular_huecos_quirofano(
    agenda_qx: pd.DataFrame,
    fecha: str,
    hora_inicio_bloque: str = "08:00",
    hora_fin_bloque: str = "20:00"
) -> list:
    """
    Calcula los huecos disponibles de un quirófano en un día concreto,
    incluyendo hueco inicial, intermedios y final del bloque.
    """
    fecha = pd.to_datetime(fecha).strftime("%Y-%m-%d")

    inicio_bloque = pd.Timestamp(f"{fecha} {hora_inicio_bloque}")
    fin_bloque = pd.Timestamp(f"{fecha} {hora_fin_bloque}")

    agenda_qx = agenda_qx.sort_values("inicio_dt").copy()

    huecos = []

    # Si no hay ninguna cirugía en ese quirófano, todo el bloque está libre
    if agenda_qx.empty:
        huecos.append({
            "inicio_hueco": inicio_bloque,
            "fin_hueco": fin_bloque,
            "duracion_hueco_min": (fin_bloque - inicio_bloque).total_seconds() / 60
        })
        return huecos

    # Hueco antes de la primera cirugía
    primera_inicio = agenda_qx.iloc[0]["inicio_dt"]
    gap_inicial = (primera_inicio - inicio_bloque).total_seconds() / 60

    if gap_inicial > 0:
        huecos.append({
            "inicio_hueco": inicio_bloque,
            "fin_hueco": primera_inicio,
            "duracion_hueco_min": gap_inicial
        })

    # Huecos entre cirugías
    for i in range(len(agenda_qx) - 1):
        fin_actual = agenda_qx.iloc[i]["fin_dt"]
        inicio_siguiente = agenda_qx.iloc[i + 1]["inicio_dt"]

        gap = (inicio_siguiente - fin_actual).total_seconds() / 60

        if gap > 0:
            huecos.append({
                "inicio_hueco": fin_actual,
                "fin_hueco": inicio_siguiente,
                "duracion_hueco_min": gap
            })

    # Hueco después de la última cirugía
    ultimo_fin = agenda_qx.iloc[-1]["fin_dt"]
    gap_final = (fin_bloque - ultimo_fin).total_seconds() / 60

    if gap_final > 0:
        huecos.append({
            "inicio_hueco": ultimo_fin,
            "fin_hueco": fin_bloque,
            "duracion_hueco_min": gap_final
        })

    return huecos


def proponer_huecos(
    df_real,
    catalogo,
    procedimiento,
    fecha,
    hora_inicio_bloque="08:00",
    hora_fin_bloque="20:00",
    quirofanos_validos=None,
    max_resultados=5
):
    """
    Devuelve varios huecos candidatos ordenados de mejor a peor.
    """
    ficha = estimar_nueva_cirugia(catalogo, procedimiento)
    duracion_necesaria = ficha["duracion_planificable_min"]

    agenda = agenda_dia(df_real, fecha).copy()

    if quirofanos_validos is not None:
        agenda = agenda[agenda["quirofano"].isin(quirofanos_validos)].copy()

    quirofanos_preferidos = [
        q.strip() for q in str(ficha["quirofanos_habituales"]).split(",")
        if q.strip()
    ]

    if agenda.empty:
        if quirofanos_validos is not None:
            quirofanos_a_explorar = quirofanos_validos
        else:
            quirofanos_a_explorar = quirofanos_preferidos
    else:
        quirofanos_a_explorar = sorted(agenda["quirofano"].dropna().astype(str).unique())

        for q in quirofanos_preferidos:
            if q not in quirofanos_a_explorar:
                quirofanos_a_explorar.append(q)

        if quirofanos_validos is not None:
            quirofanos_a_explorar = [q for q in quirofanos_a_explorar if q in quirofanos_validos]

    candidatos = []

    for qx in quirofanos_a_explorar:
        agenda_qx = agenda[agenda["quirofano"] == qx].copy()

        huecos = calcular_huecos_quirofano(
            agenda_qx=agenda_qx,
            fecha=fecha,
            hora_inicio_bloque=hora_inicio_bloque,
            hora_fin_bloque=hora_fin_bloque
        )

        for h in huecos:
            if h["duracion_hueco_min"] >= duracion_necesaria:
                candidatos.append({
                    "procedimiento": ficha["procedimiento"],
                    "quirofano": qx,
                    "inicio": h["inicio_hueco"],
                    "fin_estimado": h["inicio_hueco"] + pd.Timedelta(minutes=duracion_necesaria),
                    "duracion_necesaria": duracion_necesaria,
                    "duracion_disponible": h["duracion_hueco_min"],
                    "holgura_min": h["duracion_hueco_min"] - duracion_necesaria,
                    "es_quirofano_habitual": qx in quirofanos_preferidos
                })

    if len(candidatos) == 0:
        return pd.DataFrame()

    candidatos_df = pd.DataFrame(candidatos)

    candidatos_df = candidatos_df.sort_values(
        by=["es_quirofano_habitual", "holgura_min", "inicio"],
        ascending=[False, True, True]
    )

    return candidatos_df.head(max_resultados).reset_index(drop=True)

if __name__ == "__main__":
    main()