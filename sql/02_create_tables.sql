-- 全部业务表，由当前 SQLAlchemy 模型编译生成。建议 MySQL 8.x。
-- 先执行 01_create_database.sql，再完整执行本文件。
-- IF NOT EXISTS 只跳过已存在的表，不会修复旧表结构；本文件不是迁移脚本。
-- 不包含用户数据、密码、回答或模型生成结果。
-- default= 属于 Python ORM 默认值，下面用注释注明；未擅自转为数据库 DEFAULT。
-- 直接写 SQL 时须显式填写这些必填字段；正常接口写入由 ORM/业务代码处理。
SET NAMES utf8mb4;
USE ai_interview;

-- 1. job_roles：岗位分类：供题库关联和练习选择
-- 字段说明：
--   id：对应表中的整数主键id
--   name：岗位名称:最多50个字符，不为空不重复
CREATE TABLE IF NOT EXISTS job_roles (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. knowledge_documents：RAG 原始资料：正文、来源、审核状态和修订号
-- 字段说明：
--   id：本表记录的唯一编号
--   title：资料标题，例如”FastAPI 异步开发“
--   content：保存完整原文，后续根据它切分文本，建立索引
--   source_url：原始资料的来源链接
--   version_note：适用版本或整理说明
--   status：草稿、已审核、停用；ORM 默认值：'draft'
--   revision：修改资料后增加，用于区分不用版本；ORM 默认值：1
--   created_at：后续由业务函数填写UTC时间
--   updated_at：最后更新时间，由业务代码填写
CREATE TABLE IF NOT EXISTS knowledge_documents (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	title VARCHAR(200) NOT NULL, 
	content LONGTEXT NOT NULL, 
	source_url VARCHAR(1000), 
	version_note VARCHAR(200), 
	status VARCHAR(20) NOT NULL, 
	revision INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. knowledge_points：知识点分类：供题库关联和练习筛选
-- 字段说明：
--   id：对应表中的整数主键id
--   name：知识点名称：最多100个字符，不为空不重复
CREATE TABLE IF NOT EXISTS knowledge_points (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. questions：公共题库：审核通过的题目才能用于创建练习
-- 字段说明：
--   id：题目编号：整数主键
--   content：问题正文
--   difficulty：难度：basic 基础，advanced 进阶；ORM 默认值：'basic'
--   reference_points：回答应覆盖的参考要点
--   common_mistakes：以下三个字段允许没有值
--   followup_direction：类型和可空性见下方定义
--   sources：类型和可空性见下方定义
--   status：状态：draft 草稿，approved 已审核，disabled 禁用；ORM 默认值：'draft'
--   revision：修改号，后续编辑时由业务代码递增；ORM 默认值：1
CREATE TABLE IF NOT EXISTS questions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	content TEXT NOT NULL, 
	difficulty VARCHAR(20) NOT NULL, 
	reference_points TEXT NOT NULL, 
	common_mistakes TEXT, 
	followup_direction TEXT, 
	sources TEXT, 
	status VARCHAR(20) NOT NULL, 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. users：用户账号：保存密码哈希与角色，不保存明文密码
-- 字段说明：
--   id：用户ID，主键，自增
--   username：用户名：50字以内，不能为空不能重复
--   password_hash：保存哈希密码，不保存原始密码
--   nickname：昵称
--   role：角色：普通用户user，管理员admin；ORM 默认值：'user'
CREATE TABLE IF NOT EXISTS users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(50) NOT NULL, 
	password_hash VARCHAR(128) NOT NULL, 
	nickname VARCHAR(50) NOT NULL, 
	`role` VARCHAR(10) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. interview_sessions：用户的一次练习：记录配置快照、状态和时间
-- 字段说明：
--   id：本表记录的唯一编号
--   user_id：练习属于哪个用户，后续由登录身份确认
--   job_role_id：选择的岗位方向
--   difficulty：难度与主问题数量
--   question_count：类型和可空性见下方定义
--   current_position：旧版顺序练习的兼容字段；新版页面选题不依赖它；ORM 默认值：1
--   status：进行中，已完成或提前结束；ORM 默认值：'in_progress'
--   config_snapshot：保存创建时的配置
--   revision：类型和可空性见下方定义；ORM 默认值：1
--   started_at：时间由后续业务代码填写
--   ended_at：类型和可空性见下方定义
-- 外键：本表 user_id → users.id；未配置级联删除。
-- 外键：本表 job_role_id → job_roles.id；未配置级联删除。
CREATE TABLE IF NOT EXISTS interview_sessions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	job_role_id INTEGER NOT NULL, 
	difficulty VARCHAR(20) NOT NULL, 
	question_count INTEGER NOT NULL, 
	current_position INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	config_snapshot JSON NOT NULL, 
	revision INTEGER NOT NULL, 
	started_at DATETIME NOT NULL, 
	ended_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(job_role_id) REFERENCES job_roles (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. question_job_roles：题目与岗位的多对多关系，两个外键共同组成主键
-- 字段说明：
--   question_id：两列共同组成主键：这里的编号引用也有记录，不自动生成
--   job_role_id：类型和可空性见下方定义
-- 外键：本表 question_id → questions.id；未配置级联删除。
-- 外键：本表 job_role_id → job_roles.id；未配置级联删除。
CREATE TABLE IF NOT EXISTS question_job_roles (
	question_id INTEGER NOT NULL, 
	job_role_id INTEGER NOT NULL, 
	PRIMARY KEY (question_id, job_role_id), 
	FOREIGN KEY(question_id) REFERENCES questions (id), 
	FOREIGN KEY(job_role_id) REFERENCES job_roles (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. question_knowledge_points：题目与知识点的多对多关系
-- 字段说明：
--   question_id：两列共同组成主键：这里的编号引用也有记录，不自动生成
--   knowledge_point_id：类型和可空性见下方定义
-- 外键：本表 question_id → questions.id；未配置级联删除。
-- 外键：本表 knowledge_point_id → knowledge_points.id；未配置级联删除。
CREATE TABLE IF NOT EXISTS question_knowledge_points (
	question_id INTEGER NOT NULL, 
	knowledge_point_id INTEGER NOT NULL, 
	PRIMARY KEY (question_id, knowledge_point_id), 
	FOREIGN KEY(question_id) REFERENCES questions (id), 
	FOREIGN KEY(knowledge_point_id) REFERENCES knowledge_points (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. interview_questions：本次练习的题目快照，内容不随公共题库编辑而变化
-- 字段说明：
--   id：快照记录自己的唯一编号
--   session_id：属于哪次练习
--   question_id：快照来源于哪道公共题目
--   position：本次练习中的主问题序号
--   question_revision：创建快照时，来源题目的修订号
--   content：一下字段保存复制后的内容，不随题库自动变化
--   reference_points：回答的参考要点
--   common_mistakes：类型和可空性见下方定义
--   followup_direction：类型和可空性见下方定义
--   sources：类型和可空性见下方定义
--   knowledge_points_snapshot：保存创建时关联的知识点编号和名称
-- 外键：本表 question_id → questions.id；未配置级联删除。
-- 外键：本表 session_id → interview_sessions.id；未配置级联删除。
CREATE TABLE IF NOT EXISTS interview_questions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	session_id INTEGER NOT NULL, 
	question_id INTEGER NOT NULL, 
	position INTEGER NOT NULL, 
	question_revision INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	reference_points TEXT NOT NULL, 
	common_mistakes TEXT, 
	followup_direction TEXT, 
	sources TEXT, 
	knowledge_points_snapshot JSON NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (session_id, position), 
	FOREIGN KEY(session_id) REFERENCES interview_sessions (id), 
	FOREIGN KEY(question_id) REFERENCES questions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. interview_reports：整场练习的总结报告及生成状态
-- 字段说明：
--   id：报告自己的编号
--   session_id：关联练习：一次练习最多保存一条报告记录
--   status：报告生成状态，与练习本身的状态分开；ORM 默认值：'pending'
--   input_snapshot：生成报告时使用的数据
--   report_content：模型生成的结构化报告
--   model_name：类型和可空性见下方定义
--   prompt_version：保存本次生成所使用的提示词版本
--   error_message：类型和可空性见下方定义
--   created_at：后续由业务函数填写UTC时间
--   updated_at：最后更新时间，由业务代码填写
-- 外键：本表 session_id → interview_sessions.id；未配置级联删除。
CREATE TABLE IF NOT EXISTS interview_reports (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	session_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	input_snapshot JSON, 
	report_content JSON, 
	model_name VARCHAR(100), 
	prompt_version VARCHAR(50) NOT NULL, 
	error_message TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (session_id), 
	FOREIGN KEY(session_id) REFERENCES interview_sessions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. interview_answers：主问题正式回答：关联练习题目快照，不直接关联公共题库
-- 字段说明：
--   id：本表记录的唯一编号
--   question_record_id：回答的是本次练习中的哪道题，不是公共题库ID
--   submission_id：标识同一次提交，后续用于识别请求重试
--   content：保存用户原始回答
--   created_at：由提交接口填写UTC时间
-- 外键：本表 question_record_id → interview_questions.id；未配置级联删除。
CREATE TABLE IF NOT EXISTS interview_answers (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	question_record_id INTEGER NOT NULL, 
	submission_id VARCHAR(36) NOT NULL, 
	content TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (question_record_id), 
	FOREIGN KEY(question_record_id) REFERENCES interview_questions (id), 
	UNIQUE (submission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. interview_feedbacks：主回答的 AI 点评及生成状态
-- 字段说明：
--   id：点评记录自己的编号
--   answer_id：关联用户回答：一条回答最多保存一条点评记录
--   status：点评状态：pending/processing/succeeded/failed；ORM 默认值：'pending'
--   feedback_content：成功后保存结构化点评，尚未生成时为空
--   model_name：记录实际使用的模型名称
--   error_message：失败时记录简短原因
--   created_at：时间由后面的业务代码填写
--   updated_at：最后更新时间，由业务代码填写
-- 外键：本表 answer_id → interview_answers.id；未配置级联删除。
CREATE TABLE IF NOT EXISTS interview_feedbacks (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	answer_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	feedback_content JSON, 
	model_name VARCHAR(100), 
	error_message TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (answer_id), 
	FOREIGN KEY(answer_id) REFERENCES interview_answers (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. interview_followups：针对主回答生成的追问及参考要点
-- 字段说明：
--   id：记录自己的编号
--   parent_answer_id：关联主问题的正式回答，不是题目快照编号
--   status：追问问题的生成状态：processing / succeeded / failed
--   question_content：尚未生成成功时，正文和参考要点可以为空
--   reference_points：回答的参考要点
--   model_name：本次生成使用的模型和提示词版本
--   prompt_version：类型和可空性见下方定义
--   error_message：生成失败的简短原因
--   created_at：时间由后续业务函数填写
--   updated_at：最后更新时间，由业务代码填写
-- 外键：本表 parent_answer_id → interview_answers.id；未配置级联删除。
CREATE TABLE IF NOT EXISTS interview_followups (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	parent_answer_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	question_content TEXT, 
	reference_points TEXT, 
	model_name VARCHAR(100), 
	prompt_version VARCHAR(50) NOT NULL, 
	error_message TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (parent_answer_id), 
	FOREIGN KEY(parent_answer_id) REFERENCES interview_answers (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 14. interview_followup_answers：追问的正式回答
-- 字段说明：
--   id：追问回答自己的编号
--   followup_id：关联追问；一道追问最多有一条正式回答
--   submission_id：同一次提交重试时保持不变
--   content：保留回答原文，包括代码缩进和换行
--   created_at：由后续提交接口填写 UTC 时间
-- 外键：本表 followup_id → interview_followups.id；未配置级联删除。
CREATE TABLE IF NOT EXISTS interview_followup_answers (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	followup_id INTEGER NOT NULL, 
	submission_id VARCHAR(36) NOT NULL, 
	content TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (followup_id), 
	FOREIGN KEY(followup_id) REFERENCES interview_followups (id), 
	UNIQUE (submission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 15. interview_followup_feedbacks：追问回答的独立点评
-- 字段说明：
--   id：点评记录自己的编号
--   followup_answer_id：关联追问回答；一份回答最多保留一份点评
--   status：pending / processing / succeeded / failed；ORM 默认值：'pending'
--   feedback_content：复用 FeedbackContent 的结果结构，以字典形式保存
--   model_name：记录生成时的模型和提示词版本
--   prompt_version：类型和可空性见下方定义
--   error_message：失败时保存简短原因
--   created_at：时间由后续接口填写
--   updated_at：最后更新时间，由业务代码填写
-- 外键：本表 followup_answer_id → interview_followup_answers.id；未配置级联删除。
CREATE TABLE IF NOT EXISTS interview_followup_feedbacks (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	followup_answer_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	feedback_content JSON, 
	model_name VARCHAR(100), 
	prompt_version VARCHAR(50) NOT NULL, 
	error_message TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (followup_answer_id), 
	FOREIGN KEY(followup_answer_id) REFERENCES interview_followup_answers (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

