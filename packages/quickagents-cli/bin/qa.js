#!/usr/bin/env node

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { pathToFileURL } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 动态导入编译后的入口文件
const distPath = join(__dirname, '../dist/index.js');
const distUrl = pathToFileURL(distPath).href;

import(distUrl)
  .catch((err) => {
    console.error('Failed to start QuickAgents CLI:');
    console.error(err);
    process.exit(1);
  });
