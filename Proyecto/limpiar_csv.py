from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_EXCEL = BASE_DIR / "Data" / "2025.xls"
RUTA_SALIDA_CSV = BASE_DIR / "Data" / "quirofano_2025_limpio.csv"


def cargar_y_limpiar(ruta_excel: Path) -> pd.DataFrame:
    bruto = pd.read_excel(ruta_excel, header=None, engine="xlrd")

    # En el Excel 2025 los datos empiezan en la fila 11
    datos = bruto.iloc[11:].copy()

    df = pd.DataFrame({
        "paciente_id": datos.iloc[:, 0],
        "servicio": datos.iloc[:, 3],
        "quirofano": datos.iloc[:, 4],
        "centro": datos.iloc[:, 7],
        "fecha": datos.iloc[:, 11],
        "hora_inicio": datos.iloc[:, 12],
        "hora_fin": datos.iloc[:, 15],
        "anestesia": datos.iloc[:, 17],
        "ambulatorio": datos.iloc[:, 20],
        "tipo_caso": datos.iloc[:, 21],
        "turno": datos.iloc[:, 25],
        "progr": datos.iloc[:, 26],
        "impl": datos.iloc[:, 27],
        "dx_codigo": datos.iloc[:, 28],
        "diagnostico": datos.iloc[:, 29],
        "proc_codigo": datos.iloc[:, 30],
        "procedimiento": datos.iloc[:, 31],
        "cirujano_principal": datos.iloc[:, 32],
        "anestesista_principal": datos.iloc[:, 33],
        "suspendida": datos.iloc[:, 34],
        "motivo_suspension": datos.iloc[:, 35] if bruto.shape[1] > 35 else np.nan,
        "provincia": datos.iloc[:, 36] if bruto.shape[1] > 36 else np.nan,
        "sector": datos.iloc[:, 37] if bruto.shape[1] > 37 else np.nan,
    })

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .replace({"nan": np.nan, "None": np.nan, "": np.nan})
            )

    df["quirofano"] = df["quirofano"].astype(str).str.extract(r"(QE\d+)")[0]
    df = df[df["quirofano"].notna()].copy()

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    df["inicio_dt"] = pd.to_datetime(
        df["fecha"].dt.strftime("%Y-%m-%d") + " " + df["hora_inicio"].astype(str),
        errors="coerce",
    )

    df["fin_dt"] = pd.to_datetime(
        df["fecha"].dt.strftime("%Y-%m-%d") + " " + df["hora_fin"].astype(str),
        errors="coerce",
    )

    cruza_medianoche = df["fin_dt"] < df["inicio_dt"]
    df.loc[cruza_medianoche, "fin_dt"] += pd.Timedelta(days=1)

    df["duracion_min"] = (df["fin_dt"] - df["inicio_dt"]).dt.total_seconds() / 60
    df["duracion_horas"] = df["duracion_min"] / 60

    df["tipo_caso"] = df["tipo_caso"].astype(str).str.strip().str.upper()
    df["suspendida"] = df["suspendida"].astype(str).str.strip().str.upper()

    df["es_urgencia"] = df["tipo_caso"].eq("U")
    df["esta_suspendida"] = df["suspendida"].eq("S")

    print("\n=== DEBUG ANTES DEL FILTRO FINAL ===")
    print("Filas antes del filtro:", len(df))
    print("Quirófanos:", df["quirofano"].dropna().unique()[:20])
    print("\nColumnas fecha/hora:")
    print(df[["fecha", "hora_inicio", "hora_fin", "inicio_dt", "fin_dt", "duracion_min"]].head(20).to_string(index=False))

    df = df[df["inicio_dt"].notna() & df["fin_dt"].notna()].copy()
    df = df[df["duracion_min"].notna() & (df["duracion_min"] > 0)].copy()

    return df.reset_index(drop=True)


def main():
    print("=== COMPROBACIÓN DE RUTAS ===")
    print(f"Base del proyecto: {BASE_DIR}")
    print(f"Excel encontrado: {RUTA_EXCEL.exists()}")
    print(f"Ruta Excel: {RUTA_EXCEL}")

    df = cargar_y_limpiar(RUTA_EXCEL)

    print("\n=== RESUMEN INICIAL ===")
    print(f"Filas totales: {len(df)}")
    print(f"Quirófanos detectados: {df['quirofano'].nunique()}")
    print(f"Suspendidas: {df['esta_suspendida'].sum()}")
    print(f"Urgencias: {df['es_urgencia'].sum()}")

    print("\n=== QUIRÓFANOS ===")
    print(df["quirofano"].value_counts().to_string())

    print("\n=== PRIMERAS FILAS ===")
    print(df.head(10).to_string(index=False))

    df.to_csv(RUTA_SALIDA_CSV, index=False)
    print(f"\nArchivo generado correctamente en:\n{RUTA_SALIDA_CSV}")


if __name__ == "__main__":
    main()