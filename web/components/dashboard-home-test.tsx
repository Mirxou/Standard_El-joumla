"use client"

import React, { useState, useEffect } from "react"
import { Loader2 } from "lucide-react"

interface DashboardHomeProps {
  setActiveView?: (view: string) => void
}

export default function DashboardHomeTest({ setActiveView }: DashboardHomeProps) {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(false)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1>Test Dashboard</h1>
    </div>
  )
}

