import { useRef, useState } from 'react';
export function useAction() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const running = useRef(false);
  async function run(action: () => Promise<void>) {
    if (running.current) return;
    running.current = true;
    setPending(true);
    setError(null);
    try {
      await action();
    } catch (cause) {
      setError(cause instanceof Error ? cause : new Error('Request failed'));
    } finally {
      running.current = false;
      setPending(false);
    }
  }
  return { pending, error, run };
}
