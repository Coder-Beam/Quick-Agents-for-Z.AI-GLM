import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';
import type { Command } from 'commander';
import { fileExists, getNestedValue, setNestedValue, deleteNestedKey } from '../utils/common.js';

export async function configCommand(action: string, key: string | undefined, value: string | undefined, command: Command) {
    const cwd = process.cwd();
    const configPath = path.join(cwd, '.opencode/opencode.json');
    
    if (!await fileExists(configPath)) {
        console.log(chalk.red('配置文件不存在'));
        console.log(chalk.yellow('请先运行 qa init 初始化项目'));
        return;
    }
    
    switch (action) {
        case 'get':
            await getConfig(configPath, key);
            break;
        case 'set':
            await setConfigCmd(configPath, key, value);
            break;
        case 'list':
            await listConfig(configPath);
            break;
        case 'reset':
            await resetConfig(configPath, key);
            break;
        default:
            console.log(chalk.red('未知操作: ' + action));
            console.log(chalk.yellow('可用操作: get, set, list, reset'));
    }
}

async function getConfig(configPath: string, key: string | undefined) {
    if (!key) {
        console.log(chalk.red('请指定配置键'));
        return;
    }
    
    const config = await fs.readJson(configPath);
    const keys = key.split('.');
    const val = getNestedValue(config, keys);
    
    if (val === undefined) {
        console.log(chalk.yellow('配置键不存在: ' + key));
        return;
    }
    
    console.log(chalk.cyan(key) + ' = ' + chalk.green(JSON.stringify(val)));
}

async function setConfigCmd(configPath: string, key: string | undefined, value: string | undefined) {
    if (!key || value === undefined) {
        console.log(chalk.red('请指定配置键和值'));
        return;
    }
    
    const config = await fs.readJson(configPath);
    const keys = key.split('.');
    
    let parsedValue: unknown = value;
    try {
        parsedValue = JSON.parse(value);
    } catch {
        // 保持字符串
    }
    
    const newConfig = setNestedValue(config, keys, parsedValue);
    await fs.writeJson(configPath, newConfig, { spaces: 2 });
    console.log(chalk.green('✓') + ' 配置已更新: ' + chalk.cyan(key) + ' = ' + chalk.green(JSON.stringify(parsedValue)));
}

async function listConfig(configPath: string) {
    const config = await fs.readJson(configPath);
    console.log(chalk.bold('\n当前配置:\n'));
    printConfig(config, '');
}

function printConfig(obj: Record<string, unknown>, prefix: string) {
    for (const [key, value] of Object.entries(obj)) {
        const fullKey = prefix ? prefix + '.' + key : key;
        
        if (value && typeof value === 'object' && !Array.isArray(value)) {
            console.log(chalk.dim(fullKey + ':'));
            printConfig(value as Record<string, unknown>, fullKey);
        } else {
            console.log('  ' + chalk.cyan(fullKey) + ' = ' + chalk.green(JSON.stringify(value)));
        }
    }
}

async function resetConfig(configPath: string, key: string | undefined) {
    if (!key) {
        console.log(chalk.red('请指定要重置的配置键'));
        return;
    }
    
    const config = await fs.readJson(configPath);
    const keys = key.split('.');
    const newConfig = deleteNestedKey(config, keys);
    
    if (newConfig === null) {
        console.log(chalk.yellow('配置键不存在: ' + key));
        return;
    }
    
    await fs.writeJson(configPath, newConfig, { spaces: 2 });
    console.log(chalk.green('✓') + ' 配置已重置: ' + chalk.cyan(key));
}
