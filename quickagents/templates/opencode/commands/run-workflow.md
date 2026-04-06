---
description: 运行多代理协调工作流
mode: primary
model: inherit
tools:
  write: false
  edit: false
  bash: true
---

# 运行协调工作流

执行指定的多代理协调工作流。

## 用法

```
/run-workflow <workflow-name> [options]
```

## 可用工作流

### parallel-review (并行代码审查)
- **描述**: 多个审查代理并行工作，合并结果
- **团队**: review-team (jianming-review, mengzhang-security, hengge-perf)
- **耗时**: 约 5-10 分钟
- **适用场景**: 代码提交前全面审查

### hypothesis-debug (假设驱动调试)
- **描述**: 同时验证多个假设，选择最佳解决方案
- **团队**: debug-team (kuafu-debug, hengge-perf, mengzhang-security)
- **耗时**: 约 10-20 分钟
- **适用场景**: 复杂问题诊断

### full-stack-feature (全栈功能开发)
- **描述**: 从需求到交付的完整流程
- **团队**: feature-team (yinglong-init, cangjie-doc, lishou-test, huodi-skill)
- **耗时**: 约 30-60 分钟
- **适用场景**: 新功能完整开发

## 执行步骤

1. **前置检查**
   - 验证 quickagents.json 中 `coordination.enabled` 是否为 `true`
   - 如未启用，提示用户运行 `/enable-coordination`

2. **加载工作流配置**
   ```bash
   workflow_name="$1"
   jq ".coordination.workflows.$workflow_name" .opencode/config/quickagents.json
   ```

3. **执行工作流步骤**
   - 按步骤顺序执行
   - 处理依赖关系
   - 收集各步骤输出

4. **聚合结果**
   - 根据工作流配置的聚合策略
   - 生成最终报告

5. **输出结果**
   ```markdown
   ## 工作流执行报告
   
   **工作流**: parallel-review
   **状态**: 成功
   **耗时**: 8m 32s
   
   ### 参与代理
   - jianming-review: 完成 (3个建议)
   - mengzhang-security: 完成 (1个警告)
   - hengge-perf: 完成 (2个优化建议)
   
   ### 汇总结果
   [合并后的审查结果]
   
   ### 建议
   1. [优先级高的建议]
   2. [其他建议]
   ```

## 选项

| 选项 | 说明 |
|------|------|
| `--dry-run` | 模拟执行，不实际运行 |
| `--timeout <ms>` | 覆盖默认超时时间 |
| `--verbose` | 详细输出模式 |
| `--report <file>` | 指定报告输出文件 |

## 错误处理

- 工作流未找到: 显示可用工作流列表
- 协调未启用: 提示运行 `/enable-coordination`
- 超时: 根据 `onFailure` 配置处理
- 代理失败: 尝试重试或部分结果

## 示例

```bash
# 运行并行代码审查
/run-workflow parallel-review

# 运行假设驱动调试（详细模式）
/run-workflow hypothesis-debug --verbose

# 运行全栈功能开发（自定义超时）
/run-workflow full-stack-feature --timeout 3600000
```
