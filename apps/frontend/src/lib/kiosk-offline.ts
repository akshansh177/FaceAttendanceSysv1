const DB_NAME = "kiosk-offline";
const STORE = "events";
const DB_VERSION = 1;

export type OfflineKioskEvent = {
  id: string;
  deviceId: string;
  action: "check_in" | "check_out";
  frames: Blob[];
  ts: number;
};

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onerror = () => reject(req.error);
    req.onsuccess = () => resolve(req.result);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "id" });
      }
    };
  });
}

export async function enqueueOfflineEvent(event: OfflineKioskEvent): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(event);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function listOfflineEvents(): Promise<OfflineKioskEvent[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).getAll();
    req.onsuccess = () => resolve((req.result as OfflineKioskEvent[]) || []);
    req.onerror = () => reject(req.error);
  });
}

export async function removeOfflineEvent(id: string): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function flushOfflineQueue(
  send: (event: OfflineKioskEvent) => Promise<boolean>
): Promise<number> {
  if (!navigator.onLine) return 0;
  const events = await listOfflineEvents();
  let synced = 0;
  for (const ev of events.sort((a, b) => a.ts - b.ts)) {
    try {
      const ok = await send(ev);
      if (ok) {
        await removeOfflineEvent(ev.id);
        synced += 1;
      }
    } catch {
      break;
    }
  }
  return synced;
}
