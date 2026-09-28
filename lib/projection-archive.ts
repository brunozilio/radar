import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, rename, unlink } from 'node:fs/promises';
import path from 'node:path';
import { objectStorageEnabled, putImmutableStoredObject } from './object-storage.ts';

type Receipt = { schema: string; attemptId: string; referenceAt: string; status: string; generatedAt?: string; objects: { key: string; sha256: string; bytes: number }[] };
const hash = (bytes: Buffer) => createHash('sha256').update(bytes).digest('hex');

/** Publish all blobs before their receipt; retries never change existing evidence. */
export async function flushProjectionArchive(directory: string): Promise<void> {
  const archive = path.join(directory, 'archive');
  let names: string[];
  try { names = await readdir(path.join(archive, 'pending')); }
  catch (error) { if ((error as NodeJS.ErrnoException).code === 'ENOENT') return; throw error; }
  for (const name of names.filter(name => /^[A-Za-z0-9_-]{1,80}\.json$/.test(name)).sort()) {
    const source = path.join(archive, 'pending', name);
    const bytes = await readFile(source);
    const receipt: Receipt = JSON.parse(bytes.toString('utf8'));
    if (receipt.schema !== 'radar-archive-receipt/v1' || `${receipt.attemptId}.json` !== name || !Array.isArray(receipt.objects) || receipt.objects.length !== 2) throw new Error('Invalid archive receipt');
    for (const object of receipt.objects) {
      if (!/^[a-f0-9]{64}$/.test(object.sha256) || object.key !== `projection/blobs/${object.sha256}.tar.gz`) throw new Error('Invalid archive object');
      const localPath = path.join(archive, 'blobs', `${object.sha256}.tar.gz`);
      const blob = await readFile(localPath);
      if (hash(blob) !== object.sha256 || blob.length !== object.bytes) throw new Error('Archive integrity failure');
      await putImmutableStoredObject({ key: object.key, bytes: blob, mimeType: 'application/gzip', localPath });
    }
    const destination = path.join(archive, 'receipts', name);
    await putImmutableStoredObject({ key: `projection/receipts/${name}`, bytes, mimeType: 'application/json', localPath: destination });
    await mkdir(path.dirname(destination), { recursive: true });
    await rename(source, destination);
  }
  // Local-only deployments keep their full archive. In R2 deployments collect
  // only blobs not referenced by any still-pending attempt (shared runtime blobs).
  if (objectStorageEnabled()) {
    const pending = await readdir(path.join(archive, 'pending'));
    if (!pending.some(name => name.endsWith('.json'))) {
      const blobs = await readdir(path.join(archive, 'blobs')).catch(() => []);
      for (const blob of blobs.filter(name => /^[a-f0-9]{64}\.tar\.gz$/.test(name))) await unlink(path.join(archive, 'blobs', blob));
    }
  }
}

export async function requireArchivedReceipt(directory: string, key: unknown, expected: { attemptId: string; referenceAt: string; status: string; generatedAt?: string }): Promise<void> {
  if (typeof key !== 'string' || !/^projection\/receipts\/[A-Za-z0-9_-]{1,80}\.json$/.test(key)) throw new Error('Missing immutable forecast receipt');
  const receipt: Receipt = JSON.parse(await readFile(path.join(directory, 'archive', 'receipts', key.split('/').at(-1)!), 'utf8'));
  if (receipt.schema !== 'radar-archive-receipt/v1' || key !== `projection/receipts/${receipt.attemptId}.json` ||
      Date.parse(receipt.referenceAt) !== Date.parse(expected.referenceAt) || receipt.status !== expected.status ||
      (expected.status === 'calculated' ? receipt.generatedAt !== expected.generatedAt : receipt.attemptId !== expected.attemptId)) {
    throw new Error('Archive receipt does not match calculation');
  }
}
