# FastAPI：lifespan 与共享资源生命周期

> 来源：https://fastapi.tiangolo.com/advanced/events/
> 范围：FastAPI 当前推荐 lifespan 方式
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 生命周期
lifespan 在服务开始接收请求前初始化资源，在服务退出时清理。使用 asynccontextmanager，yield 前进行启动准备，之后执行关闭逻辑。
## 适用资源
数据库连接资源、HTTP 客户端、工作流保存器、模型相关共享组件可以统一管理。需要先初始化完成再供请求访问，避免在每个请求中反复创建昂贵资源。
## 项目应用
打开 AsyncSqliteSaver，构建 interview_graph，存入 app.state，接口通过 Request 访问。关闭时由上下文管理器释放保存器。
## 部署边界
多进程有各自内存与资源生命周期，不是一个全局 Python 对象供所有进程共享。启动时重置 processing 记录也需结合单实例假设评估。
## 常见误区
模块 import 时立刻执行网络连接可能使导入与测试困难。应用 lifespan 和单次请求依赖生命周期不是同一层。

## 官方来源

[FastAPI：lifespan 与共享资源生命周期](https://fastapi.tiangolo.com/advanced/events/)
