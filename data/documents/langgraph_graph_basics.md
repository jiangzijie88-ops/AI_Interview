# LangGraph：State、Node、Edge 与 compile

> 来源：https://docs.langchain.com/oss/python/langgraph/graph-api
> 范围：LangGraph Python Graph API
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 三个核心概念
State 是共享状态；Node 是读取状态并返回更新的函数；Edge 控制后续执行路径。节点可以调用模型，也可以执行普通业务代码。
## 构建步骤
定义状态结构 → 创建 StateGraph → 注册节点 → 添加边 → compile → invoke 或 ainvoke。compile 构造可执行图并检查部分结构问题，不执行每一项业务。
## 状态流动
节点通常返回部分字段，由字段的更新规则合并。业务字段 stage 可描述当前阶段，但字段取值本身不会自动创建边或中断，必须有节点和路由逻辑配合。
## 项目示例
加载上下文节点核对回答归属，主点评节点调用 manager，条件路由决定进入用户选择还是结束。图状态只存必要编号，正文可从数据库读取。
## 常见误区
节点不是只能是大模型；变量叫 state 不等于自动持久化。没有 checkpointer 的图也能执行，但不能据此认为具备跨调用恢复能力。
## 自测问题
注册节点和调用节点有何区别？compile 与 ainvoke 各做什么？

## 官方来源

[LangGraph：State、Node、Edge 与 compile](https://docs.langchain.com/oss/python/langgraph/graph-api)
