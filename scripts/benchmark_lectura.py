import argparse
import time
import json
import os
import statistics
import mysql.connector
import psycopg2
from config import MARIADB_CONFIG, POSTGRES_CONFIG

RESULTADOS_DIR = os.path.join(os.path.dirname(__file__), "..", "resultados")
os.makedirs(RESULTADOS_DIR, exist_ok=True)

REPETICIONES = 5

CONSULTAS_BASICAS = {
    "b1_select_por_pk": "SELECT * FROM clientes WHERE id = 75000",

    "b2_select_where_indexado": "SELECT * FROM pedidos WHERE estado = 'entregado' LIMIT 1000",

    "b3_busqueda_texto": "SELECT * FROM productos WHERE nombre LIKE '%Pro%' LIMIT 500",

    "b4_orden_y_limite": "SELECT id, nombre, precio FROM productos ORDER BY precio DESC LIMIT 100",

    "b5_agregacion_simple": """
        SELECT estado, COUNT(*) AS total, AVG(total) AS promedio
        FROM pedidos
        GROUP BY estado
    """,
}


CONSULTAS_COMPLEJAS = {
    "c1_join_simple": """
        SELECT p.id, c.nombre, c.apellido, p.total
        FROM pedidos p
        INNER JOIN clientes c ON p.cliente_id = c.id
        WHERE p.estado = 'entregado'
        LIMIT 1000
    """,

    "c2_join_multiple_top_clientes": """
        SELECT c.id, c.nombre, COUNT(dp.id) AS items, SUM(dp.subtotal) AS total_gastado
        FROM clientes c
        INNER JOIN pedidos p ON p.cliente_id = c.id
        INNER JOIN detalle_pedidos dp ON dp.pedido_id = p.id
        GROUP BY c.id, c.nombre
        ORDER BY total_gastado DESC
        LIMIT 100
    """,

    "c3_subconsulta_productos_sin_ventas": """
        SELECT pr.id, pr.nombre
        FROM productos pr
        WHERE NOT EXISTS (
            SELECT 1 FROM detalle_pedidos dp WHERE dp.producto_id = pr.id
        )
        LIMIT 200
    """,

    "c4_join_having_clientes_frecuentes": """
        SELECT c.id, c.nombre, COUNT(p.id) AS num_pedidos
        FROM clientes c
        INNER JOIN pedidos p ON p.cliente_id = c.id
        GROUP BY c.id, c.nombre
        HAVING COUNT(p.id) > 3
        ORDER BY num_pedidos DESC
        LIMIT 100
    """,

    "c5_ventas_por_categoria": """
        SELECT cat.nombre AS categoria, COUNT(dp.id) AS items_vendidos, SUM(dp.subtotal) AS total_vendido
        FROM categorias cat
        INNER JOIN productos pr ON pr.categoria_id = cat.id
        INNER JOIN detalle_pedidos dp ON dp.producto_id = pr.id
        INNER JOIN pedidos p ON p.id = dp.pedido_id
        WHERE p.estado != 'cancelado'
        GROUP BY cat.id, cat.nombre
        ORDER BY total_vendido DESC
    """,
}


def conectar(motor):
    if motor == "mariadb":
        return mysql.connector.connect(**MARIADB_CONFIG)
    else:
        return psycopg2.connect(**POSTGRES_CONFIG)


def medir_consulta(conn, query):
    tiempos = []
    for _ in range(REPETICIONES):
        cur = conn.cursor()
        inicio = time.perf_counter()
        cur.execute(query)
        cur.fetchall()
        fin = time.perf_counter()
        cur.close()
        tiempos.append(fin - inicio)
    return {
        "promedio_segundos": round(statistics.mean(tiempos), 5),
        "min_segundos": round(min(tiempos), 5),
        "max_segundos": round(max(tiempos), 5),
        "repeticiones": REPETICIONES,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--motor", choices=["mariadb", "postgres"], required=True)
    args = parser.parse_args()

    conn = conectar(args.motor)
    print(f"\n=== BENCHMARK DE LECTURA: {args.motor.upper()} ===\n")

    resultados = {"basicas": {}, "complejas": {}}

    print("--- Consultas BÁSICAS ---")
    for nombre, query in CONSULTAS_BASICAS.items():
        print(f"-> {nombre} ({REPETICIONES} repeticiones)...")
        r = medir_consulta(conn, query)
        resultados["basicas"][nombre] = r
        print(f"   Promedio: {r['promedio_segundos']}s | Min: {r['min_segundos']}s | Max: {r['max_segundos']}s\n")

    print("--- Consultas COMPLEJAS ---")
    for nombre, query in CONSULTAS_COMPLEJAS.items():
        print(f"-> {nombre} ({REPETICIONES} repeticiones)...")
        r = medir_consulta(conn, query)
        resultados["complejas"][nombre] = r
        print(f"   Promedio: {r['promedio_segundos']}s | Min: {r['min_segundos']}s | Max: {r['max_segundos']}s\n")

    conn.close()

    salida = os.path.join(RESULTADOS_DIR, f"lectura_{args.motor}.json")
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"Resultados guardados en: {salida}")


if __name__ == "__main__":
    main()
