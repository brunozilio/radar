// Public reads and a separate local SQLite fixture; no worker or notifications.
import { mkdir, writeFile } from 'node:fs/promises';
import { SACE_LEVEL_SENSORS } from '../../lib/hydro.ts';
import { collectLevelReadings, readLevelHistory } from '../../lib/river-levels.ts';
const root = new URL('./browser-data/', import.meta.url).pathname;
process.env.MONITORA_DATA_DIR = root;
process.env.MONITORA_DB_PATH = `${root}monitoramento.sqlite`;
delete process.env.OBJECT_STORAGE_URL;
const { openWriterDatabase } = await import('../../lib/database.ts');
const db = openWriterDatabase();
await mkdir(`${root}receipts`, {recursive:true});
try {
  const audit = [];
  for (const sensor of SACE_LEVEL_SENSORS) {
    const result = await collectLevelReadings(sensor, async (url, timeout) => {
      const response = await fetch(url, { signal: AbortSignal.timeout(timeout), headers: {'Cache-Control':'no-cache'} });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const body = await response.text();
      await writeFile(`${root}receipts/${sensor.code}-${new URL(url).hostname}.txt`, body);
      return body;
    }, (source, rows) => {
      for (const row of rows) {
        if (source === 'SACE/SGB') db.prepare('INSERT OR REPLACE INTO sace_readings VALUES (?, ?, ?, ?, ?)').run(sensor.code,row.timestamp,row.level,row.levelCm,new Date().toISOString());
        else db.prepare("INSERT OR REPLACE INTO river_readings VALUES (?, ?, ?, ?, NULL, 'unknown', ?, ?)").run(sensor.code,row.timestamp,row.level,row.levelCm,source,new Date().toISOString());
      }
    });
    const current = readLevelHistory(db, sensor.code, 3).at(-1);
    audit.push({city:sensor.city,station:sensor.code,sources:result,current});
    console.log(JSON.stringify(audit.at(-1)));
  }
  await writeFile(new URL('./level-collection.json',import.meta.url), JSON.stringify(audit,null,2));
} finally { db.close(); }
