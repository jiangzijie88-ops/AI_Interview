# FastAPI：UploadFile、字节与文件导入

> 来源：https://fastapi.tiangolo.com/tutorial/request-files/
> 范围：FastAPI 文件上传文档
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 请求形式
原生文件上传通常使用 multipart/form-data。声明 bytes 会将内容作为字节读入；UploadFile 提供文件对象、名称等信息，并使用可溢写到磁盘的暂存方式，适合避免总是一次性把大文件读入内存。
## 常用方法
UploadFile 提供 read、write、seek、close 等异步方法。文件内容需要按实际编码解析，扩展名不能保证正文格式或可信性。
## JSON 与文件
同一个请求体不能同时被当成普通 JSON 和 multipart 编码。需要将元数据作为表单字段或设计分开的接口。
## 项目区别
当前 Streamlit 先读取 md/txt，再通过 JSON 发送正文，所以没有用到 FastAPI UploadFile。这是文本导入，不是保存原始附件的系统。
## 常见要求
限制大小和允许格式；处理编码错误；不要用不可信文件名直接拼服务器路径。上传成功后是否入库、审核、建立索引需要业务逻辑完成。

## 官方来源

[FastAPI：UploadFile、字节与文件导入](https://fastapi.tiangolo.com/tutorial/request-files/)
