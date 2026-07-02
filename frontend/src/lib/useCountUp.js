import { useEffect, useRef, useState } from 'react'

const reduceMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

/**
 * Animates a number from 0 to `target` with an ease-out curve.
 * Starts after `startDelay` ms once `enabled` is true.
 * With prefers-reduced-motion, snaps straight to the target.
 */
export function useCountUp(target, { duration = 900, startDelay = 0, enabled = true } = {}) {
  const [value, setValue] = useState(() => (reduceMotion() ? target : 0))
  const rafRef = useRef()

  useEffect(() => {
    if (!enabled) return
    if (reduceMotion()) { setValue(target); return }
    let start
    const timer = setTimeout(() => {
      const tick = now => {
        if (start === undefined) start = now
        const t = Math.min((now - start) / duration, 1)
        const eased = 1 - Math.pow(1 - t, 3)
        setValue(target * eased)
        if (t < 1) rafRef.current = requestAnimationFrame(tick)
      }
      rafRef.current = requestAnimationFrame(tick)
    }, startDelay)
    // rAF can be throttled in background/headless contexts — guarantee the final value
    const settle = setTimeout(() => setValue(target), startDelay + duration + 200)
    return () => { clearTimeout(timer); clearTimeout(settle); cancelAnimationFrame(rafRef.current) }
  }, [target, duration, startDelay, enabled])

  return value
}

export function formatUsd(n) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
