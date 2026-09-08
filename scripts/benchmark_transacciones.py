import argparse
import json
import os
import random
import time
import mysql.connector
import psycopg2
from config import MARIADB_CONFIG, POSTGRES_CONFIG

RESULTADOS_DIR = os.path.join(os.path.dirname(__file__), "..", "resultados")
os.makedirs(RESULTADOS_DIR, exist_ok=True)

REPETICIONES = 100  # cuántas veces se ejecuta cada transacción para medir

# Rangos conocidos de IDs existentes tras cargar el dataset completo
# (ver scripts/generar_datos.py)
RANGO_CLIENTES = (1, 150_000)
RANGO_DIRECCIONES = (1, 150_000)
RANGO_PRODUCTOS = (1, 47_000)
RANGO_CATEGORIAS = (1, 50)
RANGO_PEDIDOS = (1, 250_000)


def conectar(motor):
    conn = mysql.connector.connect(**MARIADB_CONFIG) if motor == "mariadb" else psycopg2.connect(**POSTGRES_CONFIG)
    conn.autocommit = False
    return conn


def obtener_id_insertado(cur, conn, motor, query, params, id_col="id"):
    """Ejecuta un INSERT y devuelve el ID autogenerado, sea MariaDB o Postgres."""
    if motor == "mariadb":
        cur.execute(query, params)
        return cur.lastrowid
    else:
        cur.execute(query + f" RETURNING {id_col}", params)
        return cur.fetchone()[0]

def tx_crear_pedido_completo(conn, motor, rng):
    cur = conn.cursor()
    cliente_id = rng.randint(*RANGO_CLIENTES)
    direccion_id = rng.randint(*RANGO_DIRECCIONES)

    pedido_id = obtener_id_insertado(
        cur, conn, motor,
        "INSERT INTO pedidos (cliente_id, direccion_id, fecha_pedido, estado, total) "
        "VALUES (%s, %s, NOW(), %s, %s)",
        (cliente_id, direccion_id, "pendiente", 0),
    )

    total = 0
    for _ in range(2):
        producto_id = rng.randint(*RANGO_PRODUCTOS)
        cantidad = rng.randint(1, 5)
        precio_unitario = round(rng.uniform(10, 500), 2)
        subtotal = round(cantidad * precio_unitario, 2)
        total += subtotal
        cur.execute(
            "INSERT INTO detalle_pedidos (pedido_id, producto_id, cantidad, precio_unitario, subtotal) "
            "VALUES (%s, %s, %s, %s, %s)",
            (pedido_id, producto_id, cantidad, precio_unitario, subtotal),
        )

    cur.execute("UPDATE pedidos SET total = %s WHERE id = %s", (total, pedido_id))

    cur.execute(
        "INSERT INTO pagos (pedido_id, metodo_pago, monto, fecha_pago, estado) "
        "VALUES (%s, %s, %s, NOW(), %s)",
        (pedido_id, "tarjeta_credito", total, "completado"),
    )

    conn.commit()
    cur.close()

def tx_actualizar_stock(conn, motor, rng):
    cur = conn.cursor()
    producto_id = rng.randint(*RANGO_PRODUCTOS)
    cantidad_vendida = rng.randint(1, 3)

    cur.execute("SELECT stock FROM productos WHERE id = %s", (producto_id,))
    fila = cur.fetchone()
    stock_actual = fila[0] if fila else 0
    nuevo_stock = max(stock_actual - cantidad_vendida, 0)

    cur.execute("UPDATE productos SET stock = %s WHERE id = %s", (nuevo_stock, producto_id))
    conn.commit()
    cur.close()

def tx_cancelar_pedido(conn, motor, rng):
    cur = conn.cursor()
    pedido_id = rng.randint(*RANGO_PEDIDOS)

    cur.execute("UPDATE pedidos SET estado = %s WHERE id = %s", ("cancelado", pedido_id))
    cur.execute("UPDATE pagos SET estado = %s WHERE pedido_id = %s", ("rechazado", pedido_id))

    conn.commit()
    cur.close()

def tx_descuento_categoria(conn, motor, rng):
    cur = conn.cursor()
    categoria_id = rng.randint(*RANGO_CATEGORIAS)
    porcentaje = rng.choice([0.90, 0.95, 0.85])  # 10%, 5% o 15% de descuento

    cur.execute(
        "UPDATE productos SET precio = ROUND(precio * %s, 2) WHERE categoria_id = %s",
        (porcentaje, categoria_id),
    )
    conn.commit()
    cur.close()


def tx_alta_cliente(conn, motor, rng):
    cur = conn.cursor()
    sufijo = rng.randint(1_000_000, 9_999_999)

    cliente_id = obtener_id_insertado(
        cur, conn, motor,
        "INSERT INTO clientes (nombre, apellido, email, telefono, fecha_registro) "
        "VALUES (%s, %s, %s, %s, NOW())",
        ("Cliente", "Prueba", f"cliente_tx_{sufijo}@ejemplo.com", "00000000"),
    )

    cur.execute(
        "INSERT INTO direcciones (cliente_id, calle, ciudad, departamento, codigo_postal, pais) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (cliente_id, "Calle de prueba", "Ciudad de prueba", "Depto Prueba", "00000", "Honduras"),
    )

    conn.commit()
    cur.close()


TRANSACCIONES = {
    "t1_crear_pedido_completo": tx_crear_pedido_completo,
    "t2_actualizar_stock_venta": tx_actualizar_stock,
    "t3_cancelar_pedido": tx_cancelar_pedido,
    "t4_descuento_categoria": tx_descuento_categoria,
    "t5_alta_cliente_direccion": tx_alta_cliente,
}


def medir_transaccion(conn, motor, funcion, rng):
    tiempos = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        funcion(conn, motor, rng)
        fin = time.perf_counter()
        tiempos.append(fin - inicio)

    tiempo_total = sum(tiempos)
    return {
        "repeticiones": REPETICIONES,
        "tiempo_total_segundos": round(tiempo_total, 4),
        "tiempo_promedio_ms": round((tiempo_total / REPETICIONES) * 1000, 3),
        "transacciones_por_segundo": round(REPETICIONES / tiempo_total, 2),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--motor", choices=["mariadb", "postgres"], required=True)
    args = parser.parse_args()

    conn = conectar(args.motor)
    rng = random.Random(42)

    print(f"\n=== BENCHMARK DE TRANSACCIONES: {args.motor.upper()} ===\n")
    print(f"(cada transacción se repite {REPETICIONES} veces)\n")

    resultados = {}
    for nombre, funcion in TRANSACCIONES.items():
        print(f"-> {nombre}...")
        r = medir_transaccion(conn, args.motor, funcion, rng)
        resultados[nombre] = r
        print(f"   TPS: {r['transacciones_por_segundo']} | "
              f"Promedio: {r['tiempo_promedio_ms']} ms | "
              f"Total: {r['tiempo_total_segundos']}s\n")

    conn.close()

    salida = os.path.join(RESULTADOS_DIR, f"transacciones_{args.motor}.json")
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"Resultados guardados en: {salida}")


if __name__ == "__main__":
    main()
