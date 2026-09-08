

MARIADB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "benchmark123",
    "database": "benchmark_db",
}

POSTGRES_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "postgres",
    "password": "benchmark123",
    "dbname": "benchmark_db",
}

TABLAS_ORDEN = [
    "categorias",
    "proveedores",
    "productos",
    "clientes",
    "direcciones",
    "pedidos",
    "detalle_pedidos",
    "pagos",
]

VOLUMENES_PRUEBA = [1_000, 10_000, 100_000, 500_000]
