# Python：JSON、字典、编码与文件读写

> 来源：https://docs.python.org/3.11/library/json.html
> 范围：Python 3.11
> 整理日期：2026-11-12；性质：官方资料的非官方中文归纳，含教学示例与误区说明。

## 四个方法
json.dumps 将对象转为 JSON 字符串，loads 从 JSON 字符串解析对象；dump、load 操作文件对象。Python 字典不是 JSON 文本，打印字典也不等于序列化。
## 常见类型
JSON 的 null、true、false 对应 Python None、True、False。JSON 对象的键是字符串，不能依赖整数键往返后仍为整数。
## 编码
ensure_ascii=False 允许直接输出中文，但磁盘文件仍要明确使用 UTF-8。缩进参数便于阅读，不改变业务含义。bytes 必须先按正确编码转成 str。
## 项目应用
索引 config.json 记录模型名称和维度，不保存密钥。片段 metadata 中的 NumPy 数字可先转为 float，避免序列化类型不兼容。
## 边界
日期、自定义对象和集合等不能无条件直接编码。读取外部 JSON 需要大小和结构限制；解析成功不代表字段可信。

## 官方来源

[Python：JSON、字典、编码与文件读写](https://docs.python.org/3.11/library/json.html)
