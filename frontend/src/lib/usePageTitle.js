import { useEffect } from 'react'

/** Sets document.title for the current page; restores nothing on unmount by design. */
export function usePageTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} — TariffCheck` : 'TariffCheck — Find the duty you overpaid'
  }, [title])
}
