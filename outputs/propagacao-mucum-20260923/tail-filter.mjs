import { spawn } from 'node:child_process';
import { appendFileSync } from 'node:fs';
const child = spawn('node', ['node_modules/wrangler/bin/wrangler.js', 'tail', 'sofik-monitoramento-taquari', '--format', 'json'], { stdio: ['ignore', 'pipe', 'pipe'] });
let pending = '', depth = 0, quoted = false, escaped = false;
child.stdout.on('data', chunk => {
  for (const c of chunk.toString()) {
    if (!depth && c !== '{') continue;
    pending += c;
    if (quoted) { if (escaped) escaped = false; else if (c === '\\') escaped = true; else if (c === '"') quoted = false; }
    else if (c === '"') quoted = true;
    else if (c === '{') depth++;
    else if (c === '}') depth--;
    if (!depth) {
      try {
        const e = JSON.parse(pending), url = e.event?.request?.url || '';
        if (url.includes('projection') || e.event?.cron || e.logs?.length || e.exceptions?.length) {
          const safe = { at: e.eventTimestamp, outcome: e.outcome, entrypoint: e.entrypoint, url: url.split('?')[0], method: e.event?.request?.method, status: e.event?.response?.status, cron: e.event?.cron, logs: e.logs, exceptions: e.exceptions };
          const line = JSON.stringify(safe) + '\n';
          appendFileSync('outputs/propagacao-mucum-20260923/live-tail.jsonl', line);
          process.stdout.write(line);
        }
      } catch {}
      pending = '';
    }
  }
});
child.stderr.on('data', chunk => process.stderr.write(chunk));
process.on('SIGINT', () => { child.kill('SIGTERM'); process.exit(); });
process.on('SIGTERM', () => { child.kill('SIGTERM'); process.exit(); });
child.on('exit', code => process.exit(code ?? 1));
