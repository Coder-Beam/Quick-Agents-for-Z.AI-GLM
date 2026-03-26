---
description: 禁用多代理协调功能
mode: primary
model: inherit
tools:
  write: false
  edit: true
  bash: true
---

# 禁用多代理协调

禁用 QuickAgents 的多代理协调功能，恢复单代理模式。

## 执行步骤

1. **检查当前状态**
   - 读取 `.opencode/config/quickagents.json`
   - 确认当前 `coordination.enabled` 状态

2. **禁用协调功能**
   ```bash
   # 使用 jq 更新配置（如果可用）
   if command -v jq &>/dev/null; then
     jq '.coordination.enabled = false' .opencode/config/quickagents.json > tmp.json && mv tmp.json .opencode/config/quickagents.json
   else
     # 手动编辑
     echo "请手动将 quickagents.json 中的 coordination.enabled 设置为 false"
   fi
   ```

3. **清理运行状态**
   - 检查是否有正在运行的协调任务
   - 如有，等待完成或提示用户

4. **输出状态**
   ```
   ✓ 多代理协调已禁用
   
   当前模式: 单代理模式
   所有代理将独立运行，不再协调
   
   如需重新启用，请使用 /enable-coordination 命令
   ```

## 注意事项

- 禁用不会影响已完成的任务
- 正在运行的协调任务会继续完成
- 配置文件保留，可随时重新启用

## 重新启用

如需重新启用，请使用 `/enable-coordination` 命令。
