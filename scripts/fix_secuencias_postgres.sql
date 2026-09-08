SELECT setval('categorias_id_seq', COALESCE((SELECT MAX(id) FROM categorias), 1));
SELECT setval('proveedores_id_seq', COALESCE((SELECT MAX(id) FROM proveedores), 1));
SELECT setval('productos_id_seq', COALESCE((SELECT MAX(id) FROM productos), 1));
SELECT setval('clientes_id_seq', COALESCE((SELECT MAX(id) FROM clientes), 1));
SELECT setval('direcciones_id_seq', COALESCE((SELECT MAX(id) FROM direcciones), 1));
SELECT setval('pedidos_id_seq', COALESCE((SELECT MAX(id) FROM pedidos), 1));
SELECT setval('detalle_pedidos_id_seq', COALESCE((SELECT MAX(id) FROM detalle_pedidos), 1));
SELECT setval('pagos_id_seq', COALESCE((SELECT MAX(id) FROM pagos), 1));