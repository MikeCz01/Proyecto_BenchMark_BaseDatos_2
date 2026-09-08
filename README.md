# Benchmark de Bases de Datos: MariaDB vs PostgreSQL

## . Cómo ejecutar el proyecto paso a paso (Windows / PowerShell)

# 0. Instalar dependencias 
pip install faker mysql-connector-python psycopg2-binary matplotlib pandas

# 2. Levantar MariaDB
docker compose up -d mariadb

# 3. Crear el esquema en MariaDB 
Get-Content schema/mariadb_schema.sql | docker exec -i bench_mariadb mariadb -uroot -pbenchmark123

# 4. Generar los datos 
python scripts/generar_datos.py

# 5. Benchmark de INSERCIÓN sobre MariaDB 
cd scripts
python benchmark_insercion.py --motor mariadb --completo

# 6. Benchmark de LECTURA sobre MariaDB 
python benchmark_lectura.py --motor mariadb

# 7. Benchmark de TRANSACCIONES sobre MariaDB 
python benchmark_transacciones.py --motor mariadb

# 8. Medir TAMAÑO en disco de MariaDB
python medir_tamano.py --motor mariadb --etiqueta completo

# 9. Cambiar a PostgreSQL: apagar MariaDB, levantar Postgres
cd ..
docker compose stop mariadb
docker compose up -d postgres

# 10. Crear el esquema en PostgreSQL
Get-Content schema/postgres_schema.sql | docker exec -i bench_postgres psql -U postgres -d benchmark_db

# 11. Repetir TODO el benchmark, ahora con --motor postgres
cd scripts
python benchmark_insercion.py --motor postgres --completo
python benchmark_lectura.py --motor postgres
python benchmark_transacciones.py --motor postgres
python medir_tamano.py --motor postgres --etiqueta completo

# 12. Generar gráficas y tabla de KPIs para la presentación
cd ../analisis
python graficas.py
```

