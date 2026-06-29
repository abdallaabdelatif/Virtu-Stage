import { useCallback, useEffect, useRef, useState } from 'react';

export function useTransientMessages(duration = 5000) {
  const [messages, setMessages] = useState<string[]>([]);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const scheduleClear = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setMessages([]), duration);
  }, [duration]);

  const replaceMessages = useCallback(
    (next: string[]) => {
      setMessages(next);
      scheduleClear();
    },
    [scheduleClear],
  );

  const appendMessage = useCallback(
    (message: string) => {
      setMessages((current) => [...current, message]);
      scheduleClear();
    },
    [scheduleClear],
  );

  useEffect(
    () => () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    },
    [],
  );

  return { messages, replaceMessages, appendMessage };
}
