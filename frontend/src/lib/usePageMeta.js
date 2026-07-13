import { useEffect } from 'react'

// Single source of truth for absolute URLs; swap when the custom domain lands.
export const SITE_URL = 'https://tariffcheck-zeta.vercel.app'

function ensureHeadEl(selector, create) {
  let el = document.head.querySelector(selector)
  if (!el) {
    el = create()
    document.head.appendChild(el)
  }
  return el
}

function setMeta(attr, key, content) {
  const el = ensureHeadEl(`meta[${attr}="${key}"]`, () => {
    const m = document.createElement('meta')
    m.setAttribute(attr, key)
    return m
  })
  el.setAttribute('content', content)
}

/**
 * Per-route title, meta description, canonical and OG tags. The static
 * index.html used to ship one hardcoded canonical pointing every route at
 * the homepage — which told crawlers all 11 pages were duplicates of "/".
 */
export function usePageMeta({ title, description, path } = {}) {
  useEffect(() => {
    const fullTitle = title ? `${title} — TariffCheck` : 'TariffCheck — Find the duty you overpaid'
    document.title = fullTitle

    const url = SITE_URL + (path ?? window.location.pathname)
    const canon = ensureHeadEl('link[rel="canonical"]', () => {
      const l = document.createElement('link')
      l.setAttribute('rel', 'canonical')
      return l
    })
    canon.setAttribute('href', url)

    if (description) {
      setMeta('name', 'description', description)
      setMeta('property', 'og:description', description)
    }
    setMeta('property', 'og:title', fullTitle)
    setMeta('property', 'og:url', url)
  }, [title, description, path])
}
