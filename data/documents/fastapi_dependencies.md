# FastAPI：Depends、依赖注入与权限复用

> 来源：https://fastapi.tiangolo.com/tutorial/dependencies/
> 范围：FastAPI 在线文档
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 依赖注入
Depends 声明函数运行前需要的组件。FastAPI 解析请求时先执行依赖，再把返回结果传给参数，依赖还可以依赖其他依赖。
## 场景
数据库会话、当前用户、管理员权限、公共查询参数适合复用。依赖参数即使没有在函数体使用，其检查仍会执行。
## 调用区别
Depends(get_db) 传入函数，让框架在请求时管理；get_db() 是直接调用产生对象，不能机械互换。
## 缓存与生命周期
同一请求中默认可复用相同依赖的结果，这不是跨用户全局缓存。身份依赖仍需从可信凭证解析用户并查询有效状态。
## 项目应用
get_admin_user 依赖 get_current_user，接口再声明 Depends(get_admin_user)。页面隐藏按钮不替代后端权限检查。
## 自测问题
为什么 admin_user 未用于函数体仍有作用？依赖异常后接口函数会继续执行吗？

## 官方来源

[FastAPI：Depends、依赖注入与权限复用](https://fastapi.tiangolo.com/tutorial/dependencies/)
