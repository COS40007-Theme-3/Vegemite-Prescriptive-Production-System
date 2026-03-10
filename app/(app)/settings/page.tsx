'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'

const QUALITY_MODELS = [
  { value: 'xgboost', label: 'XGBoost', description: 'Gradient boosting, best for tabular quality prediction' },
  { value: 'lightgbm', label: 'LightGBM', description: 'Fast training, good for large datasets' },
  { value: 'catboost', label: 'CatBoost', description: 'Handles categoricals well, robust' },
  { value: 'random_forest', label: 'Random Forest', description: 'Ensemble, interpretable' },
]

const DOWNTIME_MODELS = [
  { value: 'xgboost', label: 'XGBoost', description: 'Default for downtime risk' },
  { value: 'lightgbm', label: 'LightGBM', description: 'Faster inference' },
  { value: 'logistic', label: 'Logistic Regression', description: 'Simple baseline' },
]

export default function SettingsPage() {
  const [qualityModel, setQualityModel] = useState('xgboost')
  const [downtimeModel, setDowntimeModel] = useState('xgboost')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.9)

  return (
    <main className="p-4 lg:p-6">
      <div className="w-full max-w-2xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Inference models</CardTitle>
            <CardDescription>
              Choose models used for quality prediction and downtime risk. Changes apply to the next run.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Quality prediction model</Label>
              <Select value={qualityModel} onValueChange={setQualityModel}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {QUALITY_MODELS.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Model used for good / low bad / high bad prediction from setpoints and sensors.
              </p>
            </div>
            <Separator />
            <div className="space-y-2">
              <Label className="text-sm font-medium">Downtime risk model</Label>
              <Select value={downtimeModel} onValueChange={setDowntimeModel}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {DOWNTIME_MODELS.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Model used to estimate downtime probability from current settings.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Dashboard</CardTitle>
            <CardDescription>Refresh and display options</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-sm font-medium">Auto-refresh charts</Label>
                <p className="text-xs text-muted-foreground">Update trend charts every 60s when dashboard is open</p>
              </div>
              <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
            </div>
            <Separator />
            <div className="space-y-2">
              <Label className="text-sm font-medium">Minimum confidence to show recommendation</Label>
              <div className="flex items-center gap-2">
                <Select
                  value={confidenceThreshold.toString()}
                  onValueChange={(v) => setConfidenceThreshold(parseFloat(v))}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0.8">80%</SelectItem>
                    <SelectItem value="0.85">85%</SelectItem>
                    <SelectItem value="0.9">90%</SelectItem>
                    <SelectItem value="0.95">95%</SelectItem>
                  </SelectContent>
                </Select>
                <Badge variant="outline">Current: {(confidenceThreshold * 100).toFixed(0)}%</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-muted">
          <CardHeader>
            <CardTitle className="text-base">About</CardTitle>
            <CardDescription>Vegemite Production AI · Theme 3</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Machine settings recommendation and downtime prediction. Models trained on production data (Theme 3).
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
