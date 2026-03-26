---
description: 启用多代理协调功能
mode: primary
model: inherit
tools:
  write: false
  edit: true
  bash: true
---

# 启用多代理协调

启用 QuickAgents 的多代理协调功能，允许多个代理并行或协作工作。

## 执行步骤

1. **检查当前状态**
   - 读取 `.opencode/config/quickagents.json`
   - 确认当前 `coordination.enabled` 状态

2. **启用协调功能**
   ```bash
   # 使用 jq 更新配置（如果可用）
   if command -v jq &>/dev/null; then
     jq '.coordination.enabled = true' .opencode/config/quickagents.json > tmp.json && mv tmp.json .opencode/config/quickagents.json
   else
     # 手动编辑
     echo "请手动将 quickagents.json 中的 coordination.enabled 设置为 true"
   fi
   ```

3. **验证配置**
   - 确认配置文件格式正确
   - 列出可用的团队和工作流

4. **输出状态**
   ```
   ✓ 多代理协调已启用
   
   可用团队:
   - review-team (代码审查团队)
   - debug-team (调试诊断团队)
   - feature-team (全栈功能团队)
   
   可用工作流:
   - parallel-review (并行代码审查)
   - hypothesis-debug (假设驱动调试)
   - full-stack-feature (全栈功能开发)
   
   使用方式:
   - /run-workflow parallel-review
   - /run-workflow hypothesis-debug
   - /run-workflow full-stack-feature
   ```

## 注意事项

- 启用后会增加资源消耗（多个代理并行运行）
- 仅支持 GLM 系列模型，继承 OpenCode 主配置
- 默认最大并行代理数为 3

## 回滚

如需禁用，请使用 `/disable-coordination` 命令。
