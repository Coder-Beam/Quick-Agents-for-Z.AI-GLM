import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import type { Command } from 'commander';
import { safeReadDir, fileExists, readDescriptionFromFiles } from '../utils/common.js';

interface SkillOptions {
    registry?: string;
}

export async function skillCommand(action: string, name: string | undefined, options: SkillOptions, command: Command) {
    const cwd = process.cwd();
    const skillsDir = path.join(cwd, '.opencode/skills');
    
    switch (action) {
        case 'list':
            await listSkills(skillsDir);
            break;
        case 'install':
            await installSkill(skillsDir, name, options.registry);
            break;
        case 'remove':
            await removeSkill(skillsDir, name);
            break;
        case 'update':
            await updateSkill(skillsDir, name);
            break;
        default:
            console.log(chalk.red('未知操作: ' + action));
            console.log(chalk.yellow('可用操作: list, install, remove, update'));
    }
}

async function listSkills(skillsDir: string) {
    if (!await fileExists(skillsDir)) {
        console.log(chalk.yellow('技能目录不存在'));
        return;
    }
    
    const dirs = await safeReadDir(skillsDir);
    const skills = dirs.filter(d => !d.startsWith('.'));
    
    if (skills.length === 0) {
        console.log(chalk.yellow('没有找到技能'));
        return;
    }
    
    console.log(chalk.bold('\n已安装技能 (' + skills.length + '):\n'));
    
    for (const skill of skills) {
        const skillPath = path.join(skillsDir, skill);
        const stat = await fs.stat(skillPath);
        
        if (stat.isDirectory()) {
            const description = await readDescriptionFromFiles(skillPath, ['skill.md', 'README.md']);
            console.log('  ' + chalk.cyan(skill));
            if (description) {
                console.log('    ' + chalk.dim(description));
            }
        }
    }
}

async function installSkill(skillsDir: string, name: string | undefined, registry?: string) {
    if (!name) {
        console.log(chalk.red('请指定技能名称'));
        return;
    }
    
    const spinner = ora('安装技能 ' + name + '...').start();
    
    try {
        const skillPath = path.join(skillsDir, name);
        
        if (await fileExists(skillPath)) {
            spinner.warn(chalk.yellow('技能已存在: ' + name));
            return;
        }
        
        await fs.ensureDir(skillPath);
        
        const skillContent = `# ${name}

> 从 ${registry || '本地'} 安装的技能

## 描述

[待补充技能描述]

## 使用方式

[待补充使用说明]
`;
        
        await fs.writeFile(path.join(skillPath, 'skill.md'), skillContent);
        spinner.succeed(chalk.green('技能 ' + name + ' 安装成功'));
        
    } catch (error) {
        spinner.fail(chalk.red('安装失败'));
        console.error(error);
    }
}

async function removeSkill(skillsDir: string, name: string | undefined) {
    if (!name) {
        console.log(chalk.red('请指定技能名称'));
        return;
    }
    
    const skillPath = path.join(skillsDir, name);
    
    if (!await fileExists(skillPath)) {
        console.log(chalk.yellow('技能不存在: ' + name));
        return;
    }
    
    await fs.remove(skillPath);
    console.log(chalk.green('✓') + ' 技能 ' + chalk.cyan(name) + ' 已移除');
}

async function updateSkill(skillsDir: string, name: string | undefined) {
    if (name) {
        console.log(chalk.cyan('更新技能: ' + name));
    } else {
        console.log(chalk.cyan('更新所有技能...'));
    }
    console.log(chalk.yellow('请手动从仓库获取最新版本'));
}
