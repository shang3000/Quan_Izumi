# MySQL 常用语句整理

> MySQL 数据库常用 SQL 语句参考手册

---

## 目录

1. [数据库操作](#数据库操作)
2. [表操作](#表操作)
3. [数据操作](#数据操作)
4. [查询语句](#查询语句)
5. [索引操作](#索引操作)
6. [视图操作](#视图操作)
7. [存储过程与函数](#存储过程与函数)
8. [事务控制](#事务控制)
9. [用户权限管理](#用户权限管理)
10. [常用函数](#常用函数)

---

## 数据库操作

### 创建数据库

```sql
CREATE DATABASE 数据库名;

CREATE DATABASE 数据库名 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

CREATE DATABASE IF NOT EXISTS 数据库名;
```

### 查看数据库

```sql
SHOW DATABASES;

SHOW CREATE DATABASE 数据库名;
```

### 选择数据库

```sql
USE 数据库名;
```

### 修改数据库

```sql
ALTER DATABASE 数据库名 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 删除数据库

```sql
DROP DATABASE 数据库名;

DROP DATABASE IF EXISTS 数据库名;
```

---

## 表操作

### 创建表

```sql
CREATE TABLE 表名 (
    字段名1 数据类型 [约束条件],
    字段名2 数据类型 [约束条件],
    ...
    [表级约束]
);

CREATE TABLE IF NOT EXISTS 表名 (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    age INT DEFAULT 18,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 常用数据类型

| 类型 | 说明 | 示例 |
|------|------|------|
| INT | 整数 | INT(11) |
| BIGINT | 大整数 | BIGINT(20) |
| DECIMAL | 精确小数 | DECIMAL(10,2) |
| FLOAT | 浮点数 | FLOAT(10,2) |
| DOUBLE | 双精度浮点 | DOUBLE(10,2) |
| VARCHAR | 变长字符串 | VARCHAR(255) |
| CHAR | 定长字符串 | CHAR(10) |
| TEXT | 长文本 | TEXT |
| DATE | 日期 | DATE |
| DATETIME | 日期时间 | DATETIME |
| TIMESTAMP | 时间戳 | TIMESTAMP |
| BOOLEAN | 布尔值 | BOOLEAN |

### 常用约束

| 约束 | 说明 | 示例 |
|------|------|------|
| PRIMARY KEY | 主键 | PRIMARY KEY |
| FOREIGN KEY | 外键 | FOREIGN KEY (id) REFERENCES 表名(id) |
| UNIQUE | 唯一约束 | UNIQUE |
| NOT NULL | 非空约束 | NOT NULL |
| DEFAULT | 默认值 | DEFAULT 0 |
| AUTO_INCREMENT | 自增 | AUTO_INCREMENT |
| CHECK | 检查约束 | CHECK (age >= 18) |

### 查看表

```sql
SHOW TABLES;

SHOW CREATE TABLE 表名;

DESCRIBE 表名;

DESC 表名;
```

### 修改表结构

```sql
-- 添加列
ALTER TABLE 表名 ADD COLUMN 字段名 数据类型;

ALTER TABLE 表名 ADD COLUMN 字段名 数据类型 AFTER 字段名;

ALTER TABLE 表名 ADD COLUMN 字段名 数据类型 FIRST;

-- 修改列
ALTER TABLE 表名 MODIFY COLUMN 字段名 新数据类型;

ALTER TABLE 表名 CHANGE COLUMN 旧字段名 新字段名 新数据类型;

-- 删除列
ALTER TABLE 表名 DROP COLUMN 字段名;

-- 添加主键
ALTER TABLE 表名 ADD PRIMARY KEY (字段名);

-- 删除主键
ALTER TABLE 表名 DROP PRIMARY KEY;

-- 添加外键
ALTER TABLE 表名 ADD CONSTRAINT 外键名 FOREIGN KEY (字段名) REFERENCES 关联表(关联字段);

-- 删除外键
ALTER TABLE 表名 DROP FOREIGN KEY 外键名;

-- 添加索引
ALTER TABLE 表名 ADD INDEX 索引名 (字段名);

-- 删除索引
ALTER TABLE 表名 DROP INDEX 索引名;
```

### 重命名表

```sql
ALTER TABLE 旧表名 RENAME TO 新表名;

RENAME TABLE 旧表名 TO 新表名;
```

### 删除表

```sql
DROP TABLE 表名;

DROP TABLE IF EXISTS 表名;

-- 清空表数据，保留表结构
TRUNCATE TABLE 表名;
```

---

## 数据操作

### 插入数据

```sql
-- 插入单条数据
INSERT INTO 表名 (字段1, 字段2, ...) VALUES (值1, 值2, ...);

-- 插入多条数据
INSERT INTO 表名 (字段1, 字段2, ...) VALUES
    (值1, 值2, ...),
    (值3, 值4, ...),
    (值5, 值6, ...);

-- 插入所有字段
INSERT INTO 表名 VALUES (值1, 值2, ...);

-- 从另一个表插入数据
INSERT INTO 表名 (字段1, 字段2, ...)
SELECT 字段1, 字段2, ... FROM 另一个表名;
```

### 更新数据

```sql
-- 更新单条数据
UPDATE 表名 SET 字段1 = 值1, 字段2 = 值2 WHERE 条件;

-- 更新多条数据
UPDATE 表名 SET 字段 = 值 WHERE 条件;

-- 批量更新
UPDATE 表名 SET 字段 = CASE
    WHEN 条件1 THEN 值1
    WHEN 条件2 THEN 值2
    ELSE 字段
END;
```

### 删除数据

```sql
-- 删除指定数据
DELETE FROM 表名 WHERE 条件;

-- 删除所有数据（不推荐，使用 TRUNCATE 更快）
DELETE FROM 表名;

-- 删除重复数据
DELETE t1 FROM 表名 t1
INNER JOIN 表名 t2
WHERE t1.id > t2.id AND t1.字段 = t2.字段;
```

---

## 查询语句

### 基本查询

```sql
-- 查询所有字段
SELECT * FROM 表名;

-- 查询指定字段
SELECT 字段1, 字段2, ... FROM 表名;

-- 查询并去重
SELECT DISTINCT 字段 FROM 表名;

-- 查询并限制数量
SELECT * FROM 表名 LIMIT 10;

-- 查询并分页
SELECT * FROM 表名 LIMIT 10 OFFSET 20;
SELECT * FROM 表名 LIMIT 20, 10;

-- 查询并排序
SELECT * FROM 表名 ORDER BY 字段 ASC;
SELECT * FROM 表名 ORDER BY 字段 DESC;
SELECT * FROM 表名 ORDER BY 字段1 ASC, 字段2 DESC;
```

### 条件查询

```sql
-- WHERE 条件
SELECT * FROM 表名 WHERE 条件;

-- 比较运算符
SELECT * FROM 表名 WHERE 字段 = 值;
SELECT * FROM 表名 WHERE 字段 != 值;
SELECT * FROM 表名 WHERE 字段 > 值;
SELECT * FROM 表名 WHERE 字段 >= 值;
SELECT * FROM 表名 WHERE 字段 < 值;
SELECT * FROM 表名 WHERE 字段 <= 值;

-- 逻辑运算符
SELECT * FROM 表名 WHERE 条件1 AND 条件2;
SELECT * FROM 表名 WHERE 条件1 OR 条件2;
SELECT * FROM 表名 WHERE NOT 条件;
SELECT * FROM 表名 WHERE 字段 IN (值1, 值2, ...);
SELECT * FROM 表名 WHERE 字段 NOT IN (值1, 值2, ...);
SELECT * FROM 表名 WHERE 字段 BETWEEN 值1 AND 值2;
SELECT * FROM 表名 WHERE 字段 NOT BETWEEN 值1 AND 值2;

-- 模糊查询
SELECT * FROM 表名 WHERE 字段 LIKE '模式';
SELECT * FROM 表名 WHERE 字段 LIKE 'abc%';  -- 以 abc 开头
SELECT * FROM 表名 WHERE 字段 LIKE '%abc';  -- 以 abc 结尾
SELECT * FROM 表名 WHERE 字段 LIKE '%abc%'; -- 包含 abc
SELECT * FROM 表名 WHERE 字段 LIKE '_bc%';  -- 第二个字符是 bc

-- NULL 值查询
SELECT * FROM 表名 WHERE 字段 IS NULL;
SELECT * FROM 表名 WHERE 字段 IS NOT NULL;
```

### 聚合函数

```sql
-- COUNT 统计数量
SELECT COUNT(*) FROM 表名;
SELECT COUNT(字段) FROM 表名;
SELECT COUNT(DISTINCT 字段) FROM 表名;

-- SUM 求和
SELECT SUM(字段) FROM 表名;

-- AVG 平均值
SELECT AVG(字段) FROM 表名;

-- MAX 最大值
SELECT MAX(字段) FROM 表名;

-- MIN 最小值
SELECT MIN(字段) FROM 表名;

-- GROUP BY 分组
SELECT 字段, COUNT(*) FROM 表名 GROUP BY 字段;
SELECT 字段1, 字段2, SUM(字段3) FROM 表名 GROUP BY 字段1, 字段2;

-- HAVING 分组后筛选
SELECT 字段, COUNT(*) FROM 表名 GROUP BY 字段 HAVING COUNT(*) > 10;

-- WITH ROLLUP 生成汇总行
SELECT 字段, SUM(金额) FROM 表名 GROUP BY 字段 WITH ROLLUP;
```

### 连接查询

```sql
-- 内连接
SELECT * FROM 表1 INNER JOIN 表2 ON 表1.字段 = 表2.字段;

-- 左连接
SELECT * FROM 表1 LEFT JOIN 表2 ON 表1.字段 = 表2.字段;

-- 右连接
SELECT * FROM 表1 RIGHT JOIN 表2 ON 表1.字段 = 表2.字段;

-- 全连接（MySQL 不支持，使用 UNION）
SELECT * FROM 表1 LEFT JOIN 表2 ON 表1.字段 = 表2.字段
UNION
SELECT * FROM 表1 RIGHT JOIN 表2 ON 表1.字段 = 表2.字段;

-- 自连接
SELECT t1.字段 FROM 表名 t1 INNER JOIN 表名 t2 ON t1.字段 = t2.字段;

-- 多表连接
SELECT * FROM 表1
INNER JOIN 表2 ON 表1.字段 = 表2.字段
INNER JOIN 表3 ON 表2.字段 = 表3.字段;
```

### 子查询

```sql
-- 标量子查询
SELECT * FROM 表名 WHERE 字段 = (SELECT 字段 FROM 表名 WHERE 条件);

-- 列子查询
SELECT * FROM 表名 WHERE 字段 IN (SELECT 字段 FROM 表名 WHERE 条件);

-- 行子查询
SELECT * FROM 表名 WHERE (字段1, 字段2) = (SELECT 字段1, 字段2 FROM 表名 WHERE 条件);

-- 表子查询
SELECT * FROM (SELECT * FROM 表名 WHERE 条件) AS 别名;

-- EXISTS 子查询
SELECT * FROM 表名 WHERE EXISTS (SELECT 1 FROM 表名 WHERE 条件);

-- NOT EXISTS 子查询
SELECT * FROM 表名 WHERE NOT EXISTS (SELECT 1 FROM 表名 WHERE 条件);
```

### UNION 操作

```sql
-- 合并查询结果（去重）
SELECT 字段 FROM 表1 UNION SELECT 字段 FROM 表2;

-- 合并查询结果（不去重）
SELECT 字段 FROM 表1 UNION ALL SELECT 字段 FROM 表2;
```

---

## 索引操作

### 创建索引

```sql
-- 普通索引
CREATE INDEX 索引名 ON 表名 (字段名);

-- 唯一索引
CREATE UNIQUE INDEX 索引名 ON 表名 (字段名);

-- 组合索引
CREATE INDEX 索引名 ON 表名 (字段名1, 字段名2);

-- 全文索引
CREATE FULLTEXT INDEX 索引名 ON 表名 (字段名);

-- 空间索引
CREATE SPATIAL INDEX 索引名 ON 表名 (字段名);

-- 使用 ALTER TABLE 创建索引
ALTER TABLE 表名 ADD INDEX 索引名 (字段名);
ALTER TABLE 表名 ADD UNIQUE INDEX 索引名 (字段名);
```

### 查看索引

```sql
SHOW INDEX FROM 表名;

SHOW INDEX FROM 表名 WHERE Key_name = '索引名';
```

### 删除索引

```sql
DROP INDEX 索引名 ON 表名;

ALTER TABLE 表名 DROP INDEX 索引名;
```

### 索引优化建议

- WHERE、ORDER BY、GROUP BY 的字段适合建索引
- 频繁更新的字段不适合建索引
- 区分度高的字段适合建索引
- 组合索引遵循最左前缀原则
- 避免在索引列上进行函数运算

---

## 视图操作

### 创建视图

```sql
CREATE VIEW 视图名 AS SELECT 语句;

CREATE OR REPLACE VIEW 视图名 AS SELECT 语句;

CREATE VIEW 视图名 (字段1, 字段2, ...) AS SELECT 语句;
```

### 查看视图

```sql
SHOW CREATE VIEW 视图名;

SHOW FULL TABLES WHERE TABLE_TYPE = 'VIEW';
```

### 修改视图

```sql
ALTER VIEW 视图名 AS SELECT 语句;
```

### 删除视图

```sql
DROP VIEW 视图名;

DROP VIEW IF EXISTS 视图名;
```

---

## 存储过程与函数

### 创建存储过程

```sql
DELIMITER //
CREATE PROCEDURE 存储过程名(参数列表)
BEGIN
    SQL语句;
END //
DELIMITER ;

-- 示例
DELIMITER //
CREATE PROCEDURE GetUserById(IN user_id INT)
BEGIN
    SELECT * FROM users WHERE id = user_id;
END //
DELIMITER ;
```

### 调用存储过程

```sql
CALL 存储过程名(参数);

CALL GetUserById(1);
```

### 删除存储过程

```sql
DROP PROCEDURE 存储过程名;

DROP PROCEDURE IF EXISTS 存储过程名;
```

### 创建函数

```sql
DELIMITER //
CREATE FUNCTION 函数名(参数列表) RETURNS 返回类型
BEGIN
    SQL语句;
    RETURN 返回值;
END //
DELIMITER ;

-- 示例
DELIMITER //
CREATE FUNCTION GetUserCount() RETURNS INT
BEGIN
    DECLARE user_count INT;
    SELECT COUNT(*) INTO user_count FROM users;
    RETURN user_count;
END //
DELIMITER ;
```

### 调用函数

```sql
SELECT 函数名(参数);

SELECT GetUserCount();
```

### 删除函数

```sql
DROP FUNCTION 函数名;

DROP FUNCTION IF EXISTS 函数名;
```

### 查看存储过程和函数

```sql
SHOW PROCEDURE STATUS;

SHOW FUNCTION STATUS;

SHOW CREATE PROCEDURE 存储过程名;

SHOW CREATE FUNCTION 函数名;
```

---

## 事务控制

### 开启事务

```sql
START TRANSACTION;

BEGIN;
```

### 提交事务

```sql
COMMIT;
```

### 回滚事务

```sql
ROLLBACK;
```

### 事务示例

```sql
START TRANSACTION;

UPDATE 账户表 SET 余额 = 余额 - 100 WHERE 用户 = 'A';
UPDATE 账户表 SET 余额 = 余额 + 100 WHERE 用户 = 'B';

COMMIT;  -- 提交事务

-- 或
ROLLBACK;  -- 回滚事务
```

### 事务隔离级别

```sql
-- 查看隔离级别
SELECT @@transaction_isolation;

-- 设置隔离级别
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

### 自动提交控制

```sql
-- 查看自动提交状态
SELECT @@autocommit;

-- 开启自动提交
SET autocommit = 1;

-- 关闭自动提交
SET autocommit = 0;
```

---

## 用户权限管理

### 创建用户

```sql
CREATE USER '用户名'@'主机' IDENTIFIED BY '密码';

CREATE USER '用户名'@'%' IDENTIFIED BY '密码';

CREATE USER '用户名'@'localhost' IDENTIFIED BY '密码';

CREATE USER '用户名'@'192.168.1.%' IDENTIFIED BY '密码';
```

### 修改用户密码

```sql
ALTER USER '用户名'@'主机' IDENTIFIED BY '新密码';

SET PASSWORD FOR '用户名'@'主机' = PASSWORD('新密码');
```

### 删除用户

```sql
DROP USER '用户名'@'主机';

DROP USER IF EXISTS '用户名'@'主机';
```

### 授予权限

```sql
-- 授予所有权限
GRANT ALL PRIVILEGES ON 数据库名.* TO '用户名'@'主机';

-- 授予指定权限
GRANT SELECT, INSERT, UPDATE, DELETE ON 数据库名.* TO '用户名'@'主机';

-- 授予所有数据库权限
GRANT ALL PRIVILEGES ON *.* TO '用户名'@'主机';

-- 授予创建用户权限
GRANT CREATE USER ON *.* TO '用户名'@'主机';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 撤销权限

```sql
REVOKE ALL PRIVILEGES ON 数据库名.* FROM '用户名'@'主机';

REVOKE SELECT, INSERT, UPDATE ON 数据库名.* FROM '用户名'@'主机';
```

### 查看权限

```sql
SHOW GRANTS FOR '用户名'@'主机';

SHOW GRANTS FOR CURRENT_USER();
```

---

## 常用函数

### 字符串函数

```sql
-- 字符串长度
SELECT LENGTH('hello');  -- 5

-- 字符串拼接
SELECT CONCAT('hello', ' ', 'world');  -- hello world

-- 大小写转换
SELECT UPPER('hello');  -- HELLO
SELECT LOWER('HELLO');  -- hello

-- 去除空格
SELECT TRIM('  hello  ');  -- hello
SELECT LTRIM('  hello');  -- hello
SELECT RTRIM('hello  ');  -- hello

-- 截取字符串
SELECT SUBSTRING('hello', 1, 3);  -- hel
SELECT LEFT('hello', 2);  -- he
SELECT RIGHT('hello', 2);  -- lo

-- 替换字符串
SELECT REPLACE('hello world', 'world', 'mysql');  -- hello mysql

-- 查找位置
SELECT INSTR('hello world', 'world');  -- 7
SELECT LOCATE('world', 'hello world');  -- 7

-- 重复字符串
SELECT REPEAT('hello', 3);  -- hellohellohello

-- 反转字符串
SELECT REVERSE('hello');  -- olleh

-- 字符串转数字
SELECT CAST('123' AS SIGNED);  -- 123
SELECT CONVERT('123', SIGNED);  -- 123
```

### 数值函数

```sql
-- 绝对值
SELECT ABS(-10);  -- 10

-- 向上取整
SELECT CEIL(3.14);  -- 4

-- 向下取整
SELECT FLOOR(3.14);  -- 3

-- 四舍五入
SELECT ROUND(3.14);  -- 3
SELECT ROUND(3.14, 1);  -- 3.1

-- 取模
SELECT MOD(10, 3);  -- 1

-- 幂运算
SELECT POW(2, 3);  -- 8
SELECT POWER(2, 3);  -- 8

-- 平方根
SELECT SQRT(16);  -- 4

-- 随机数
SELECT RAND();  -- 0-1 之间的随机数
SELECT RAND() * 100;  -- 0-100 之间的随机数

-- 格式化数字
SELECT FORMAT(1234.5678, 2);  -- 1,234.57
```

### 日期时间函数

```sql
-- 当前日期时间
SELECT NOW();  -- 2024-01-01 12:00:00
SELECT CURRENT_TIMESTAMP();  -- 2024-01-01 12:00:00
SELECT CURRENT_DATE();  -- 2024-01-01
SELECT CURRENT_TIME();  -- 12:00:00

-- 日期加减
SELECT DATE_ADD(NOW(), INTERVAL 1 DAY);  -- 加1天
SELECT DATE_SUB(NOW(), INTERVAL 1 DAY);  -- 减1天
SELECT DATE_ADD(NOW(), INTERVAL 1 MONTH);  -- 加1月
SELECT DATE_ADD(NOW(), INTERVAL 1 YEAR);  -- 加1年

-- 日期差
SELECT DATEDIFF('2024-01-10', '2024-01-01');  -- 9

-- 日期格式化
SELECT DATE_FORMAT(NOW(), '%Y-%m-%d');  -- 2024-01-01
SELECT DATE_FORMAT(NOW(), '%Y年%m月%d日');  -- 2024年01月01日

-- 字符串转日期
SELECT STR_TO_DATE('2024-01-01', '%Y-%m-%d');  -- 2024-01-01

-- 提取日期部分
SELECT YEAR(NOW());  -- 2024
SELECT MONTH(NOW());  -- 1
SELECT DAY(NOW());  -- 1
SELECT HOUR(NOW());  -- 12
SELECT MINUTE(NOW());  -- 0
SELECT SECOND(NOW());  -- 0

-- 星期几
SELECT DAYOFWEEK(NOW());  -- 1-7 (1=周日)
SELECT DAYNAME(NOW());  -- Monday
SELECT WEEKDAY(NOW());  -- 0-6 (0=周一)

-- 一年中的第几天
SELECT DAYOFYEAR(NOW());  -- 1

-- 一年中的第几周
SELECT WEEK(NOW());  -- 1

-- 时间戳
SELECT UNIX_TIMESTAMP();  -- 1704067200
SELECT FROM_UNIX_TIMESTAMP(1704067200);  -- 2024-01-01 00:00:00
```

### 条件函数

```sql
-- IF 函数
SELECT IF(1 > 0, '真', '假');  -- 真

-- IFNULL 函数
SELECT IFNULL(NULL, '默认值');  -- 默认值
SELECT IFNULL('值', '默认值');  -- 值

-- NULLIF 函数
SELECT NULLIF(1, 1);  -- NULL
SELECT NULLIF(1, 2);  -- 1

-- CASE WHEN 语句
SELECT 
    CASE 
        WHEN 成绩 >= 90 THEN '优秀'
        WHEN 成绩 >= 80 THEN '良好'
        WHEN 成绩 >= 60 THEN '及格'
        ELSE '不及格'
    END AS 等级
FROM 成绩表;
```

### 其他函数

```sql
-- 数据库信息
SELECT DATABASE();  -- 当前数据库名
SELECT USER();  -- 当前用户
SELECT VERSION();  -- MySQL 版本

-- UUID
SELECT UUID();  -- 生成唯一标识符

-- MD5 加密
SELECT MD5('password');  -- 5f4dcc3b5aa765d61d8327deb882cf99

-- SHA1 加密
SELECT SHA1('password');  -- 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8

-- 类型转换
SELECT CAST('123' AS SIGNED);  -- 123
SELECT CAST('123.45' AS DECIMAL(10,2));  -- 123.45
SELECT CAST('2024-01-01' AS DATE);  -- 2024-01-01
```

---

## 实用技巧

### 批量插入优化

```sql
-- 使用 INSERT IGNORE 忽略重复
INSERT IGNORE INTO 表名 (字段) VALUES (值);

-- 使用 REPLACE INTO 替换重复
REPLACE INTO 表名 (字段) VALUES (值);

-- 使用 ON DUPLICATE KEY UPDATE 更新重复
INSERT INTO 表名 (字段1, 字段2, 字段3) VALUES (值1, 值2, 值3)
ON DUPLICATE KEY UPDATE 字段2 = 值2, 字段3 = 值3;
```

### 分页优化

```sql
-- 传统分页（数据量大时性能差）
SELECT * FROM 表名 LIMIT 100000, 10;

-- 使用 WHERE 优化分页
SELECT * FROM 表名 WHERE id > 100000 LIMIT 10;

-- 使用 JOIN 优化分页
SELECT t1.* FROM 表名 t1
INNER JOIN (SELECT id FROM 表名 ORDER BY id LIMIT 100000, 10) t2
ON t1.id = t2.id;
```

### 查询优化

```sql
-- 使用 EXPLAIN 分析查询
EXPLAIN SELECT * FROM 表名 WHERE 字段 = 值;

-- 使用索引提示
SELECT * FROM 表名 USE INDEX (索引名) WHERE 字段 = 值;
SELECT * FROM 表名 FORCE INDEX (索引名) WHERE 字段 = 值;
SELECT * FROM 表名 IGNORE INDEX (索引名) WHERE 字段 = 值;

-- 使用 SQL 缓存
SELECT SQL_CACHE * FROM 表名 WHERE 字段 = 值;
SELECT SQL_NO_CACHE * FROM 表名 WHERE 字段 = 值;
```

### 数据备份与恢复

```sql
-- 备份数据库（命令行）
mysqldump -u 用户名 -p 数据库名 > 备份文件.sql

-- 恢复数据库（命令行）
mysql -u 用户名 -p 数据库名 < 备份文件.sql

-- 导出表结构
mysqldump -u 用户名 -p -d 数据库名 > 结构.sql

-- 导出表数据
mysqldump -u 用户名 -p -t 数据库名 > 数据.sql
```

---

## 常见问题解决

### 查看当前连接

```sql
SHOW PROCESSLIST;

SHOW FULL PROCESSLIST;
```

### 杀死连接

```sql
KILL 连接ID;
```

### 查看表大小

```sql
SELECT 
    table_name AS '表名',
    table_rows AS '行数',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS '大小(MB)'
FROM information_schema.TABLES
WHERE table_schema = '数据库名'
ORDER BY (data_length + index_length) DESC;
```

### 查看数据库大小

```sql
SELECT 
    table_schema AS '数据库名',
    SUM(table_rows) AS '总行数',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS '总大小(MB)'
FROM information_schema.TABLES
GROUP BY table_schema
ORDER BY (data_length + index_length) DESC;
```

### 查看索引使用情况

```sql
SELECT 
    table_name,
    index_name,
    column_name,
    seq_in_index
FROM information_schema.STATISTICS
WHERE table_schema = '数据库名'
ORDER BY table_name, index_name, seq_in_index;
```

---

## 注意事项

1. **SQL 注入防护**：使用参数化查询，避免直接拼接 SQL
2. **索引优化**：合理创建索引，避免过度索引
3. **事务使用**：重要操作使用事务，确保数据一致性
4. **定期备份**：定期备份数据库，防止数据丢失
5. **权限管理**：遵循最小权限原则，避免使用 root 账号
6. **性能监控**：定期监控慢查询，优化 SQL 语句
7. **字符集**：统一使用 utf8mb4 字符集，支持 emoji
8. **存储引擎**：推荐使用 InnoDB，支持事务和外键

---

## 参考资料

- [MySQL 官方文档](https://dev.mysql.com/doc/)
- [MySQL 8.0 参考手册](https://dev.mysql.com/doc/refman/8.0/en/)
