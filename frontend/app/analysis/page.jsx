'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, AlertTriangle } from 'lucide-react'

export default function Analysis() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Analysis</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            AI Analysis Dashboard
          </CardTitle>
          <CardDescription>
            Monitor and manage AI analysis of intelligence articles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <AlertTriangle className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Analysis Dashboard Coming Soon</h3>
            <p className="text-gray-500">
              This feature will provide detailed insights into AI analysis performance and results.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}