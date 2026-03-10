import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { HelpCircle, Book, Mail, MessageCircle } from 'lucide-react'

export default function HelpPage() {
  return (
    <main className="p-4 lg:p-6">
      <div className="mx-auto max-w-2xl w-full space-y-6">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <HelpCircle className="size-6" />
            Help Centre
          </h2>
          <p className="text-muted-foreground mt-1">
            How to use the Vegemite Production Dashboard and frequently asked questions.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Book className="size-5" />
              Quick start
            </CardTitle>
            <CardDescription>
              Basic steps to get started with the dashboard.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>
              <strong>Dashboard</strong> shows a production overview: predicted quality, downtime risk, and alerts.
            </p>
            <p>
              <strong>Settings</strong> let you choose AI models (Quality, Downtime), turn auto-refresh on/off, and set the confidence threshold.
            </p>
            <p>
              Use <strong>Search</strong> (magnifying glass icon) to find any text on the page.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Frequently asked questions</CardTitle>
            <CardDescription>Answers to common questions.</CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="faq-1">
                <AccordionTrigger>How do I change the quality prediction model?</AccordionTrigger>
                <AccordionContent>
                  Go to <strong>Settings</strong> → &quot;Quality prediction model&quot; → select XGBoost, LightGBM, CatBoost or Random Forest. Save to apply.
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="faq-2">
                <AccordionTrigger>How is downtime risk calculated?</AccordionTrigger>
                <AccordionContent>
                  The system uses an ML model (default XGBoost) to predict downtime probability from sensor and historical data. The confidence threshold can be adjusted in Settings.
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="faq-3">
                <AccordionTrigger>Can I turn off auto-refresh?</AccordionTrigger>
                <AccordionContent>
                  Yes. In <strong>Settings</strong>, turn off the &quot;Auto-refresh dashboard&quot; switch. The dashboard will not update automatically until you turn it back on or refresh the page.
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="size-5" />
              Contact support
            </CardTitle>
            <CardDescription>
              Need more help? Send an email or open a ticket.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p className="flex items-center gap-2">
              <Mail className="size-4 text-muted-foreground" />
              <a href="mailto:support@example.com" className="text-primary underline underline-offset-4">
                support@example.com
              </a>
            </p>
            <p className="text-muted-foreground">
              Response time: within 24 business hours.
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
