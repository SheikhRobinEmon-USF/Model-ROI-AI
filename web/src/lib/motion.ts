import { cubicOut } from 'svelte/easing'

const reduced = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches

/** Transition params that collapse to instant when the user prefers reduced motion. */
export const rise = (delay = 0) => ({ y: reduced ? 0 : 10, duration: reduced ? 0 : 320, delay: reduced ? 0 : delay, easing: cubicOut })
export const quick = { duration: reduced ? 0 : 160 }
export const pop = { start: reduced ? 1 : 0.97, duration: reduced ? 0 : 180, easing: cubicOut }
