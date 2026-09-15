import json
import os
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

RESULTADOS_DIR = os.path.join(os.path.dirname(__file__), "..", "resultados")

HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="4472C4")

COLOR_MARIADB = "4472C4"
COLOR_POSTGRES = "ED7D31"


def cargar(nombre):
    with open(os.path.join(RESULTADOS_DIR, nombre), encoding="utf-8") as f:
        return json.load(f)


def escribir_tabla(ws, fila, col, encabezados, filas):
    """Escribe una tabla con encabezado en negrita y devuelve la fila siguiente libre."""
    for j, encabezado in enumerate(encabezados):
        celda = ws.cell(row=fila, column=col + j, value=encabezado)
        celda.font = HEADER_FONT
        celda.fill = HEADER_FILL
    for i, valores in enumerate(filas):
        for j, valor in enumerate(valores):
            ws.cell(row=fila + 1 + i, column=col + j, value=valor)
    for j, encabezado in enumerate(encabezados):
        ws.column_dimensions[get_column_letter(col + j)].width = max(14, len(str(encabezado)) + 2)
    return fila + 1 + len(filas)


def grafico_barras(ws, titulo, min_col, max_col, fila_encabezado, fila_fin, col_categorias, ancla, y_titulo=""):
    grafico = BarChart()
    grafico.type = "col"
    grafico.grouping = "clustered"
    grafico.title = titulo
    grafico.y_axis.title = y_titulo
    grafico.style = 10

    datos = Reference(ws, min_col=min_col, max_col=max_col, min_row=fila_encabezado, max_row=fila_fin)
    categorias = Reference(ws, min_col=col_categorias, max_col=col_categorias, min_row=fila_encabezado + 1, max_row=fila_fin)
    grafico.add_data(datos, titles_from_data=True)
    grafico.set_categories(categorias)
    grafico.width = 18
    grafico.height = 10
    ws.add_chart(grafico, ancla)
    return grafico


def hoja_resumen(wb, insercion_mdb, insercion_pg, lectura_mdb, lectura_pg, transacciones_mdb, transacciones_pg, tamano_mdb, tamano_pg):
    ws = wb.active
    ws.title = "Resumen"

    def prom(d, seccion):
        vals = [q["promedio_segundos"] for q in d[seccion].values()]
        return round(sum(vals) / len(vals), 5)

    def prom_tps(d):
        vals = [t["transacciones_por_segundo"] for t in d.values()]
        return round(sum(vals) / len(vals), 2)

    filas = [
        ("Inserción máx. (reg/s)", insercion_mdb[-1]["registros_por_segundo"], insercion_pg[-1]["registros_por_segundo"]),
        ("Lectura básicas prom. (s)", prom(lectura_mdb, "basicas"), prom(lectura_pg, "basicas")),
        ("Lectura complejas prom. (s)", prom(lectura_mdb, "complejas"), prom(lectura_pg, "complejas")),
        ("TPS promedio (transacciones)", prom_tps(transacciones_mdb), prom_tps(transacciones_pg)),
        ("Tamaño final BD (MB)", tamano_mdb["total_mb"], tamano_pg["total_mb"]),
    ]

    fila_fin = escribir_tabla(ws, 1, 1, ["KPI", "MariaDB", "Postgres"], filas)

    # Un grafico por KPI porque las escalas son muy distintas entre si (reg/s vs segundos vs MB)
    fila_ancla = fila_fin + 2
    for i, (kpi, _, _) in enumerate(filas):
        fila_dato = 2 + i
        grafico = BarChart()
        grafico.type = "col"
        grafico.title = kpi
        grafico.style = 10
        datos = Reference(ws, min_col=2, max_col=3, min_row=1, max_row=1)
        datos_fila = Reference(ws, min_col=2, max_col=3, min_row=fila_dato, max_row=fila_dato)
        grafico.add_data(datos_fila, titles_from_data=False)
        grafico.set_categories(Reference(ws, min_col=2, max_col=3, min_row=1, max_row=1))
        grafico.width = 10
        grafico.height = 7
        ws.add_chart(grafico, f"E{fila_ancla + i * 15}")

    return ws


def hoja_insercion(wb, insercion_mdb, insercion_pg):
    ws = wb.create_sheet("Insercion")

    filas = []
    for m, p in zip(insercion_mdb, insercion_pg):
        etiqueta = m["volumen_objetivo"] if m["volumen_objetivo"] is not None else "completo"
        filas.append((
            etiqueta,
            m["registros_por_segundo"], p["registros_por_segundo"],
            m["tiempo_total_segundos"], p["tiempo_total_segundos"],
        ))

    fila_fin = escribir_tabla(
        ws, 1, 1,
        ["Volumen objetivo", "Reg/s MariaDB", "Reg/s Postgres", "Tiempo total (s) MariaDB", "Tiempo total (s) Postgres"],
        filas,
    )

    grafico_barras(ws, "Registros por segundo vs volumen", 2, 3, 1, fila_fin, 1, "G2", "reg/s")
    grafico_barras(ws, "Tiempo total de carga vs volumen", 4, 5, 1, fila_fin, 1, "G22", "segundos")

    # Detalle por tabla de la corrida "completa" (ultimo elemento de cada lista)
    detalle_mdb = insercion_mdb[-1]["detalle_por_tabla"]
    detalle_pg = insercion_pg[-1]["detalle_por_tabla"]
    filas_tabla = []
    for tabla in detalle_mdb:
        filas_tabla.append((
            tabla,
            detalle_mdb[tabla]["registros"],
            detalle_mdb[tabla]["segundos"],
            detalle_pg[tabla]["segundos"],
        ))

    fila_inicio_tabla = fila_fin + 3
    fila_fin_tabla = escribir_tabla(
        ws, fila_inicio_tabla, 1,
        ["Tabla", "Registros (completo)", "Segundos MariaDB", "Segundos Postgres"],
        filas_tabla,
    )
    grafico_barras(
        ws, "Tiempo de carga por tabla (corrida completa)", 3, 4,
        fila_inicio_tabla, fila_fin_tabla, 1, "G42", "segundos",
    )
    return ws


def hoja_lectura(wb, nombre_hoja, titulo, lectura_mdb, lectura_pg, seccion):
    ws = wb.create_sheet(nombre_hoja)
    claves = list(lectura_mdb[seccion].keys())
    filas = [
        (clave, lectura_mdb[seccion][clave]["promedio_segundos"], lectura_pg[seccion][clave]["promedio_segundos"])
        for clave in claves
    ]
    fila_fin = escribir_tabla(ws, 1, 1, ["Consulta", "MariaDB (s)", "Postgres (s)"], filas)
    grafico_barras(ws, titulo, 2, 3, 1, fila_fin, 1, "F2", "segundos")
    return ws


def hoja_transacciones(wb, transacciones_mdb, transacciones_pg):
    ws = wb.create_sheet("Transacciones")
    claves = list(transacciones_mdb.keys())
    filas = [
        (
            clave,
            transacciones_mdb[clave]["transacciones_por_segundo"],
            transacciones_pg[clave]["transacciones_por_segundo"],
            transacciones_mdb[clave]["tiempo_promedio_ms"],
            transacciones_pg[clave]["tiempo_promedio_ms"],
        )
        for clave in claves
    ]
    fila_fin = escribir_tabla(
        ws, 1, 1,
        ["Transacción", "TPS MariaDB", "TPS Postgres", "Prom. ms MariaDB", "Prom. ms Postgres"],
        filas,
    )
    grafico_barras(ws, "Transacciones por segundo", 2, 3, 1, fila_fin, 1, "G2", "TPS")
    grafico_barras(ws, "Tiempo promedio por transacción", 4, 5, 1, fila_fin, 1, "G22", "ms")
    return ws


def hoja_tamano(wb, tamano_mdb, tamano_pg):
    ws = wb.create_sheet("Tamano_BD")

    filas_total = [("MariaDB", tamano_mdb["total_mb"]), ("Postgres", tamano_pg["total_mb"])]
    fila_fin_total = escribir_tabla(ws, 1, 1, ["Motor", "Total (MB)"], filas_total)
    grafico_barras(ws, "Tamaño total de la BD", 2, 2, 1, fila_fin_total, 1, "E2", "MB")

    detalle_mdb = tamano_mdb["detalle_por_tabla_mb"]
    detalle_pg = tamano_pg["detalle_por_tabla_mb"]
    tablas = list(detalle_mdb.keys())

    filas_detalle = []
    for tabla in tablas:
        filas_detalle.append((
            tabla,
            detalle_mdb[tabla]["datos_bytes"],
            detalle_mdb[tabla]["indices_bytes"],
            detalle_pg[tabla]["datos_bytes"],
            detalle_pg[tabla]["indices_bytes"],
        ))

    fila_inicio = fila_fin_total + 3
    fila_fin_detalle = escribir_tabla(
        ws, fila_inicio, 1,
        ["Tabla", "Datos MariaDB (MB)", "Índices MariaDB (MB)", "Datos Postgres (MB)", "Índices Postgres (MB)"],
        filas_detalle,
    )

    # Total por tabla (datos + indices) comparando motores
    grafico_total_tabla = BarChart()
    grafico_total_tabla.type = "col"
    grafico_total_tabla.grouping = "clustered"
    grafico_total_tabla.title = "Tamaño por tabla (MariaDB vs Postgres)"
    grafico_total_tabla.y_axis.title = "MB"
    col_total_mdb = 6
    col_total_pg = 7
    ws.cell(row=fila_inicio, column=col_total_mdb, value="Total MariaDB (MB)").font = HEADER_FONT
    ws.cell(row=fila_inicio, column=col_total_mdb).fill = HEADER_FILL
    ws.cell(row=fila_inicio, column=col_total_pg, value="Total Postgres (MB)").font = HEADER_FONT
    ws.cell(row=fila_inicio, column=col_total_pg).fill = HEADER_FILL
    for i, tabla in enumerate(tablas):
        ws.cell(row=fila_inicio + 1 + i, column=col_total_mdb,
                value=detalle_mdb[tabla]["datos_bytes"] + detalle_mdb[tabla]["indices_bytes"])
        ws.cell(row=fila_inicio + 1 + i, column=col_total_pg,
                value=detalle_pg[tabla]["datos_bytes"] + detalle_pg[tabla]["indices_bytes"])
    datos_ref = Reference(ws, min_col=col_total_mdb, max_col=col_total_pg, min_row=fila_inicio, max_row=fila_fin_detalle)
    cat_ref = Reference(ws, min_col=1, max_col=1, min_row=fila_inicio + 1, max_row=fila_fin_detalle)
    grafico_total_tabla.add_data(datos_ref, titles_from_data=True)
    grafico_total_tabla.set_categories(cat_ref)
    grafico_total_tabla.width = 18
    grafico_total_tabla.height = 10
    ws.add_chart(grafico_total_tabla, "I2")

    # Composicion datos vs indices, un grafico apilado por motor
    for motor, col_datos, col_indices, ancla in (
        ("MariaDB", 2, 3, "I22"),
        ("Postgres", 4, 5, "I42"),
    ):
        grafico = BarChart()
        grafico.type = "col"
        grafico.grouping = "stacked"
        grafico.overlap = 100
        grafico.title = f"{motor}: datos vs índices por tabla"
        grafico.y_axis.title = "MB"
        datos_ref = Reference(ws, min_col=col_datos, max_col=col_indices, min_row=fila_inicio, max_row=fila_fin_detalle)
        cat_ref = Reference(ws, min_col=1, max_col=1, min_row=fila_inicio + 1, max_row=fila_fin_detalle)
        grafico.add_data(datos_ref, titles_from_data=True)
        grafico.set_categories(cat_ref)
        grafico.width = 18
        grafico.height = 10
        ws.add_chart(grafico, ancla)

    return ws


def main():
    insercion_mdb = cargar("insercion_mariadb.json")
    insercion_pg = cargar("insercion_postgres.json")
    lectura_mdb = cargar("lectura_mariadb.json")
    lectura_pg = cargar("lectura_postgres.json")
    transacciones_mdb = cargar("transacciones_mariadb.json")
    transacciones_pg = cargar("transacciones_postgres.json")
    tamano_mdb = cargar("tamano_mariadb_completo.json")
    tamano_pg = cargar("tamano_postgres_completo.json")

    wb = Workbook()
    hoja_resumen(wb, insercion_mdb, insercion_pg, lectura_mdb, lectura_pg, transacciones_mdb, transacciones_pg, tamano_mdb, tamano_pg)
    hoja_insercion(wb, insercion_mdb, insercion_pg)
    hoja_lectura(wb, "Lectura_basicas", "Consultas básicas: tiempo promedio", lectura_mdb, lectura_pg, "basicas")
    hoja_lectura(wb, "Lectura_complejas", "Consultas complejas: tiempo promedio", lectura_mdb, lectura_pg, "complejas")
    hoja_transacciones(wb, transacciones_mdb, transacciones_pg)
    hoja_tamano(wb, tamano_mdb, tamano_pg)

    salida = os.path.join(RESULTADOS_DIR, "reporte_benchmark.xlsx")
    wb.save(salida)
    print(f"Excel generado en: {salida}")


if __name__ == "__main__":
    main()
