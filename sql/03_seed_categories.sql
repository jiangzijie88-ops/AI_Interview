-- 第三步：为全新数据库添加岗位和知识点，与 data/questions_example.json 的 ID 对应。
-- 仅在首次初始化时执行。重复执行会因主键或名称重复报错，不覆盖已有分类。
-- 已有数据请先查询并核对，不要用 REPLACE 或删除旧分类的方式强行套用编号。
USE ai_interview;
SET NAMES utf8mb4;

-- 分类写入使用事务。若任意 INSERT 报错，停止执行并手动 ROLLBACK，
-- 不要继续执行 COMMIT；检查已有编号后再处理。
START TRANSACTION;

-- 岗位：一题可关联多个岗位，关联关系由导入题库时写入。
INSERT INTO job_roles (id, name) VALUES
(1, 'Python 后端'),
(2, 'AI 应用开发');

-- 知识点：编号必须与示例 JSON 的 knowledge_point_ids 对应。
INSERT INTO knowledge_points (id, name) VALUES
(1, 'Python 基础'),
(2, 'SQL 与 MySQL'),
(3, 'FastAPI'),
(4, 'Streamlit'),
(5, 'LangChain'),
(6, 'LangGraph'),
(7, 'Agent 开发'),
(8, 'RAG');

COMMIT;

-- 核对结果：应有两个岗位、八个知识点。
SELECT id, name FROM job_roles ORDER BY id;
SELECT id, name FROM knowledge_points ORDER BY id;

-- 本文件不创建管理员、不导入题目、不插入真实用户信息。
-- 请在网页注册账号，再运行 python -m backend.init_admin。
-- 题目由管理员上传 data/questions_example.json，导入后检查并审核。
