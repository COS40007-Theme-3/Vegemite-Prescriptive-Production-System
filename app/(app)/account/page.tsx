'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Mail, Building2, Calendar, Shield } from 'lucide-react'

const MOCK = {
  name: 'Minh Hoang',
  email: 'minh.hoang@vegemite.au',
  role: 'Production Engineer',
  department: 'Paste Production',
  lastLogin: '17 Feb 2026, 09:42',
  memberSince: 'March 2023',
  initials: 'MH',
}

export default function AccountPage() {
  return (
    <main className="p-4 lg:p-6">
      <div className="w-full max-w-2xl mx-auto space-y-6">
        <Card>
          <CardHeader className="flex flex-row items-center gap-4 space-y-0 pb-2">
            <Avatar className="h-20 w-20 rounded-lg">
              <AvatarFallback className="rounded-lg text-2xl font-semibold bg-primary/10 text-primary">
                {MOCK.initials}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 space-y-1">
              <CardTitle className="text-xl">{MOCK.name}</CardTitle>
              <CardDescription>{MOCK.role}</CardDescription>
              <Badge variant="secondary" className="mt-1">
                <Shield className="mr-1 h-3 w-3" />
                Standard access
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Separator />
            <div className="grid gap-4">
              <div className="flex items-center gap-3 text-sm">
                <Mail className="h-4 w-4 text-muted-foreground shrink-0" />
                <div>
                  <p className="text-muted-foreground">Email</p>
                  <p className="font-medium">{MOCK.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
                <div>
                  <p className="text-muted-foreground">Department</p>
                  <p className="font-medium">{MOCK.department}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground shrink-0" />
                <div>
                  <p className="text-muted-foreground">Last login</p>
                  <p className="font-medium">{MOCK.lastLogin}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground shrink-0" />
                <div>
                  <p className="text-muted-foreground">Member since</p>
                  <p className="font-medium">{MOCK.memberSince}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Security</CardTitle>
            <CardDescription>Password and session</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Change password and manage sessions from Settings.
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
