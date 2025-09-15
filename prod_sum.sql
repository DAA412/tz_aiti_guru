SELECT
    c.name AS "Наименование клиента",
    COALESCE(SUM(oi.quantity * oi.price), 0) AS "Сумма"
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
LEFT JOIN order_items oi ON oi.order_id = o.id
GROUP BY c.id, c.name
ORDER BY "Сумма" DESC;