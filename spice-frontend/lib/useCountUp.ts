import { useEffect, useRef, useState } from "react";

/**
 * Count-up animation for hero numbers (DR4 motion).
 * Eases from `from` to `to` over `duration` ms once `run` is true.
 */
export function useCountUp(to: number, run: boolean, duration = 900, from = 0): number {
  const [value, setValue] = useState(run ? from : to);
  const raf = useRef<number>();

  useEffect(() => {
    if (!run) {
      setValue(to);
      return;
    }
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(from + (to - from) * eased);
      if (t < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [to, run, duration, from]);

  return value;
}
