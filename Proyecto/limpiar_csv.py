from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_EXCEL = BASE_DIR / "Data" / "2025.xls"
RUTA_SALIDA_CSV = BASE_DIR / "Data" / "quirofano_febrero_limpio.csv"


def cargar_y_limpiar(ruta_excel: Path) -> pd.DataFrame:
    """
    Carga el Excel bruto del quirófano y devuelve un DataFrame limpio
    con las columnas útiles para el proyecto de planificación.
    """
    bruto = pd.read_excel(ruta_excel, header=None, engine="xlrd")

    columnas_utiles = [
        0,   # paciente_id
        4,   # servicio
        5,   # quirofano
        7,   # centro
        12,  # fecha
        13,  # hora_inicio
        16,  # hora_fin
        18,  # anestesia
        21,  # ambulatorio
        22,  # tipo_caso
        26,  # turno
        27,  # progr
        28,  # impl
        29,  # dx_codigo
        30,  # diagnostico
        31,  # proc_codigo
        32,  # procedimiento
        33,  # cirujano_principal
        34,  # anestesista_principal
        35,  # suspendida
        36,  # motivo_suspension
        37,  # provincia
        38,  # sector
    ]

    df = bruto.iloc[11:, columnas_utiles].copy()

    df.columns = [
        "paciente_id",
        "servicio",
        "quirofano",
        "centro",
        "fecha",
        "hora_inicio",
        "hora_fin",
        "anestesia",
        "ambulatorio",
        "tipo_caso",
        "turno",
        "progr",
        "impl",
        "dx_codigo",
        "diagnostico",
        "proc_codigo",
        "procedimiento",
        "cirujano_principal",
        "anestesista_principal",
        "suspendida",
        "motivo_suspension",
        "provincia",
        "sector",
    ]

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .replace({"nan": np.nan, "None": np.nan, "": np.nan})
            )

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    df["inicio_dt"] = pd.to_datetime(
        df["fecha"].dt.strftime("%Y-%m-%d") + " " + df["hora_inicio"].astype(str),
        errors="coerce"
    )

    df["fin_dt"] = pd.to_datetime(
        df["fecha"].dt.strftime("%Y-%m-%d") + " " + df["hora_fin"].astype(str),
        errors="coerce"
    )

    cruza_medianoche = df["fin_dt"] < df["inicio_dt"]
    df.loc[cruza_medianoche, "fin_dt"] = df.loc[cruza_medianoche, "fin_dt"] + pd.Timedelta(days=1)

    df["duracion_min"] = (df["fin_dt"] - df["inicio_dt"]).dt.total_seconds() / 60
    df["duracion_horas"] = df["duracion_min"] / 60
    df["es_urgencia"] = df["tipo_caso"].eq("U")
    df["esta_suspendida"] = df["suspendida"].eq("S")

    return df


def main():
    print("=== COMPROBACIÓN DE RUTAS ===")
    print(f"Base del proyecto: {BASE_DIR}")
    print(f"Excel encontrado: {RUTA_EXCEL.exists()}")
    print(f"Ruta Excel: {RUTA_EXCEL}")

    if not RUTA_EXCEL.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo Excel en: {RUTA_EXCEL}\n"
            "Mueve el archivo a la carpeta Data/ y vuelve a ejecutar."
        )

    df = cargar_y_limpiar(RUTA_EXCEL)

    print("\n=== RESUMEN INICIAL ===")
    print(f"Filas totales: {len(df)}")
    print(f"Quirófanos detectados: {df['quirofano'].nunique()}")
    print(f"Suspendidas: {df['esta_suspendida'].sum()}")
    print(f"Urgencias: {df['es_urgencia'].sum()}")

    print("\n=== PRIMERAS FILAS ===")
    print(df.head(10).to_string(index=False))

    df.to_csv(RUTA_SALIDA_CSV, index=False)
    print(f"\nArchivo generado correctamente en:\n{RUTA_SALIDA_CSV}")


if __name__ == "__main__":
    main()