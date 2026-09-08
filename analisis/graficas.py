"""
Consolida los resultados JSON de ambos motores y genera las gráficas
comparativas para la presentación final del proyecto.

Genera en analisis/graficas_salida/:
    - insercion_comparativo.png
    - lectura_basicas_comparativo.png
    - lectura_complejas_comparativo.png
    - transacciones_comparativo.png
    - tamano_comparativo.png
    - tabla_kpis.csv

Uso:
    python graficas.py
"""

import json
import os
import glob
import matplotlib.pyplot as plt
import pandas as pd

RESULTADOS_DIR = os.path.join(os.path.dirname(__file__), "..", "resultados")
SALIDA_DIR = os.path.join(os.path.dirname(__file__), "graficas_salida")
os.makedirs(SALIDA_DIR, exist_ok=True)


def graficar_insercion():
    ruta_m = os.path.join(RESULTADOS_DIR, "insercion_mariadb.json")
    ruta_p = os.path.join(RESULTADOS_DIR, "insercion_postgres.json")
    if not (os.path.exists(ruta_m) and os.path.exists(ruta_p)):
        print("[!] Faltan resultados de inserción, omitiendo gráfica")
        return

    datos_m = json.load(open(ruta_m, encoding="utf-8"))
    datos_p = json.load(open(ruta_p, encoding="utf-8"))

    vols_m = [r["total_registros_insertados"] for r in datos_m]
    vel_m = [r["registros_por_segundo"] for r in datos_m]
    vols_p = [r["total_registros_insertados"] for r in datos_p]
    vel_p = [r["registros_por_segundo"] for r in datos_p]

    plt.figure(figsize=(9, 5))
    plt.plot(vols_m, vel_m, marker="o", label="MariaDB")
    plt.plot(vols_p, vel_p, marker="s", label="PostgreSQL")
    plt.xlabel("Registros insertados (total)")
    plt.ylabel("Velocidad (registros/segundo)")
    plt.title("Velocidad de inserción por volumen de datos")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(SALIDA_DIR, "insercion_comparativo.png"), dpi=150)
    plt.close()
    print("Gráfica generada: insercion_comparativo.png")


def graficar_lectura(tipo):
    """tipo: 'basicas' o 'complejas'"""
    ruta_m = os.path.join(RESULTADOS_DIR, "lectura_mariadb.json")
    ruta_p = os.path.join(RESULTADOS_DIR, "lectura_postgres.json")
    if not (os.path.exists(ruta_m) and os.path.exists(ruta_p)):
        print(f"[!] Faltan resultados de lectura, omitiendo gráfica de {tipo}")
        return

    datos_m = json.load(open(ruta_m, encoding="utf-8"))
    datos_p = json.load(open(ruta_p, encoding="utf-8"))

    consultas = list(datos_m[tipo].keys())
    tiempos_m = [datos_m[tipo][c]["promedio_segundos"] for c in consultas]
    tiempos_p = [datos_p[tipo][c]["promedio_segundos"] for c in consultas]

    x = range(len(consultas))
    ancho = 0.35
    plt.figure(figsize=(11, 6))
    plt.bar([i - ancho / 2 for i in x], tiempos_m, width=ancho, label="MariaDB")
    plt.bar([i + ancho / 2 for i in x], tiempos_p, width=ancho, label="PostgreSQL")
    plt.xticks(list(x), consultas, rotation=30, ha="right")
    plt.ylabel("Tiempo promedio (segundos)")
    titulo = "básicas" if tipo == "basicas" else "complejas"
    plt.title(f"Velocidad de lectura — consultas {titulo}")
    plt.legend()
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    nombre_archivo = f"lectura_{tipo}_comparativo.png"
    plt.savefig(os.path.join(SALIDA_DIR, nombre_archivo), dpi=150)
    plt.close()
    print(f"Gráfica generada: {nombre_archivo}")


def graficar_transacciones():
    ruta_m = os.path.join(RESULTADOS_DIR, "transacciones_mariadb.json")
    ruta_p = os.path.join(RESULTADOS_DIR, "transacciones_postgres.json")
    if not (os.path.exists(ruta_m) and os.path.exists(ruta_p)):
        print("[!] Faltan resultados de transacciones, omitiendo gráfica")
        return

    datos_m = json.load(open(ruta_m, encoding="utf-8"))
    datos_p = json.load(open(ruta_p, encoding="utf-8"))

    transacciones = list(datos_m.keys())
    tps_m = [datos_m[t]["transacciones_por_segundo"] for t in transacciones]
    tps_p = [datos_p[t]["transacciones_por_segundo"] for t in transacciones]

    x = range(len(transacciones))
    ancho = 0.35
    plt.figure(figsize=(11, 6))
    plt.bar([i - ancho / 2 for i in x], tps_m, width=ancho, label="MariaDB")
    plt.bar([i + ancho / 2 for i in x], tps_p, width=ancho, label="PostgreSQL")
    plt.xticks(list(x), transacciones, rotation=30, ha="right")
    plt.ylabel("Transacciones por segundo (TPS)")
    plt.title("Velocidad de transacciones (operaciones multi-paso)")
    plt.legend()
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(os.path.join(SALIDA_DIR, "transacciones_comparativo.png"), dpi=150)
    plt.close()
    print("Gráfica generada: transacciones_comparativo.png")


def graficar_tamano():
    archivos_m = sorted(glob.glob(os.path.join(RESULTADOS_DIR, "tamano_mariadb_*.json")))
    archivos_p = sorted(glob.glob(os.path.join(RESULTADOS_DIR, "tamano_postgres_*.json")))
    if not archivos_m or not archivos_p:
        print("[!] Faltan resultados de tamaño, omitiendo gráfica")
        return

    etiquetas_m, mb_m = [], []
    for a in archivos_m:
        d = json.load(open(a, encoding="utf-8"))
        etiquetas_m.append(d["etiqueta_volumen"])
        mb_m.append(d["total_mb"])

    etiquetas_p, mb_p = [], []
    for a in archivos_p:
        d = json.load(open(a, encoding="utf-8"))
        etiquetas_p.append(d["etiqueta_volumen"])
        mb_p.append(d["total_mb"])

    plt.figure(figsize=(9, 5))
    plt.plot(etiquetas_m, mb_m, marker="o", label="MariaDB")
    plt.plot(etiquetas_p, mb_p, marker="s", label="PostgreSQL")
    plt.xlabel("Volumen de datos cargado")
    plt.ylabel("Tamaño en disco (MB)")
    plt.title("Tamaño de la base de datos por volumen")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(SALIDA_DIR, "tamano_comparativo.png"), dpi=150)
    plt.close()
    print("Gráfica generada: tamano_comparativo.png")


def generar_tabla_kpis():
    filas = []

    for motor in ["mariadb", "postgres"]:
        ruta_ins = os.path.join(RESULTADOS_DIR, f"insercion_{motor}.json")
        if os.path.exists(ruta_ins):
            datos = json.load(open(ruta_ins, encoding="utf-8"))
            mejor = max(r["registros_por_segundo"] for r in datos)
            filas.append({"motor": motor, "kpi": "Inserción máx. (reg/s)", "valor": mejor})

        ruta_lec = os.path.join(RESULTADOS_DIR, f"lectura_{motor}.json")
        if os.path.exists(ruta_lec):
            datos = json.load(open(ruta_lec, encoding="utf-8"))
            prom_basicas = sum(v["promedio_segundos"] for v in datos["basicas"].values()) / len(datos["basicas"])
            prom_complejas = sum(v["promedio_segundos"] for v in datos["complejas"].values()) / len(datos["complejas"])
            filas.append({"motor": motor, "kpi": "Lectura básicas prom. (s)", "valor": round(prom_basicas, 5)})
            filas.append({"motor": motor, "kpi": "Lectura complejas prom. (s)", "valor": round(prom_complejas, 5)})

        ruta_tx = os.path.join(RESULTADOS_DIR, f"transacciones_{motor}.json")
        if os.path.exists(ruta_tx):
            datos = json.load(open(ruta_tx, encoding="utf-8"))
            prom_tps = sum(v["transacciones_por_segundo"] for v in datos.values()) / len(datos)
            filas.append({"motor": motor, "kpi": "TPS promedio (transacciones)", "valor": round(prom_tps, 2)})

        archivos_tam = sorted(glob.glob(os.path.join(RESULTADOS_DIR, f"tamano_{motor}_*.json")))
        if archivos_tam:
            ultimo = json.load(open(archivos_tam[-1], encoding="utf-8"))
            filas.append({"motor": motor, "kpi": "Tamaño final BD (MB)", "valor": ultimo["total_mb"]})

    df = pd.DataFrame(filas)
    ruta_csv = os.path.join(SALIDA_DIR, "tabla_kpis.csv")
    df.to_csv(ruta_csv, index=False)
    print(f"Tabla de KPIs guardada en: {ruta_csv}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    graficar_insercion()
    graficar_lectura("basicas")
    graficar_lectura("complejas")
    graficar_transacciones()
    graficar_tamano()
    generar_tabla_kpis()
