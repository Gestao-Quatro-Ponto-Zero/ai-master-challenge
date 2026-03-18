import { useState, useEffect, useCallback, useRef } from 'react';
import { setPresence, heartbeat, getPresence } from '../services/presenceService';
import type { OperatorStatus } from '../types';

const HEARTBEAT_INTERVAL_MS = 30_000;

export function usePresence(userId: string | undefined) {
  const [status, setStatus] = useState<OperatorStatus>('online');
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const updateStatus = useCallback(
    async (next: OperatorStatus) => {
      if (!userId) return;
      setStatus(next);
      await setPresence(userId, next).catch(() => {});
    },
    [userId],
  );

  useEffect(() => {
    if (!userId) return;

    let cancelled = false;

    async function init() {
      const existing = await getPresence(userId!).catch(() => null);
      if (!cancelled) {
        const initial = existing?.status === 'offline' ? 'online' : (existing?.status ?? 'online');
        setStatus(initial as OperatorStatus);
        await setPresence(userId!, initial as OperatorStatus).catch(() => {});
      }
    }

    init();

    intervalRef.current = setInterval(() => {
      if (!document.hidden) {
        heartbeat(userId).catch(() => {});
      }
    }, HEARTBEAT_INTERVAL_MS);

    function onVisibilityChange() {
      if (document.hidden) {
        setPresence(userId!, 'away').catch(() => {});
        setStatus('away');
      } else {
        setPresence(userId!, 'online').catch(() => {});
        setStatus('online');
      }
    }

    document.addEventListener('visibilitychange', onVisibilityChange);

    async function onBeforeUnload() {
      await setPresence(userId!, 'offline').catch(() => {});
    }

    window.addEventListener('beforeunload', onBeforeUnload);

    return () => {
      cancelled = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
      document.removeEventListener('visibilitychange', onVisibilityChange);
      window.removeEventListener('beforeunload', onBeforeUnload);
      setPresence(userId!, 'offline').catch(() => {});
    };
  }, [userId]);

  return { status, updateStatus };
}
