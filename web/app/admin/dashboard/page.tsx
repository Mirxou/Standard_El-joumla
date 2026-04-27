'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, CheckCircle2, Clock, RefreshCw, Download, Server } from 'lucide-react'

interface Device {
  device_id: string
  device_name: string
  version: string
  last_sync: string
  status: 'online' | 'offline' | 'syncing' | 'error'
  memory_usage?: number
  today_sales?: number
  last_error?: string
  os?: string
  ip_address?: string
}

export default function DeveloperDashboard() {
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const fetchDevices = async () => {
    try {
      const response = await fetch('/api/v1/admin/devices')
      if (response.ok) {
        const data = await response.json()
        setDevices(data)
        setLastUpdate(new Date())
      }
    } catch (error) {
      console.error('Error fetching devices:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDevices()
    // تحديث كل 30 ثانية
    const interval = setInterval(fetchDevices, 30000)
    return () => clearInterval(interval)
  }, [])

  const triggerSync = async (deviceId: string) => {
    try {
      const response = await fetch(`/api/v1/admin/devices/${deviceId}/sync`, {
        method: 'POST'
      })
      if (response.ok) {
        await fetchDevices()
      }
    } catch (error) {
      console.error('Error triggering sync:', error)
    }
  }

  const getStatusBadge = (status: Device['status']) => {
    const variants: Record<Device['status'], { variant: 'default' | 'secondary' | 'destructive' | 'outline', icon: any, label: string }> = {
      online: { variant: 'default', icon: CheckCircle2, label: 'Online' },
      offline: { variant: 'secondary', icon: AlertCircle, label: 'Offline' },
      syncing: { variant: 'outline', icon: RefreshCw, label: 'Syncing' },
      error: { variant: 'destructive', icon: AlertCircle, label: 'Error' }
    }
    const config = variants[status] || variants.offline
    const Icon = config.icon
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    )
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleString('ar-SA', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateString
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Developer Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            لوحة تحكم المطور - مراقبة حالة جميع تطبيقات Desktop
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-muted-foreground">
            آخر تحديث: {lastUpdate.toLocaleTimeString('ar-SA')}
          </div>
          <Button onClick={fetchDevices} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            تحديث
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">إجمالي الأجهزة</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{devices.length}</div>
            <p className="text-xs text-muted-foreground">
              {devices.filter(d => d.status === 'online').length} متصل
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">الأجهزة المتصلة</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {devices.filter(d => d.status === 'online').length}
            </div>
            <p className="text-xs text-muted-foreground">
              {devices.length > 0 
                ? `${Math.round((devices.filter(d => d.status === 'online').length / devices.length) * 100)}%`
                : '0%'
              } من إجمالي الأجهزة
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">في المزامنة</CardTitle>
            <RefreshCw className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {devices.filter(d => d.status === 'syncing').length}
            </div>
            <p className="text-xs text-muted-foreground">أجهزة قيد المزامنة</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">المبيعات اليومية</CardTitle>
            <Download className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {devices.reduce((sum, d) => sum + (d.today_sales || 0), 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">من جميع الأجهزة</p>
          </CardContent>
        </Card>
      </div>

      {/* Devices Table */}
      <Card>
        <CardHeader>
          <CardTitle>الأجهزة المتصلة</CardTitle>
          <CardDescription>قائمة بجميع تطبيقات Desktop المتصلة</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : devices.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              لا توجد أجهزة متصلة
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>اسم الجهاز</TableHead>
                  <TableHead>الإصدار</TableHead>
                  <TableHead>الحالة</TableHead>
                  <TableHead>آخر مزامنة</TableHead>
                  <TableHead>الذاكرة</TableHead>
                  <TableHead>المبيعات اليومية</TableHead>
                  <TableHead>النظام</TableHead>
                  <TableHead>الإجراءات</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {devices.map((device) => (
                  <TableRow key={device.device_id}>
                    <TableCell className="font-medium">
                      <div>
                        <div>{device.device_name}</div>
                        {device.ip_address && (
                          <div className="text-xs text-muted-foreground">
                            {device.ip_address}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{device.version}</Badge>
                    </TableCell>
                    <TableCell>{getStatusBadge(device.status)}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        {formatDate(device.last_sync)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {device.memory_usage !== undefined ? (
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-secondary rounded-full h-2">
                            <div
                              className="bg-primary h-2 rounded-full"
                              style={{ width: `${device.memory_usage}%` }}
                            />
                          </div>
                          <span className="text-sm">{device.memory_usage.toFixed(1)}%</span>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {device.today_sales !== undefined 
                        ? device.today_sales.toLocaleString()
                        : '-'
                      }
                    </TableCell>
                    <TableCell>
                      {device.os || '-'}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => triggerSync(device.device_id)}
                          disabled={device.status === 'syncing'}
                        >
                          <RefreshCw className={`h-3 w-3 ${device.status === 'syncing' ? 'animate-spin' : ''}`} />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Error Logs */}
      {devices.some(d => d.last_error) && (
        <Card>
          <CardHeader>
            <CardTitle>الأخطاء الأخيرة</CardTitle>
            <CardDescription>سجلات الأخطاء من الأجهزة</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {devices
                .filter(d => d.last_error)
                .map((device) => (
                  <div key={device.device_id} className="p-3 border rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium">{device.device_name}</span>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(device.last_sync)}
                      </span>
                    </div>
                    <p className="text-sm text-destructive">{device.last_error}</p>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
