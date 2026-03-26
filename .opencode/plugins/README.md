# OpenCode 插件目录

此目录用于存放项目级 OpenCode 插件。

## 插件类型

OpenCode 支持以下类型的插件：

1. **JavaScript/TypeScript 插件**: 通过 JS/TS 模块扩展 OpenCode 核心功能
2. **MCP 服务器插件**: 集成 Model Context Protocol 服务器
3. **命令插件**: 添加自定义命令
4. **工具插件**: 添加自定义工具

## 插件目录结构

```
.opencode/plugins/
├── plugin-name/
│   ├── package.json         # 插件元数据
│   ├── index.js/ts         # 插件入口
│   ├── README.md           # 插件说明
│   └── assets/            # 静态资源（可选）
```

## 基本插件模板

### package.json

```json
{
  "name": "my-opencode-plugin",
  "version": "1.0.0",
  "description": "My custom OpenCode plugin",
  "main": "index.js",
  "opencode": {
    "type": "extension",
    "hooks": {
      "onInit": "onInit",
      "onExit": "onExit"
    }
  }
}
```

### index.js

```javascript
module.exports = {
  onInit(context) {
    console.log('Plugin initialized');
    // 初始化逻辑
  },
  
  onExit(context) {
    console.log('Plugin exiting');
    // 清理逻辑
  }
};
```

## 插件配置

在项目根目录的 `opencode.json` 中启用插件：

```json
{
  "plugins": {
    "my-plugin": {
      "enabled": true,
      "option1": "value1"
    }
  }
}
```

## 注意事项

1. 插件需要遵循 OpenCode 插件规范
2. 插件会自动加载，无需额外配置
3. 插件可以访问 OpenCode 的核心 API
4. 确保插件不会影响 OpenCode 的性能

## 相关文档

- [OpenCode 插件文档](https://opencode.ai/docs/plugins/)
- [OpenCode 配置文档](https://opencode.ai/docs/config/#plugins)
