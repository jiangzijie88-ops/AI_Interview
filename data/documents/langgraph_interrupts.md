> 官方来源：https://docs.langchain.com/oss/python/langgraph/interrupts
> 官方文档节选的非官方中文翻译；整理日期：2026-11-12。省略进阶案例及重复示例，保留核心机制与使用规则。API 名称保留，使用前应核对本地版本。

# LangGraph 中断：暂停、恢复与使用规则

中断允许在指定位置暂停图执行，等待外部输入后继续，实现需要人工参与的人机协同流程。触发中断时，LangGraph 通过持久化层保存状态，等待调用方恢复执行。

在图节点中调用 `interrupt()` 可以触发中断。函数接受可 JSON 序列化的数据，并将它提供给调用方。准备继续时，通过携带恢复值的 `Command` 再次调用图，恢复值成为节点内部对应 `interrupt()` 调用的返回值。

与在特定节点执行前后暂停的静态断点不同，中断是动态的，可以放在节点代码的指定位置，并根据业务逻辑触发。

- checkpointer 保存执行状态，供之后读取检查点并恢复。
- thread_id 定位执行线程。通过 `config={"configurable": {"thread_id": ...}}` 指定应读取的状态。
- 使用 `graph.stream_events(..., version="v3")` 时，中断数据通过 `stream.interrupts` 暴露；等待输入时，`stream.interrupted` 为 True。

复用相同 thread_id 可以关联原检查点；使用新的标识会创建初始状态为空的新线程。

## 使用 interrupt 暂停

需要满足三个条件：

1. 配置 checkpointer 保存状态；生产环境使用持久化后端。
2. 配置 thread_id，确定要恢复哪份执行状态。
3. 在需要暂停的位置调用 interrupt，参数必须可以 JSON 序列化。

以下是节点片段，State 由应用定义：

```python
from langgraph.types import interrupt


def approval_node(state: State):
    # 暂停并请求批准
    approved = interrupt("Do you approve this action?")
    # 恢复输入成为对应 interrupt() 的返回值
    return {"approved": approved}
```

调用中断后：

1. 图在 interrupt 调用处暂停。
2. checkpointer 保存状态；生产环境应使用数据库等持久化存储。
3. 中断参数返回给调用方。事件流模式通过 stream.interrupts 获取；默认 invoke 接口通过结果的 __interrupt__ 字段获取。参数可以是字符串、字典、数组等可 JSON 序列化的值。
4. 图保持暂停，直到调用方提交恢复输入。
5. 恢复值传回节点，作为对应 interrupt 调用的返回值。

## 恢复中断

暂停后，再次调用图并传入包含恢复值的 Command。恢复值传给对应 interrupt，使节点根据外部输入继续执行。

原文推荐通过事件流驱动可能中断的图：stream.interrupts 和 stream.interrupted 提供中断信息，stream.output 提供最终状态。下面的片段假定 graph 已完成构建：

```python
from langgraph.types import Command

# 首次运行，遇到中断后暂停；生产环境应使用稳定的标识
config = {"configurable": {"thread_id": "thread-1"}}
stream = graph.stream_events({"input": "data"}, config=config, version="v3")

# 获取输出，驱动本次执行直至完成或暂停
final = stream.output

if stream.interrupted:
    print(stream.interrupts)

# 使用相同 thread_id 恢复
# True 成为节点内对应 interrupt() 的返回值
resumed = graph.stream_events(Command(resume=True), config=config, version="v3")
final = resumed.output
```

默认 graph.invoke(...) 仍可使用，中断信息位于 `result["__interrupt__"]`。不需要事件流时可以采用该接口。事件流示例来自在线文档，使用前需要核对安装版本，不必为了导入资料而替换项目现有的 ainvoke 调用。

恢复执行的关键点：

- 必须使用与中断发生时相同的 thread_id。
- Command(resume=...) 中的值成为对应 interrupt 的返回值。
- **包含中断的节点会从头重新执行，不是从暂停行直接继续。** 中断之前的代码也会再次运行。
- 恢复值应可以 JSON 序列化；指定带类型的 response_schema 时，还需要通过相应校验。

作为 invoke、stream 或 stream_events 的输入时，用于恢复中断的是 Command(resume=...)。其他参数 update、goto、graph 主要用于节点返回 Command。不要把 Command(update=...) 当作继续普通多轮对话的输入；常规新输入应使用普通字典。

## 中断使用规则

interrupt 通过抛出特殊异常通知运行时暂停。异常沿调用栈传播，由运行时捕获，随后保存状态并等待外部输入。

恢复时，运行时重新执行整个节点，因此必须考虑中断之前的操作会重复执行。

### 不要用宽泛的 try/except 包住 interrupt

宽泛异常捕获可能吞掉用于暂停的特殊异常，使图无法正确处理中断。

- 将中断与容易出错的业务代码分开。
- 必须处理异常时，只捕获明确的业务异常类型。
- 不要用裸 except 或宽泛捕获拦截中断异常。

### 不要改变节点内中断的顺序

节点可以包含多次中断，但必须保持顺序稳定。LangGraph 为执行节点的任务维护恢复值列表。每次恢复从节点开头执行，遇到中断时按列表位置寻找对应恢复值，匹配严格依赖顺序索引。

- 不同次执行中，中断顺序应一致。
- 不要依据跨次执行可能变化的条件跳过某次中断。
- 不要在执行次数不确定的循环中调用中断，包括用于校验的 while True 循环。可通过条件边组织重复校验流程。

### 中断参数应可序列化

不同 checkpointer 的序列化能力可能不同，函数等复杂对象通常不能按 JSON 序列化。为了便于部署，使用简单数据结构。

- 可以传字符串、数字、布尔值等简单类型。
- 可以传由简单值组成的字典和列表。
- 不要传函数、任意自定义类实例或其他复杂对象。

### 中断前的副作用应保持幂等

副作用是改变外部状态的操作，例如更新数据库、创建记录或发送通知。幂等表示同一操作执行多次，不会产生超出首次执行之外的额外影响。

恢复会重新执行节点，中断之前的副作用也会重复。例如先调用接口更新记录，再触发中断，恢复时接口会再次调用，可能覆盖数据或创建重复记录。

建议：

- 中断前使用幂等操作，例如按稳定主键更新或执行 upsert。
- 尽可能把副作用放在中断之后。
- 条件允许时，将副作用拆到独立节点。
- 创建记录前检查其是否存在，或利用唯一约束等机制去重。

**放在中断之后仍然需要幂等性。** 如果节点已提交外部操作，却在节点完成前失败，重试仍可能重复该操作。外部系统需要幂等处理或写入去重。

不要在中断前无条件创建新记录或追加历史事件，否则每次恢复都可能产生重复数据。