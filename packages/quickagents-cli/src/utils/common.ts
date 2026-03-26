import fs from 'fs-extra';
import path from 'path';

export async function safeReadDir(dir: string): Promise<string[]> {
    if (!await fs.pathExists(dir)) return [];
    return fs.readdir(dir);
}

export async function safeReadFile(filePath: string): Promise<string | null> {
    if (!await fs.pathExists(filePath)) return null;
    return fs.readFile(filePath, 'utf-8');
}

export async function fileExists(filePath: string): Promise<boolean> {
    return fs.pathExists(filePath);
}

export function getNestedValue(obj: Record<string, unknown>, keys: string[]): unknown {
    let current: unknown = obj;
    for (const key of keys) {
        if (current && typeof current === 'object' && key in current) {
            current = (current as Record<string, unknown>)[key];
        } else {
            return undefined;
        }
    }
    return current;
}

export function setNestedValue(obj: Record<string, unknown>, keys: string[], value: unknown): Record<string, unknown> {
    const result = JSON.parse(JSON.stringify(obj));
    let current: unknown = result;
    
    for (let i = 0; i < keys.length - 1; i++) {
        const k = keys[i];
        if (typeof current !== 'object' || current === null) {
            (result as Record<string, unknown>)[k] = {};
        }
        current = (current as Record<string, unknown>)[k];
        if (typeof current !== 'object' || current === null) {
            (result as Record<string, unknown>)[keys[i]] = {};
            current = (result as Record<string, unknown>)[keys[i]];
        }
    }
    
    if (typeof current === 'object' && current !== null) {
        (current as Record<string, unknown>)[keys[keys.length - 1]] = value;
    }
    return result;
}

export function deleteNestedKey(obj: Record<string, unknown>, keys: string[]): Record<string, unknown> | null {
    const result = JSON.parse(JSON.stringify(obj));
    let current: unknown = result;
    
    for (let i = 0; i < keys.length - 1; i++) {
        const k = keys[i];
        if (typeof current !== 'object' || current === null || !(k in current)) {
            return null;
        }
        current = (current as Record<string, unknown>)[k];
    }
    
    if (typeof current === 'object' && current !== null) {
        delete (current as Record<string, unknown>)[keys[keys.length - 1]];
    }
    return result;
}

export async function readDescriptionFromFiles(basePath: string, fileNames: string[]): Promise<string> {
    for (const fileName of fileNames) {
        const filePath = path.join(basePath, fileName);
        if (await fs.pathExists(filePath)) {
            try {
                const content = await fs.readFile(filePath, 'utf-8');
                const lines = content.split('\n').filter(l => l.trim() && !l.startsWith('#') && !l.startsWith('---'));
                if (lines.length > 0) {
                    return lines[0].substring(0, 80);
                }
            } catch {
                continue;
            }
        }
    }
    return '';
}

export function formatTimestamp(): string {
    return new Date().toLocaleString('zh-CN');
}
