'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'

const TITLES: Record<string, string> = {
  '/': 'Production Dashboard',
  '/data': 'Data',
  '/account': 'Account',
  '/settings': 'Settings',
  '/help': 'Get Help',
}

export function Header() {
  const pathname = usePathname()
  const title = TITLES[pathname ?? '/'] ?? 'Production Dashboard'
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b bg-background px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 h-6" />
      <h1 className="font-semibold text-foreground tracking-tight">{title}</h1>
      <div className="ml-auto">
        {mounted ? (
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          >
            {theme === 'dark' ? <Sun className="size-4" /> : <Moon className="size-4" />}
            <span className="sr-only">Toggle theme</span>
          </Button>
        ) : (
          <div className="size-8 rounded-md bg-muted" />
        )}
      </div>
    </header>
  )
}
