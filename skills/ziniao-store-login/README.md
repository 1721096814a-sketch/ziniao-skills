# 紫鸟店铺登录技能

已安装为个人技能 `ziniao-store-login`，由 Agent 按 SKILL.md 编排执行。

## 使用

在会话中指定真实目标店铺，例如：

```text
用 ziniao-store-login 登录 12号机美国。
```

或使用斜杠命令：

```text
/ziniao-store-login 12号机美国
```

以上仅为调用示例，不表示已执行该店铺登录。

流程：尝试紫鸟已有自动填充 → 未获验证码时按表向关联人员以飞书应用身份询问 → 最多等待 5 分钟，收到有效关联回复即尝试登录 → 核对后台身份并通知用户。询问、收到的相关回复及每次尝试都通过飞书应用同步。收到的正常验证码按要求完整转发给任务用户，本地断点不保存验证码。

## 所有店铺业务的公共前置

本技能也是当前及未来所有紫鸟店铺网页业务技能的统一前置，不限于 IEN 和超时货件。业务技能先以 `entryMode=ensure_session` 确保目标登录；已有有效登录直接复用，未登录统一恢复，成功后从原业务断点继续。正常执行业务时无需先额外发送登录命令。`entryMode` 是 Agent 交接字段，不是 CLI 参数。

通用交接、返回状态与新技能接入模板见 [upstream-contract.md](references/upstream-contract.md)。可按仓库根目录 README 的示例，在自己的全局 `~/.claude/CLAUDE.md` 中加入前置要求。本仓库的 IEN 技能已接入，其他店铺业务技能可采用同一契约。业务结果通知范围与登录通知分别管理，当次只读/不登录/不发送等限制优先。

唯一默认表格为 `D:\共享\验证码请求飞书.xls`。列为「机器名称、员工UserID、姓名」，其中员工UserID 使用飞书 `ou_` 开头的 open_id。每次执行重新读表；不编辑、不另存为固定人员名单。

这是跨平台 Agent 操作规范，页面选择器按执行时页面确认；没有驻留服务或定时任务。技能创建后不会自行发送索码消息。遇到未知平台验证流程或 UI 无法触达时，按正文保存断点并报告。

## 本地只读核对

```powershell
python -I -X utf8 "<本技能目录>/scripts/read_mapping.py" --list
python -I -X utf8 "<本技能目录>/scripts/read_mapping.py" --store "12号机美国"
```

脚本只读取 XLS，不调用紫鸟或飞书，不发消息。Windows 输出使用 UTF-8。依赖 `xlrd==2.0.2` 已安装在本技能 `vendor`，迁移后可重新安装：

```powershell
python -I -m pip install --target "<本技能目录>/vendor" xlrd==2.0.2
```

## 验证

```powershell
python -I -X utf8 -m unittest discover -s "<本技能目录>/tests" -v
```

本地测试覆盖精确店铺匹配、重复行、字段缺失、ID 格式、同 ID 姓名冲突与源工作簿保持不变。模拟流程验证与真实登录验证分开记录；创建阶段不联系人员做测试。
