# LangGraph：条件边、分支与循环

> 来源：https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow
> 范围：LangGraph Python 控制流文档
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 普通边与条件边
普通边定义固定执行顺序。条件边调用路由函数，根据当前状态返回后续节点标识；可以映射业务标签到真实节点。
## 分支和循环
分支用于成功/失败、是否继续等判断；循环让步骤重复直到条件满足。必须设计退出路径和执行限制，不能依赖模型永远自行停止。
## 状态与路由
节点返回业务数据，路由函数读取这些数据决定方向。状态 stage 不是线程位置的唯一真相；恢复时还应查看图的待执行任务与中断信息。
## 工程示例
点评 succeeded 后进入等待选择；failed 后结束本轮图调用，由接口决定重试。选择 generate_followup 进入生成节点，finish 进入 END。
## 常见误区
同时给一个节点设置普通后继和条件路由，可能让多条路径都执行，并非条件边天然覆盖普通边。应只保留实际想要的控制关系。

## 官方来源

[LangGraph：条件边、分支与循环](https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow)
