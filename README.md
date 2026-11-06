# 紫鸟店铺业务技能

两个配合使用的 Claude Code 技能：

| 技能 | 用途 |
|---|---|
| [ziniao-store-login](skills/ziniao-store-login/SKILL.md) | 检查/恢复店铺网站登录，验证码未自动填充时按本地表格向关联人员索码，最多等待5分钟，并通过飞书应用同步进展。 |
| [ziniao-amazon-ien-report](skills/ziniao-amazon-ien-report/SKILL.md) | 匹配来源表中的 IEN，通过页面填写、保存后重新打开核对，并发送按店铺汇总的三列飞书结果卡片。 |

这些技能由 Agent 按规范编排执行，包含只读匹配脚本和卡片构造器，没有驻留服务、定时任务或跨平台无人值守登录 Runtime。

## 依赖

- 紫鸟客户端与 `ziniao-cli`，以及 CLI 自带的 `ziniao-shared`、`ziniao-store`、`ziniao-page` 等技能。
- `lark-cli` 及其当前 IM 指南；应用需具备实际收发目标私聊的权限。使用 `--as bot` 发送和读取应用会话。
- IEN 来源为钉钉电子表格时，安装并配置相应钉钉表格技能/CLI。
- Python 3.10+，读取 XLS 使用 `xlrd==2.0.2`；Node.js 用于 IEN 卡片脚本和测试。

## 安装

将 `skills` 下两个目录复制到个人技能目录。PowerShell 中，在本仓库根目录执行：

```powershell
$SkillRoot = Join-Path $HOME ".claude/skills"
New-Item -ItemType Directory -Force $SkillRoot | Out-Null
Copy-Item -Recurse "./skills/ziniao-store-login" $SkillRoot
Copy-Item -Recurse "./skills/ziniao-amazon-ien-report" $SkillRoot
python -I -m pip install --target (Join-Path $SkillRoot "ziniao-store-login/vendor") -r "./requirements.txt"
```

已有同名技能时先核对本地修改，再选择合并或替换。CLI 自带技能须与这两个技能安装在同一技能根目录，使相对依赖路径能够解析。克隆仓库本身不会配置任何服务登录或发送消息。

## 本地配置

验证码联系人表默认位于 `D:\共享\验证码请求飞书.xls`，第一行为：

```text
机器名称 | 员工UserID | 姓名
```

机器名称填写紫鸟完整店铺名；员工UserID 使用飞书 `ou_` 开头的 open_id。表格始终只读，名称精确匹配；保留“新”、VC、PO、地区等区别。联系人表、真实人员和 open_id 不包含在仓库中。

使用其他路径时，先在本地确认该来源，再将相同路径作为本次技能输入；只读脚本通过 `--workbook` 指定。不要把来源路径变更扩展成自动读取其他文件。

IEN 来源表链接由任务用户提供。仓库未内置内部文档地址、账号、真实货件结果、Cookie、令牌或运行断点。

## 使用

```text
用 ziniao-store-login 登录 <完整店铺名>。
用 ziniao-amazon-ien-report 处理 <完整店铺名> 的指定货件，IEN 来源为 <用户提供的表格链接>。
```

IEN 技能已将登录技能作为前置。其他店铺业务技能也可按 [统一交接契约](skills/ziniao-store-login/references/upstream-contract.md) 接入：先以内部 `entryMode=ensure_session` 确保登录，已登录则直接复用，未登录统一处理。`entryMode` 是 Agent 交接字段，不是 CLI 参数。

若要让今后开发的所有店铺业务技能都遵从这一前置，可在自己的全局指令中加入：

> 所有紫鸟店铺网页业务技能先使用 ziniao-store-login，按其 references/upstream-contract.md 检查目标登录状态，传入真实业务用途、断点和当次限制；成功并核对身份后进入业务。新建或修改技能时也应加入这个前置。

## 操作规则

- 网站只读同源请求串行执行，响应后间隔1–3秒。
- 填写和提交只通过 `ziniao-cli page input` / `page click`；不通过页面脚本改值或调用写接口。UI 无法触达时暂停处理。
- 验证码询问说明完整店铺名和实际用途，不加站点/请求编号。收到的相关回复和尝试结果只向任务用户同步，按任务要求转发验证码，本地不保存验证码正文。
- 用户明确只读、不登录或不发送等限制优先。
- IEN 只有保存后重新打开核对一致，才标记“已填写并核对”；登录成功和消息发送成功都不能替代该核对。

## 验证

在仓库根目录执行：

```powershell
python -I -m pip install --target "./skills/ziniao-store-login/vendor" -r "./requirements.txt"
python -I -X utf8 -m unittest discover -s "./skills/ziniao-store-login/tests" -v
node "./skills/ziniao-amazon-ien-report/ien-card.test.cjs"
```

Python测试覆盖精确匹配、重复/空字段、错误ID与源表只读。机器上没有个人来源表时，对应真实工作簿检查会跳过；其余测试使用模拟数据。Node测试验证三列表格、缺少IEN记录、状态校验及原卡片更新请求。

真实网站登录、五分钟收信和业务提交需要在已授权的目标店铺执行；本地测试不代表完整在线流程已验证。
