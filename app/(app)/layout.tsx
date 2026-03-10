'use client'

import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/app-sidebar'
import { Header } from '@/components/header'
import { FloatingSearch } from '@/components/floating-search'
import { SearchProvider } from '@/context/search-context'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SearchProvider>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset className="flex h-dvh flex-col overflow-hidden">
          <Header />
          <FloatingSearch />
          <div className="flex-1 overflow-auto min-h-0">
            {children}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </SearchProvider>
  )
}
