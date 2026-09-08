import argparse
import json
import os
import mysql.connector
import psycopg2
from config import MARIADB_CONFIG, POSTGRES_CONFIG, TABLAS_ORDEN

RESULTADOS_DIR = os.path.join(os.path.dirname(__file__), "..", "resultados")
os.makedirs(RESULTADOS_DIR, exist_ok=True)


def medir_mariadb():
    conn = mysql.connector.connect(**MARIADB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT ROUND(SUM(data_length + index_length), 2) AS total_bytes
        FROM information_schema.tables
        WHERE table_schema = %s
    """, (MARIADB_CONFIG["database"],))
    total_bytes = float(cur.fetchone()[0] or 0)

    cur.execute("""
        SELECT table_name, data_length, index_length
        FROM information_schema.tables
        WHERE table_schema = %s
    """, (MARIADB_CONFIG["database"],))
    detalle = {
        row[0]: {"datos_bytes": float(row[1] or 0), "indices_bytes": float(row[2] or 0)}
        for row in cur.fetchall()
    }

    cur.close()
    conn.close()
    return total_bytes, detalle


def medir_postgres():
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT pg_database_size(%s)", (POSTGRES_CONFIG["dbname"],))
    total_bytes = float(cur.fetchone()[0])

    detalle = {}
    for tabla in TABLAS_ORDEN:
        cur.execute("SELECT pg_total_relation_size(%s), pg_relation_size(%s)", (tabla, tabla))
        total_rel, solo_datos = cur.fetchone()
        detalle[tabla] = {
            "datos_bytes": float(solo_datos),
            "indices_bytes": float(total_rel - solo_datos),
        }

    cur.close()
    conn.close()
    return total_bytes, detalle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--motor", choices=["mariadb", "postgres"], required=True)
    parser.add_argument("--etiqueta", required=True)
    args = parser.parse_args()

    if args.motor == "mariadb":
        total_bytes, detalle = medir_mariadb()
    else:
        total_bytes, detalle = medir_postgres()

    resultado = {
        "motor": args.motor,
        "etiqueta_volumen": args.etiqueta,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "total_gb": round(total_bytes / (1024 * 1024 * 1024), 4),
        "detalle_por_tabla_mb": {
            t: {k: round(v_ / (1024 * 1024), 3) for k, v_ in v.items()}
            for t, v in detalle.items()
        },
    }

    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    salida = os.path.join(RESULTADOS_DIR, f"tamano_{args.motor}_{args.etiqueta}.json")
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultados guardados en: {salida}")


if __name__ == "__main__":
    main()
