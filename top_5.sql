CREATE VIEW top_5_products_last_month AS
SELECT
    p.name AS "Наименование товара",
    (SELECT name FROM categories WHERE left_key <= c.left_key AND right_key >= c.right_key AND level = 1 LIMIT 1) AS "Категория 1-го уровня",
    SUM(oi.quantity) AS "Общее количество проданных штук"
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
JOIN products p ON oi.product_id = p.id
JOIN categories c ON p.category_id = c.id
WHERE o.order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
  AND o.order_date < DATE_TRUNC('month', CURRENT_DATE)
GROUP BY p.id, p.name, c.left_key, c.right_key
ORDER BY "Общее количество проданных штук" DESC
LIMIT 5;


-- Запрос будет тормозить при больших объемах данных из-за:
-- Сканирование больших таблиц orders и order_items по временному диапазону.
-- Сложное вычисление категории 1-го уровня для каждого товара через подзапрос, который также читает таблицу categories.
--
-- Предложения по оптимизации:
-- Денормализация для ускорения отчетов:
--
-- Добавить в таблицу products прямое поле root_category_id, которое будет хранить ID категории 1-го уровня. Это избавит от дорогостоящего подзапроса к categories в отчетах.
-- ALTER TABLE products ADD COLUMN root_category_id INTEGER;
--
-- Индексы:
-- CREATE INDEX idx_orders_order_date ON orders(order_date); — Быстрое нахождение заказов за период.
-- CREATE INDEX idx_order_items_order_id ON order_items(order_id); — Быстрое соединение с заказами.
-- Составной индекс для order_items: (product_id, quantity) может ускорить агрегацию.
--
-- Партиционирование таблиц orders и order_items по order_date (например, по месяцам). Запрос будет читать только одну партицию (последний месяц), а не всю таблицу.
--
-- Материализованное представление (Materialized View):
-- Если данные в отчете могут быть не самыми свежими (допустима задержка в несколько часов), можно создать материализованное представление и обновлять его по расписанию (например, ночью). Это радикально ускорит выполнение запроса.
-- CREATE MATERIALIZED VIEW mv_top_products_monthly AS
-- WITH DATA;
-- -- Обновление по расписанию: REFRESH MATERIALIZED VIEW mv_top_products_monthly;
-- Вынос агрегированных данных в отдельную таблицу (OLAP-куб):
--
-- Для систем с тысячами заказов в день лучшим решением будет построение ETL-процесса, который будет считать продажи за день и складывать готовые цифры в таблицу product_sales_daily (product_id, date, total_quantity). Итоговый отчет будет простым и быстрым SELECT ... FROM product_sales_daily WHERE date BETWEEN ....