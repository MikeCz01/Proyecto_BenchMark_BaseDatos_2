import csv
import random
import os
from faker import Faker

fake = Faker("es_MX")
Faker.seed(42)
random.seed(42)

N_CATEGORIAS = 50
N_PROVEEDORES = 3_000
N_PRODUCTOS = 47_000
N_CLIENTES = 150_000
N_DIRECCIONES = 150_000
N_PEDIDOS = 250_000
N_DETALLE_PEDIDOS = 300_000
N_PAGOS = 250_000

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "resultados_csv")
os.makedirs(OUT_DIR, exist_ok=True)

ESTADOS_PEDIDO = ["pendiente", "procesando", "enviado", "entregado", "cancelado"]
ESTADOS_PAGO = ["pendiente", "completado", "rechazado"]
METODOS_PAGO = ["tarjeta_credito", "tarjeta_debito", "transferencia", "efectivo", "paypal"]


def fecha_aleatoria(inicio="-3y", fin="now"):
    return fake.date_time_between(start_date=inicio, end_date=fin)


def escribir_csv(nombre_archivo, encabezado, filas):
    ruta = os.path.join(OUT_DIR, nombre_archivo)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(encabezado)
        writer.writerows(filas)
    print(f"  -> {nombre_archivo}: {len(filas):,} registros")


def generar_categorias():
    print("Generando categorias...")
    nombres = set()
    filas = []
    while len(filas) < N_CATEGORIAS:
        nombre = fake.unique.word().capitalize() + " " + random.choice(
            ["Electrónica", "Hogar", "Ropa", "Deportes", "Juguetes", "Alimentos", "Belleza", "Libros"]
        )
        if nombre in nombres:
            continue
        nombres.add(nombre)
        filas.append([len(filas) + 1, nombre, fake.sentence(nb_words=8)])
    escribir_csv("categorias.csv", ["id", "nombre", "descripcion"], filas)
    return len(filas)


def generar_proveedores():
    print("Generando proveedores...")
    filas = []
    for i in range(1, N_PROVEEDORES + 1):
        filas.append([i, fake.company(), fake.name(), fake.phone_number()[:20], fake.company_email()])
    escribir_csv("proveedores.csv", ["id", "nombre", "contacto", "telefono", "email"], filas)
    return len(filas)


def generar_productos(n_categorias, n_proveedores):
    print("Generando productos...")
    filas = []
    for i in range(1, N_PRODUCTOS + 1):
        filas.append([
            i, fake.catch_phrase(), random.randint(1, n_categorias), random.randint(1, n_proveedores),
            round(random.uniform(5, 2500), 2), random.randint(0, 5000),
        ])
    escribir_csv("productos.csv", ["id", "nombre", "categoria_id", "proveedor_id", "precio", "stock"], filas)
    return len(filas)


def generar_clientes():
    print("Generando clientes...")
    filas = []
    for i in range(1, N_CLIENTES + 1):
        filas.append([
            i, fake.first_name(), fake.last_name(),
            f"cliente{i}_{fake.user_name()}@{fake.free_email_domain()}",
            fake.phone_number()[:20], fecha_aleatoria().strftime("%Y-%m-%d %H:%M:%S"),
        ])
    escribir_csv("clientes.csv", ["id", "nombre", "apellido", "email", "telefono", "fecha_registro"], filas)
    return len(filas)


def generar_direcciones(n_clientes):
    print("Generando direcciones...")
    filas = []
    for i in range(1, N_DIRECCIONES + 1):
        filas.append([
            i, random.randint(1, n_clientes), fake.street_address(),
            fake.city(), fake.state(), fake.postcode(), "Honduras",
        ])
    escribir_csv("direcciones.csv", ["id", "cliente_id", "calle", "ciudad", "departamento", "codigo_postal", "pais"], filas)
    return len(filas)


def generar_pedidos(n_clientes, n_direcciones):
    print("Generando pedidos...")
    filas = []
    for i in range(1, N_PEDIDOS + 1):
        filas.append([
            i, random.randint(1, n_clientes), random.randint(1, n_direcciones),
            fecha_aleatoria().strftime("%Y-%m-%d %H:%M:%S"), random.choice(ESTADOS_PEDIDO),
            round(random.uniform(20, 5000), 2),
        ])
    escribir_csv("pedidos.csv", ["id", "cliente_id", "direccion_id", "fecha_pedido", "estado", "total"], filas)
    return len(filas)


def generar_detalle_pedidos(n_pedidos, n_productos):
    print("Generando detalle_pedidos...")
    filas = []
    for i in range(1, N_DETALLE_PEDIDOS + 1):
        cantidad = random.randint(1, 10)
        precio_unitario = round(random.uniform(5, 2500), 2)
        filas.append([
            i, random.randint(1, n_pedidos), random.randint(1, n_productos),
            cantidad, precio_unitario, round(cantidad * precio_unitario, 2),
        ])
    escribir_csv("detalle_pedidos.csv", ["id", "pedido_id", "producto_id", "cantidad", "precio_unitario", "subtotal"], filas)
    return len(filas)


def generar_pagos(n_pedidos):
    print("Generando pagos...")
    filas = []
    for i in range(1, N_PAGOS + 1):
        filas.append([
            i, random.randint(1, n_pedidos), random.choice(METODOS_PAGO),
            round(random.uniform(20, 5000), 2), fecha_aleatoria().strftime("%Y-%m-%d %H:%M:%S"),
            random.choice(ESTADOS_PAGO),
        ])
    escribir_csv("pagos.csv", ["id", "pedido_id", "metodo_pago", "monto", "fecha_pago", "estado"], filas)
    return len(filas)


if __name__ == "__main__":
    print("=" * 60)
    print("GENERADOR DE DATOS - Benchmark MariaDB vs PostgreSQL")
    print("=" * 60)

    total = 0
    total += generar_categorias()
    total += generar_proveedores()
    total += generar_productos(N_CATEGORIAS, N_PROVEEDORES)
    total += generar_clientes()
    total += generar_direcciones(N_CLIENTES)
    total += generar_pedidos(N_CLIENTES, N_DIRECCIONES)
    total += generar_detalle_pedidos(N_PEDIDOS, N_PRODUCTOS)
    total += generar_pagos(N_PEDIDOS)

    print("=" * 60)
    print(f"TOTAL DE REGISTROS GENERADOS: {total:,}")
    print(f"Archivos CSV guardados en: {OUT_DIR}")
    print("=" * 60)
