

import argparse
import csv
import os
import random
import time
import json
import mysql.connector
import psycopg2
import psycopg2.extras
from config import MARIADB_CONFIG, POSTGRES_CONFIG, TABLAS_ORDEN, VOLUMENES_PRUEBA

CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "resultados_csv")
RESULTADOS_DIR = os.path.join(os.path.dirname(__file__), "..", "resultados")
os.makedirs(RESULTADOS_DIR, exist_ok=True)

BATCH_SIZE = 5000

FK_MAP = {
    "productos": [("categoria_id", "categorias"), ("proveedor_id", "proveedores")],
    "direcciones": [("cliente_id", "clientes")],
    "pedidos": [("cliente_id", "clientes"), ("direccion_id", "direcciones")],
    "detalle_pedidos": [("pedido_id", "pedidos"), ("producto_id", "productos")],
    "pagos": [("pedido_id", "pedidos")],
}


def conectar(motor):
    if motor == "mariadb":
        conn = mysql.connector.connect(**MARIADB_CONFIG)
    else:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
    conn.autocommit = False
    return conn


def leer_csv_completo(tabla):
    ruta = os.path.join(CSV_DIR, f"{tabla}.csv")
    with open(ruta, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        encabezado = next(reader)
        filas = list(reader)
    return encabezado, filas


def truncar_tablas(conn, motor):
    cur = conn.cursor()
    if motor == "mariadb":
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for t in reversed(TABLAS_ORDEN):
            cur.execute(f"TRUNCATE TABLE {t}")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    else:
        cur.execute(f"TRUNCATE TABLE {', '.join(TABLAS_ORDEN)} RESTART IDENTITY CASCADE")
    conn.commit()
    cur.close()


def insertar_tabla(conn, motor, tabla, limite, contadores, rng):
    encabezado, filas_totales = leer_csv_completo(tabla)
    idx_col = {nombre: i for i, nombre in enumerate(encabezado)}
    fks = FK_MAP.get(tabla, [])

    if limite is not None:
        filas = [list(f) for f in filas_totales[:limite]]
        if fks:
            for fila in filas:
                for col_fk, tabla_padre in fks:
                    max_id_disponible = contadores.get(tabla_padre, 0)
                    if max_id_disponible > 0:
                        fila[idx_col[col_fk]] = str(rng.randint(1, max_id_disponible))
    else:
        filas = filas_totales

    cols = ", ".join(encabezado)
    if motor == "postgres":
        query = f"INSERT INTO {tabla} ({cols}) VALUES %s"
    else:
        query = f"INSERT INTO {tabla} ({cols}) VALUES ({', '.join(['%s'] * len(encabezado))})"

    cur = conn.cursor()
    inicio = time.perf_counter()
    for i in range(0, len(filas), BATCH_SIZE):
        lote = filas[i:i + BATCH_SIZE]
        if motor == "postgres":
            psycopg2.extras.execute_values(cur, query, lote, page_size=BATCH_SIZE)
        else:
            cur.executemany(query, lote)
        conn.commit()
    fin = time.perf_counter()
    cur.close()

    contadores[tabla] = len(filas)
    return len(filas), fin - inicio


def correr_prueba_volumen(motor, volumen):
    conn = conectar(motor)
    truncar_tablas(conn, motor)

    rng = random.Random(42)
    detalle = {}
    total_registros = 0
    contadores = {}
    inicio_total = time.perf_counter()
    for tabla in TABLAS_ORDEN:
        n, t = insertar_tabla(conn, motor, tabla, volumen, contadores, rng)
        detalle[tabla] = {"registros": n, "segundos": round(t, 4)}
        total_registros += n
    fin_total = time.perf_counter()

    conn.close()

    resultado = {
        "motor": motor,
        "volumen_objetivo": volumen,
        "total_registros_insertados": total_registros,
        "tiempo_total_segundos": round(fin_total - inicio_total, 4),
        "registros_por_segundo": round(total_registros / (fin_total - inicio_total), 2),
        "detalle_por_tabla": detalle,
    }
    return resultado


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--motor", choices=["mariadb", "postgres"], required=True)
    parser.add_argument("--completo", action="store_true")
    args = parser.parse_args()

    resultados = []
    print(f"\n=== BENCHMARK DE INSERCIÓN: {args.motor.upper()} ===\n")

    for vol in VOLUMENES_PRUEBA:
        print(f"-> Probando volumen: {vol:,} registros por tabla...")
        r = correr_prueba_volumen(args.motor, vol)
        resultados.append(r)
        print(f"   Total: {r['total_registros_insertados']:,} regs | "
              f"Tiempo: {r['tiempo_total_segundos']}s | "
              f"Velocidad: {r['registros_por_segundo']:,} reg/s\n")

    if args.completo:
        print("-> Insertando dataset COMPLETO (>1,000,000 registros)...")
        r = correr_prueba_volumen(args.motor, None)
        resultados.append(r)
        print(f"   Total: {r['total_registros_insertados']:,} regs | "
              f"Tiempo: {r['tiempo_total_segundos']}s | "
              f"Velocidad: {r['registros_por_segundo']:,} reg/s\n")

    salida = os.path.join(RESULTADOS_DIR, f"insercion_{args.motor}.json")
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"Resultados guardados en: {salida}")


if __name__ == "__main__":
    main()