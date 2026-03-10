'use client'

import type { KeyboardEvent as ReactKeyboardEvent } from 'react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Search as SearchIcon, X } from 'lucide-react'
import { useSearch } from '@/context/search-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

export function FloatingSearch() {
  const { isOpen, closeSearch } = useSearch()
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen) {
      setQuery('')
      inputRef.current?.focus()
    }
  }, [isOpen])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeSearch()
    }
    if (isOpen) {
      window.addEventListener('keydown', onKeyDown)
      return () => window.removeEventListener('keydown', onKeyDown)
    }
  }, [isOpen, closeSearch])

  const findInPage = useCallback(() => {
    if (typeof window === 'undefined') return
    const win = window as typeof window & { find?: (...args: unknown[]) => boolean }
    const q = query.trim()
    if (!q) return

    // Use native browser find to highlight + scroll to next occurrence.
    // First call: search from current cursor, case-insensitive, forward, wrap enabled.
    if (!win.find) return

    const found = win.find(q, false, false, true, false, true, false)

    // If nothing found, clear selection and search again from top.
    if (!found) {
      win.getSelection?.()?.removeAllRanges()
      win.find(q, false, false, true, false, true, false)
    }
  }, [query])

  const onKeyDown = (e: ReactKeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      findInPage()
    }
  }

  if (!isOpen) return null

  return (
    <div
      className={cn(
        'fixed left-1/2 top-16 z-50 w-full max-w-xl -translate-x-1/2',
        'rounded-lg border bg-background shadow-lg',
        'animate-in fade-in-0 zoom-in-95 duration-200',
      )}
    >
      <div className="flex items-center gap-2 p-2">
        <SearchIcon className="size-4 shrink-0 text-muted-foreground" />
        <Input
          ref={inputRef}
          type="search"
          placeholder="Search in dashboard…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          className="h-9 flex-1 border-0 bg-transparent shadow-none focus-visible:ring-0"
          autoComplete="off"
        />
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-8 shrink-0"
          onClick={closeSearch}
          aria-label="Close"
        >
          <X className="size-4" />
        </Button>
      </div>
      <p className="border-t px-3 py-1.5 text-xs text-muted-foreground">Enter to jump, Esc to close.</p>
    </div>
  )
}
