"use client"

import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent, CardHeader } from "@/components/ui/card"

/**
 * Skeleton pour les cartes de statistiques
 */
export function StatsCardSkeleton() {
  return (
    <Card className="glass-panel border-white/10">
      <CardHeader className="pb-3">
        <Skeleton className="h-4 w-24 bg-white/10" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-32 mb-2 bg-white/10" />
        <Skeleton className="h-3 w-20 bg-white/5" />
      </CardContent>
    </Card>
  )
}

/**
 * Skeleton pour les tableaux
 */
export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex gap-4 pb-3 border-b border-white/10">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1 bg-white/10" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div key={rowIdx} className="flex gap-4 py-3">
          {Array.from({ length: cols }).map((_, colIdx) => (
            <Skeleton key={colIdx} className="h-4 flex-1 bg-white/5" />
          ))}
        </div>
      ))}
    </div>
  )
}

/**
 * Skeleton pour les cartes de produits
 */
export function ProductCardSkeleton() {
  return (
    <Card className="glass-panel border-white/10">
      <CardHeader>
        <Skeleton className="h-32 w-full mb-4 bg-white/10" />
        <Skeleton className="h-5 w-3/4 mb-2 bg-white/10" />
        <Skeleton className="h-4 w-1/2 bg-white/5" />
      </CardHeader>
      <CardContent>
        <div className="flex justify-between items-center">
          <Skeleton className="h-6 w-20 bg-white/10" />
          <Skeleton className="h-8 w-24 bg-white/10" />
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Skeleton pour les formulaires
 */
export function FormSkeleton({ fields = 4 }: { fields?: number }) {
  return (
    <div className="space-y-6">
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-24 bg-white/10" />
          <Skeleton className="h-10 w-full bg-white/5" />
        </div>
      ))}
      <div className="flex gap-3 pt-4">
        <Skeleton className="h-10 w-24 bg-white/10" />
        <Skeleton className="h-10 w-24 bg-white/5" />
      </div>
    </div>
  )
}

/**
 * Skeleton pour le dashboard home
 */
export function DashboardHomeSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <Skeleton className="h-8 w-48 bg-white/10" />
        <Skeleton className="h-10 w-32 bg-white/10" />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <StatsCardSkeleton key={i} />
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="glass-panel border-white/10">
          <CardHeader>
            <Skeleton className="h-6 w-32 bg-white/10" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full bg-white/5" />
          </CardContent>
        </Card>
        <Card className="glass-panel border-white/10">
          <CardHeader>
            <Skeleton className="h-6 w-32 bg-white/10" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full bg-white/5" />
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="glass-panel border-white/10">
        <CardHeader>
          <Skeleton className="h-6 w-40 bg-white/10" />
        </CardHeader>
        <CardContent>
          <TableSkeleton rows={5} cols={4} />
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * Skeleton pour les listes de produits
 */
export function ProductListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  )
}

/**
 * Skeleton pour les pages de chargement complet
 */
export function PageSkeleton() {
  return (
    <div className="min-h-screen bg-[#0f172a] p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <DashboardHomeSkeleton />
      </div>
    </div>
  )
}
