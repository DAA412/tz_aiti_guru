SELECT
    parent.name AS "Категория",
    COUNT(child.id) AS "Количество детей 1-го уровня"
FROM categories AS parent
LEFT JOIN categories AS child ON (child.left_key > parent.left_key AND child.right_key < parent.right_key AND child.level = parent.level + 1)
GROUP BY parent.id, parent.name
HAVING COUNT(child.id) > 0
ORDER BY parent.name;