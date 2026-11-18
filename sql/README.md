# 数据库初始化说明

本目录为首次复现项目提供 MySQL 数据库、全部 15 张业务表和基础分类。表结构依据当前 `backend/models` 定义编译生成，包含主键、外键、唯一约束及模型定义的索引。建议使用 MySQL 8.x；未在新建 MySQL 实例执行验收。

## 执行顺序

先启动 MySQL，使用 SQLTools 或 MySQL Workbench 连接。依次打开并完整执行：

1. `01_create_database.sql`：创建并选择 `ai_interview`。
2. `02_create_tables.sql`：按依赖顺序创建全部业务表。
3. `03_seed_categories.sql`：插入示例题库使用的岗位、知识点。

SQLTools 中注意选择正确连接并执行整个文件，不要只运行光标所在的一句。各文件都显式指定库名。没有创建数据库权限时，让数据库管理员创建库，再执行后两个文件。

如果偏好 MySQL 命令行，可连接后执行（将路径替换为自己的项目路径，使用正斜杠）：

```sql
SOURCE D:/AIProgects/GitProjects/AI_Interview/sql/01_create_database.sql;
SOURCE D:/AIProgects/GitProjects/AI_Interview/sql/02_create_tables.sql;
SOURCE D:/AIProgects/GitProjects/AI_Interview/sql/03_seed_categories.sql;
```

`SOURCE` 是 MySQL 客户端命令，不要当成普通 SQL 发给 SQLTools。

## 表之间的业务关系

| 表 | 用途 |
| --- | --- |
| users | 注册账号、密码哈希、昵称、角色 |
| job_roles、knowledge_points | 岗位和知识点分类 |
| questions | 公共题库 |
| question_job_roles、question_knowledge_points | 题库与分类的多对多关系 |
| interview_sessions | 某用户的一场练习及配置快照 |
| interview_questions | 练习内的题目快照，保留创建时内容 |
| interview_answers | 对题目快照的正式回答 |
| interview_feedbacks | 主回答点评 |
| interview_followups | 针对主回答生成的追问 |
| interview_followup_answers | 追问回答 |
| interview_followup_feedbacks | 追问回答点评 |
| interview_reports | 整场练习报告 |
| knowledge_documents | 参考资料正文、来源和审核版本 |

外键含义示例：`interview_answers.question_record_id` 指向 `interview_questions.id`，是本场练习中的题目快照编号，不是公共题库编号。具体外键关系已逐表标注在建表文件中。

## 默认值、约束与时间

- 模型中的 `default=` 是 SQLAlchemy 在写入时补充的值，不等于数据库端 `DEFAULT`。建表文件保留这一行为并在字段注释中写明，避免 SQL 与模型不一致。
- 直接通过 SQL 插入业务数据时，需要自己填写必填字段；建议使用前端和接口新增用户、题目、练习等记录。
- 时间由业务代码填写，项目约定使用 UTC；未新增数据库自动更新时间机制。
- 自增 ID 不保证连续，删除或失败的事务可能产生空号。
- 唯一约束用于防止重复关系、重复正式回答或重复提交编号等，不能随意删除。
- 未配置级联删除的外键保留原行为，删除被引用记录会受到约束。

## 完成 SQL 初始化后

1. 配置根目录 `.env`，使 `DB_NAME`、账号、端口与实际数据库一致。
2. 根据根目录 README 安装依赖并启动前后端。
3. 在网页注册，再运行 `python -m backend.init_admin`，输入已有用户名设置管理员。
4. 管理员导入 `data/questions_example.json`，检查并审核题目；重复导入会重复新增。
5. 按需导入 `data/documents` 中的资料，审核通过后重建索引。

SQL 不提供账号密码、API Key、真实用户、问答记录或 AI 结果。LangGraph SQLite 检查点和 FAISS 索引属于本地运行数据，不在 MySQL 中建对应表；按程序运行流程创建即可。

## 已有数据库与后续更新

`CREATE TABLE IF NOT EXISTS` 仅跳过已有表，不会检查或更新字段。不要把初始化文件当作升级脚本；更改模型后应同步维护本目录，旧数据库需要另行编写针对性的结构变更语句。

分类初始化不做覆盖更新。执行报错时先停止；若分类事务未提交，执行 `ROLLBACK`，检查编号后再处理。MySQL DDL 有隐式提交行为，不能靠回滚撤销整个建表过程，因此本目录没有自动删库或重置数据操作。

## 手动检查

```sql
USE ai_interview;
SHOW TABLES;  -- 全新项目库应包含上述 15 张业务表
SHOW CREATE TABLE interview_answers;  -- 检查字段与外键
SELECT id, name FROM job_roles ORDER BY id;
SELECT id, name FROM knowledge_points ORDER BY id;
```
