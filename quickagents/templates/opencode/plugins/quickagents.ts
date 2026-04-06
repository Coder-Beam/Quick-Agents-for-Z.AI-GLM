/**

 ============================================================================
// LoopDetector V3 - 轻量级本地计数器 + Python 深度检测
// ============================================================================

  const loopDetector = {
    // 加载配置（启动时执行一次）
    loadConfig: (): LoopDetectorConfig => {
      if (cachedConfig) {
        return cachedConfig;
      }
      
      try {
        const configPath = path.join(directory, "quickagents.json");
        if (fs.existsSync(configPath)) {
          const configData = JSON.parse(fs.readFileSync(configPath, "utf-8"));
          cachedConfig = configData.loop_detector || {};
        }
      } catch (e) {
        // 配置加载失败，使用默认值
      }
      
      // 默认配置
      cachedConfig = cachedConfig || {
        threshold_strategy: "normal",
        deep_check_interval: 5
      };
      
      return cachedConfig;
    },
    
    // 本地计数器更新
    updateCounters: (result?: any) => {
      counters.totalCalls++;
      if (result && (result.error || result.success === false)) {
        counters.failures++;
        counters.lastResult = result;
      }
    },
    
    // 检查是否需要深度检测
    shouldDeepCheck: (): boolean => {
      const cfg = loopDetector.loadConfig();
      const interval = cfg.deep_check_interval || 5;
      
      // 每 N 次调用触发一次深度检测
      if (counters.totalCalls % interval === 0) {
        return true;
      }
      
      // 有失败时立即触发深度检测
      if (counters.failures > 0) {
        return true;
      }
      
      return false;
    },
    
    // 深度检测（调用 Python V3）
    deepCheck: (
      toolName: string, 
      toolArgs: any,
      result?: any
    ): LocalResult => {
      return callPython(`
from quickagents import get_loop_detector
import json

detector = get_loop_detector()
is_loop, info = detector.check(
    tool_name='${toolName}',
    tool_args=${JSON.stringify(toolArgs)},
    result=${result ? JSON.stringify(result) : 'None'}
)

print(json.dumps({
    "success": True,
    "data": {
        "is_loop": is_loop,
        "info": info
    }
}))
      `, 5000);
    },
    
    // 主检查函数
    check: (
      toolName: string, 
      toolArgs: any,
      result?: any
    ): { detected: boolean; info: any } => {
      if (!config.loopDetector) {
        return { detected: false, info: {} };
      }
      
      // 1. 更新本地计数器
      loopDetector.updateCounters(result);
      
      // 2. 检查是否需要深度检测
      if (!loopDetector.shouldDeepCheck()) {
        return { detected: false, info: { source: "local_counter" } };
      }
      
      // 3. 执行深度检测
      const checkResult = loopDetector.deepCheck(toolName, toolArgs, result);
      
      if (checkResult.success && checkResult.data) {
        const { is_loop, info } = checkResult.data;
        
        if (is_loop) {
          await log(`Loop detected: ${info.type || "unknown"} - ${toolName}`, "warn");
        }
        
        return { detected: is_loop, info };
      }
      
      return { detected: false, info: { source: "python_error", error: checkResult.error } };
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

    // 2. LoopDetector V3: 使用新的检测逻辑（本地计数 + 定期深度检测）
    const loopResult = loopDetector.check(toolName, toolArgs);
    if (loopResult.detected) {
      const patternType = loopResult.info?.type || "unknown";
      await log(`Loop detected: ${patternType} - ${toolName}`, "warn");
      throw new Error(
        `[QuickAgents] DOOM_LOOP_DETECTED\n` +
        `Pattern: ${patternType}\n` +
        `Tool: ${toolName}\n` +
        `Detail: ${JSON.stringify(loopResult.info)}\n` +
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
  // tool.execute.after - 后处理（更新本地计数器)
  // ------------------------------------------------------------------
  "tool.execute.after": async (input: any, output: any) => {
    const toolName = input.tool;
    const toolArgs = input.args || {};
    const outputResult = output?.result;

    // FileManager Cache更新
    if (toolName === "read" && toolArgs.filePath && outputResult) {
      fileManagerCache.update(toolArgs.filePath, outputResult);
    }

    // 更新 LoopDetector 本地计数器（记录失败）
    if (outputResult && (outputResult.error || outputResult.success === false)) {
      loopDetector.updateCounters(outputResult);
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
