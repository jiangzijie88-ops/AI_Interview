-- 第一步：创建项目数据库。使用具有 CREATE 权限的 MySQL 账号执行。
-- 若使用其他库名，请同时修改这三个 SQL 文件中的库名和根目录 .env 的 DB_NAME。
-- IF NOT EXISTS 表示数据库已经存在时不重复创建，不会删除原数据。
-- utf8mb4 支持中文和 Emoji；业务表使用 InnoDB 以支持事务和外键。
CREATE DATABASE IF NOT EXISTS ai_interview CHARACTER SET utf8mb4;

-- 切换到项目数据库，后续不要在 mysql 系统库中建业务表。
USE ai_interview;
SET NAMES utf8mb4;

-- 成功时应返回 ai_interview。
SELECT DATABASE() AS current_database;
