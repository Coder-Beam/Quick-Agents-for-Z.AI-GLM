/**
 * @opencode-plugin @coder-beam/quickagents
 * @version 2.6.8
 * @description QuickAgents Unified Plugin - Maximize local processing, minimize token consumption
 * @author Coder-Beam
 * @license MIT
 * 
 * 核心目标：最大化本地处理，最小化Token消耗
 * 
 * 整合模块：
 * - FileManager Cache: 文件哈希检测，Token节省60-100%
 * - LoopDetector: Pattern-based循环检测，Token节省100%
 *   - Stuck pattern: A→A→A (same operation 3+ times)
 *   - Oscillation pattern: A→B→A→B (2+ cycles)
 * - Reminder: 事件驱动提醒
 * - LocalExecutor: 本地执行器
 *   - qa命令拦截：memory/knowledge/stats/progress
 *   - grep/glob工具拦截
 * - SkillEvolution: Skills自我进化
 * - FeedbackCollector: 经验收集
 * 
 * Token节省预估：
 * - 文件操作密集场景：60-80%
 * - 搜索密集场景：80-95%
 * - 记忆/知识图谱密集场景：90-100%
 * - 综合场景：50-70%
 */

import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";
import type { Plugin } from "@opencode-ai/plugin";

// ============================================================================
// 类型定义
// ============================================================================

interface PluginConfig {
  fileManagerCache: boolean;
  loopDetector: boolean;
  reminder: boolean;
  localExecutor: boolean;
  skillEvolution: boolean;
  feedbackCollector: boolean;
}

interface CacheEntry {
  hash: string;
  content: string;
  timestamp: number;
}

interface LocalResult {
  success: boolean;
  data?: any;
  error?: string;
}

// ============================================================================
// 主插件
// ============================================================================

export const QuickAgentsPlugin: Plugin = async (ctx) => {
  const { directory, client } = ctx;

  const config: PluginConfig = {
    fileManagerCache: true,
    loopDetector: true,
    reminder: true,
    localExecutor: true,
    skillEvolution: true,
    feedbackCollector: true,
  };

  // ============================================================================
  // 状态管理
  // ============================================================================

  const fileCache = new Map<string, CacheEntry>();
  
  // Pattern-based loop detection state
  interface ToolCall {
    fingerprint: string;
    toolName: string;
    timestamp: number;
  }
  const callSequence: ToolCall[] = [];
  const MAX_SEQUENCE_LENGTH = 20;
  const STUCK_THRESHOLD = 3;      // Same call 3+ times in a row
  const OSCILLATION_MIN = 2;      // A→B→A→B pattern (2 cycles)
  const PATTERN_WINDOW = 60000;   // 60 second window
  
  let toolCallCount = 0;
  let sessionStartTime = Date.now();
  let errorCount = 0;

  // ============================================================================
  // 工具函数
  // ============================================================================

  const log = async (
    message: string,
    level: "info" | "warn" | "error" = "info",
    extra: Record<string, any> = {}
  ) => {
    await client.app.log({
      body: {
        service: "quickagents",
        level,
        message,
        extra: { cacheSize: fileCache.size, toolCalls: toolCallCount, ...extra },
      },
    });
  };

  const callPython = (script: string, timeout = 5000): LocalResult => {
    try {
      const escapedDir = directory.replace(/\\/g, "\\\\");
      const indentedScript = script.split("\n").map((l) => "    " + l).join("\n");
      const fullScript = `
import sys, json
sys.path.insert(0, r"${escapedDir}")
try:
${indentedScript}
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
      `.trim();

      const escapedScript = fullScript
        .replace(/\\/g, "\\\\")
        .replace(/"/g, '\\"')
        .replace(/\n/g, "; ");

      const result = execSync(`python -c "${escapedScript}"`, {
        encoding: "utf-8",
        timeout,
        cwd: directory,
        maxBuffer: 10 * 1024 * 1024,
      });

      return JSON.parse(result.trim());
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  };

  const getFileHash = (filePath: string): string => {
    try {
      if (!fs.existsSync(filePath)) return "";
      if (process.platform === "win32") {
        const output = execSync(`certutil -hashfile "${filePath}" MD5`, {
          encoding: "utf-8",
        });
        return output.split("\n")[1]?.trim().replace(/\s/g, "") || "";
      } else {
        return execSync(`md5 -q "${filePath}"`, { encoding: "utf-8" }).trim();
      }
    } catch {
      return "";
    }
  };

  const shouldSkipFile = (filePath: string): boolean => {
    const skipPatterns = [
      "node_modules", ".git", "__pycache__", ".pyc",
      "dist", "build", ".next", "coverage", ".venv", "venv",
    ];
    return skipPatterns.some((p) => filePath.includes(p));
  };

  // ============================================================================
  // FileManager Cache 模块
  // ============================================================================

  const fileManagerCache = {
    check: (filePath: string): boolean => {
      if (!config.fileManagerCache || shouldSkipFile(filePath)) return false;

      const currentHash = getFileHash(filePath);
      const cached = fileCache.get(filePath);

      if (cached && cached.hash === currentHash) {
        return true; // 文件未变化
      }
      return false;
    },

    update: (filePath: string, content: string) => {
      const hash = getFileHash(filePath);
      if (hash) {
        fileCache.set(filePath, { hash, content, timestamp: Date.now() });
      }
    },

    invalidate: (filePath: string) => {
      fileCache.delete(filePath);
    },

    clear: () => {
      fileCache.clear();
    },
  };

  // ============================================================================
  // LoopDetector 模块 - Pattern-based Detection
  // ============================================================================

  const loopDetector = {
    // Generate fingerprint for a tool call
    fingerprint: (toolName: string, toolArgs: any): string => {
      // Normalize args for comparison
      const normalizedArgs = JSON.stringify(toolArgs, Object.keys(toolArgs || {}).sort());
      return `${toolName}:${normalizedArgs}`;
    },

    // Detect if stuck on same operation (A→A→A)
    detectStuck: (sequence: ToolCall[]): { detected: boolean; pattern: string } => {
      if (sequence.length < STUCK_THRESHOLD) return { detected: false, pattern: "" };
      
      const recent = sequence.slice(-STUCK_THRESHOLD);
      const firstFingerprint = recent[0].fingerprint;
      
      if (recent.every(call => call.fingerprint === firstFingerprint)) {
        return { detected: true, pattern: `stuck:${firstFingerprint}` };
      }
      return { detected: false, pattern: "" };
    },

    // Detect oscillation between two operations (A→B→A→B)
    detectOscillation: (sequence: ToolCall[]): { detected: boolean; pattern: string } => {
      if (sequence.length < 4) return { detected: false, pattern: "" };
      
      const recent = sequence.slice(-6); // Check last 6 calls
      const fingerprints = recent.map(c => c.fingerprint);
      
      // Check for A→B→A→B pattern
      for (let cycleLen = 2; cycleLen <= 3; cycleLen++) {
        const cycles = Math.floor(fingerprints.length / cycleLen);
        if (cycles < OSCILLATION_MIN) continue;
        
        let isOscillation = true;
        const pattern = fingerprints.slice(0, cycleLen);
        
        for (let i = 0; i < fingerprints.length; i++) {
          if (fingerprints[i] !== pattern[i % cycleLen]) {
            isOscillation = false;
            break;
          }
        }
        
        if (isOscillation) {
          return { detected: true, pattern: `oscillation:${pattern.join(",")}` };
        }
      }
      return { detected: false, pattern: "" };
    },

    // Main check function
    check: (toolName: string, toolArgs: any): { detected: boolean; pattern: string; count: number } => {
      if (!config.loopDetector) return { detected: false, pattern: "", count: 0 };

      const fingerprint = loopDetector.fingerprint(toolName, toolArgs);
      const now = Date.now();

      // Add to sequence
      callSequence.push({ fingerprint, toolName, timestamp: now });
      
      // Trim old entries
      while (callSequence.length > MAX_SEQUENCE_LENGTH) {
        callSequence.shift();
      }

      // Filter to window
      const recentCalls = callSequence.filter(c => now - c.timestamp < PATTERN_WINDOW);

      // Check patterns
      const stuck = loopDetector.detectStuck(recentCalls);
      if (stuck.detected) {
        return { detected: true, pattern: stuck.pattern, count: STUCK_THRESHOLD };
      }

      const oscillation = loopDetector.detectOscillation(recentCalls);
      if (oscillation.detected) {
        return { detected: true, pattern: oscillation.pattern, count: 4 };
      }

      // Count same fingerprint in window
      const sameCount = recentCalls.filter(c => c.fingerprint === fingerprint).length;
      return { detected: false, pattern: "", count: sameCount };
    },

    // Get recent sequence for debugging
    getSequence: (): ToolCall[] => [...callSequence],
  };

  // ============================================================================
  // LocalExecutor 模块（核心：本地执行）
  // ============================================================================

  const localExecutor = {
    // QA命令处理
    qa: {
      memory: (args: string[]): LocalResult => {
        const subCmd = args[0];
        
        if (subCmd === "get") {
          const key = args[1];
          return callPython(`
from quickagents import UnifiedDB
db = UnifiedDB()
value = db.get_memory('${key}')
print(json.dumps({"success": True, "data": value}))
          `);
        }
        
        if (subCmd === "set") {
          const key = args[1];
          const value = args.slice(2).join(" ");
          return callPython(`
from quickagents import UnifiedDB, MemoryType
db = UnifiedDB()
db.set_memory('${key}', '${value}', MemoryType.FACTUAL)
print(json.dumps({"success": True}))
          `);
        }
        
        if (subCmd === "search") {
          const query = args.slice(1).join(" ");
          return callPython(`
from quickagents import UnifiedDB
db = UnifiedDB()
results = db.search_memory('${query}')
print(json.dumps({"success": True, "data": results}))
          `, 10000);
        }
        
        return { success: false, error: `Unknown memory command: ${subCmd}` };
      },

      knowledge: (args: string[]): LocalResult => {
        const subCmd = args[0];
        
        if (subCmd === "search") {
          const query = args.slice(1).join(" ");
          return callPython(`
from quickagents.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph()
results = kg.search('${query}')
data = [{"id": n.id, "title": n.title} for n in results[:10]]
print(json.dumps({"success": True, "data": data}))
          `, 10000);
        }
        
        if (subCmd === "trace") {
          const nodeId = args[1];
          return callPython(`
from quickagents.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph()
trace = kg.trace_requirement('${nodeId}')
print(json.dumps({"success": True, "data": [n.id for n in trace]}))
          `, 10000);
        }
        
        return { success: false, error: `Unknown knowledge command: ${subCmd}` };
      },

      stats: (): LocalResult => {
        return callPython(`
from quickagents import UnifiedDB
db = UnifiedDB()
stats = db.get_stats()
print(json.dumps({"success": True, "data": stats}))
        `);
      },

      progress: (): LocalResult => {
        return callPython(`
from quickagents import UnifiedDB
db = UnifiedDB()
progress = db.get_progress()
print(json.dumps({"success": True, "data": progress}))
        `);
      },
    },

    // Grep本地执行
    grep: (pattern: string, include?: string): LocalResult => {
      try {
        let cmd: string;
        if (process.platform === "win32") {
          cmd = include
            ? `findstr /S /N /C:"${pattern}" ${include}`
            : `findstr /S /N /C:"${pattern}" *.*`;
        } else {
          cmd = include
            ? `rg -l "${pattern}" -g "${include}"`
            : `rg -l "${pattern}"`;
        }
        
        const result = execSync(cmd, {
          encoding: "utf-8",
          timeout: 30000,
          cwd: directory,
          maxBuffer: 5 * 1024 * 1024,
        });
        
        const files = result.trim().split("\n").filter(Boolean);
        return { success: true, data: files.slice(0, 100) };
      } catch (error: any) {
        if (error.status === 1) {
          return { success: true, data: [] };
        }
        return { success: false, error: error.message };
      }
    },

    // Glob本地执行
    glob: (pattern: string): LocalResult => {
      try {
        // 空值检查：如果pattern为空，返回空结果
        if (!pattern || typeof pattern !== 'string' || pattern.trim() === '') {
          return { success: true, data: [] };
        }
        
        const files: string[] = [];
        
        const walkDir = (dir: string, regex: RegExp) => {
          const entries = fs.readdirSync(dir, { withFileTypes: true });
          for (const entry of entries) {
            const fullPath = path.join(dir, entry.name);
            if (entry.isDirectory()) {
              if (!["node_modules", ".git", "__pycache__"].includes(entry.name)) {
                walkDir(fullPath, regex);
              }
            } else if (entry.isFile() && regex.test(entry.name)) {
              files.push(fullPath.replace(directory, ".").replace(/\\/g, "/"));
            }
          }
        };
        
        const regexPattern = new RegExp(
          "^" + pattern
            .replace(/\*\*/g, ".*")
            .replace(/\*/g, "[^/]*")
            .replace(/\?/g, "[^/]")
            .replace(/\./g, "\\.") + "$"
        );
        
        walkDir(directory, regexPattern);
        
        return { success: true, data: files };
      } catch (error: any) {
        return { success: false, error: error.message };
      }
    },
  };

  // ============================================================================
  // 插件初始化日志
  // ============================================================================

  await log("QuickAgents Plugin v2.2.0 initialized", "info", {
    config,
    platform: process.platform,
    features: ["FileManager", "LoopDetector", "LocalExecutor", "SkillEvolution"],
  });

  // ============================================================================
  // 返回 Hooks
  // ============================================================================

  return {
    // ------------------------------------------------------------------
    // tool.execute.before - 核心拦截点
    // ------------------------------------------------------------------
    "tool.execute.before": async (input: any, output: any) => {
      const toolName = input.tool;
      const toolArgs = input.args || {};

      // 1. FileManager Cache: 拦截read
      if (toolName === "read" && toolArgs.filePath) {
        if (fileManagerCache.check(toolArgs.filePath)) {
          await log(`Cache HIT: ${toolArgs.filePath}`, "info");
          throw new Error(
            `[QuickAgents] FILE_UNCHANGED: ${toolArgs.filePath}\n` +
            `文件未变化，请使用对话上下文中的缓存内容。`
          );
        }
        await log(`Cache MISS: ${toolArgs.filePath}`, "info");
      }

      // 2. LoopDetector: Pattern-based detection
      const loopResult = loopDetector.check(toolName, toolArgs);
      if (loopResult.detected) {
        const patternType = loopResult.pattern.startsWith("stuck:") ? "Stuck" : "Oscillation";
        await log(`Loop detected: ${patternType} - ${toolName}`, "warn");
        throw new Error(
          `[QuickAgents] DOOM_LOOP_DETECTED\n` +
          `Pattern: ${patternType}\n` +
          `Tool: ${toolName}\n` +
          `Detail: ${loopResult.pattern}\n` +
          `Action: Verify your approach or request user confirmation.`
        );
      }

      // 3. LocalExecutor: 拦截bash中的qa命令
      if (config.localExecutor && toolName === "bash") {
        const cmd = toolArgs.command || "";
        
        if (cmd.startsWith("qa ")) {
          const parts = cmd.slice(3).trim().split(/\s+/);
          const qaCmd = parts[0];
          const qaArgs = parts.slice(1);
          
          let result: LocalResult;
          
          switch (qaCmd) {
            case "memory":
              result = localExecutor.qa.memory(qaArgs);
              break;
            case "knowledge":
              result = localExecutor.qa.knowledge(qaArgs);
              break;
            case "stats":
              result = localExecutor.qa.stats();
              break;
            case "progress":
              result = localExecutor.qa.progress();
              break;
            default:
              result = { success: false, error: `Unknown qa command: ${qaCmd}` };
          }
          
          await log(`QA command intercepted: qa ${qaCmd}`, "info");
          
          throw new Error(
            `[QuickAgents] LOCAL_RESULT\n` +
            `命令: qa ${qaCmd}\n` +
            `结果: ${JSON.stringify(result, null, 2)}`
          );
        }
      }

      // 4. LocalExecutor: 拦截grep
      if (config.localExecutor && toolName === "grep") {
        const pattern = toolArgs.pattern;
        const include = toolArgs.include;
        const result = localExecutor.grep(pattern, include);
        
        await log(`Grep intercepted: ${pattern}`, "info", { 
          count: result.data?.length || 0 
        });
        
        throw new Error(
          `[QuickAgents] LOCAL_RESULT\n` +
          `工具: grep\n` +
          `结果: ${JSON.stringify(result, null, 2)}`
        );
      }

      // 5. LocalExecutor: 拦截glob
      if (config.localExecutor && toolName === "glob") {
        const pattern = toolArgs.pattern;
        
        if (!pattern) {
          return;
        }
        
        const result = localExecutor.glob(pattern);
        
        await log(`Glob intercepted: ${pattern}`, "info", { 
          count: result.data?.length || 0 
        });
        
        throw new Error(
          `[QuickAgents] LOCAL_RESULT\n` +
          `工具: glob\n` +
          `结果: ${JSON.stringify(result, null, 2)}`
        );
      }
    },

    // ------------------------------------------------------------------
    // tool.execute.after - 后处理
    // ------------------------------------------------------------------
    "tool.execute.after": async (input: any, output: any) => {
      const toolName = input.tool;
      const toolArgs = input.args || {};

      // FileManager Cache更新
      if (toolName === "read" && toolArgs.filePath && output.result) {
        fileManagerCache.update(toolArgs.filePath, output.result);
      }

      // Reminder计数
      toolCallCount++;
      if (toolCallCount % 5 === 0) {
        await log(`Progress: ${toolCallCount} tool calls`, "info");
      }

      // SkillEvolution
      if (toolName === "skill") {
        callPython(`
from quickagents import get_evolution
evolution = get_evolution()
evolution.on_task_complete({
    'task_id': 'auto',
    'skills_used': ['${toolArgs.name}'],
    'success': True
})
        `, 10000);
      }
    },

    // ------------------------------------------------------------------
    // 其他 Hooks
    // ------------------------------------------------------------------

    "file.watcher.updated": async (input: any) => {
      if (input.path) {
        fileManagerCache.invalidate(input.path);
        await log(`Cache invalidated: ${input.path}`, "info");
      }
    },

    "session.status": async () => {
      const elapsed = (Date.now() - sessionStartTime) / 60000;
      if ([10, 30].includes(Math.floor(elapsed))) {
        await log(`Long running session: ${Math.floor(elapsed)} minutes`, "warn");
      }
    },

    "session.error": async (input: any) => {
      errorCount++;
      await log(`Error #${errorCount}: ${input.error?.message || "Unknown"}`, "error");
    },

    "session.deleted": async () => {
      fileManagerCache.clear();
      callSequence.length = 0;
      toolCallCount = 0;
      sessionStartTime = Date.now();
      errorCount = 0;
      await log("Session cleaned up", "info");
    },

    "command.executed": async (input: any) => {
      if (input.command?.includes("git commit")) {
        callPython(`
from quickagents import get_evolution
evolution = get_evolution()
evolution.on_git_commit()
        `, 10000);
        await log("Git commit detected, SkillEvolution triggered", "info");
      }
    },
  };
};

export default QuickAgentsPlugin;
