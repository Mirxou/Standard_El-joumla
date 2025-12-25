"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Database,
  Download,
  Upload,
  RefreshCw,
  Shield,
  Clock,
  HardDrive,
  Save,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Calendar,
} from "lucide-react"
import { toast } from "sonner"

export default function BackupRestore() {
  const [isBackupDialogOpen, setIsBackupDialogOpen] = useState(false)

  const backupHistory = [
    {
      id: 1,
      name: "نسخة احتياطية تلقائية",
      date: "2024-11-17",
      time: "03:00 ص",
      size: "245 MB",
      type: "تلقائي",
      status: "مكتمل",
      files: "قاعدة البيانات + الملفات",
    },
    {
      id: 2,
      name: "نسخة احتياطية يدوية",
      date: "2024-11-16",
      time: "10:30 ص",
      size: "238 MB",
      type: "يدوي",
      status: "مكتمل",
      files: "قاعدة البيانات فقط",
    },
    {
      id: 3,
      name: "نسخة احتياطية تلقائية",
      date: "2024-11-16",
      time: "03:00 ص",
      size: "242 MB",
      type: "تلقائي",
      status: "مكتمل",
      files: "قاعدة البيانات + الملفات",
    },
    {
      id: 4,
      name: "نسخة احتياطية تلقائية",
      date: "2024-11-15",
      time: "03:00 ص",
      size: "240 MB",
      type: "تلقائي",
      status: "مكتمل",
      files: "قاعدة البيانات + الملفات",
    },
    {
      id: 5,
      name: "نسخة احتياطية أسبوعية",
      date: "2024-11-10",
      time: "02:00 ص",
      size: "235 MB",
      type: "تلقائي",
      status: "مكتمل",
      files: "قاعدة البيانات + الملفات",
    },
  ]

  const handleCreateBackup = () => {
    toast.success("جاري إنشاء النسخة الاحتياطية...")
    setTimeout(() => {
      toast.success("تم إنشاء النسخة الاحتياطية بنجاح")
      setIsBackupDialogOpen(false)
    }, 2000)
  }

  const handleDownloadBackup = (backupName: string) => {
    toast.info(`جاري تحميل ${backupName}...`)
  }

  const handleRestoreBackup = (backupName: string) => {
    toast.warning(`هل أنت متأكد من استعادة ${backupName}؟`)
  }

  const handleDeleteBackup = (backupName: string) => {
    toast.error(`تم حذف ${backupName}`)
  }

  const getTypeColor = (type: string) => {
    return type === "تلقائي" ? "bg-blue-100 text-blue-800" : "bg-purple-100 text-purple-800"
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">النسخ الاحتياطي والاستعادة</h1>
          <p className="text-gray-600">إدارة النسخ الاحتياطية واستعادة البيانات</p>
        </div>
        <Dialog open={isBackupDialogOpen} onOpenChange={setIsBackupDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Save className="h-4 w-4 ml-2" />
              إنشاء نسخة احتياطية
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-blue-600" />
                إنشاء نسخة احتياطية جديدة
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="backup-name">اسم النسخة الاحتياطية *</Label>
                <Input id="backup-name" placeholder="نسخة احتياطية يدوية - نوفمبر 2024" />
              </div>
              <div>
                <Label htmlFor="backup-type">نوع النسخة</Label>
                <Select defaultValue="full">
                  <SelectTrigger id="backup-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="full">كاملة (قاعدة البيانات + الملفات)</SelectItem>
                    <SelectItem value="database">قاعدة البيانات فقط</SelectItem>
                    <SelectItem value="files">الملفات فقط</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="backup-desc">الوصف (اختياري)</Label>
                <Textarea
                  id="backup-desc"
                  placeholder="وصف النسخة الاحتياطية..."
                  rows={3}
                />
              </div>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <div className="flex items-start gap-3">
                  <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-semibold text-blue-900 mb-1">ملاحظة مهمة:</p>
                    <p className="text-blue-700">
                      سيتم تشفير النسخة الاحتياطية تلقائياً لحماية بياناتك. قد تستغرق العملية
                      عدة دقائق حسب حجم البيانات.
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="outline" onClick={() => setIsBackupDialogOpen(false)}>
                  إلغاء
                </Button>
                <Button onClick={handleCreateBackup} className="bg-blue-600 hover:bg-blue-700">
                  <Save className="h-4 w-4 ml-2" />
                  إنشاء النسخة
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* معلومات النظام */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">النسخ المتوفرة</p>
                <p className="text-2xl font-bold text-blue-600">{backupHistory.length}</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-lg">
                <Database className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">الحجم الإجمالي</p>
                <p className="text-2xl font-bold text-green-600">1.2 GB</p>
              </div>
              <div className="bg-green-100 p-3 rounded-lg">
                <HardDrive className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">آخر نسخة</p>
                <p className="text-lg font-bold text-purple-600">اليوم</p>
                <p className="text-xs text-gray-500">03:00 ص</p>
              </div>
              <div className="bg-purple-100 p-3 rounded-lg">
                <Clock className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">النسخ التلقائية</p>
                <p className="text-2xl font-bold text-orange-600">مفعّل</p>
              </div>
              <div className="bg-orange-100 p-3 rounded-lg">
                <RefreshCw className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* الإعدادات التلقائية */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5 text-blue-600" />
            إعدادات النسخ الاحتياطي التلقائي
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-6">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-blue-600 p-2 rounded">
                  <Calendar className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-blue-900">النسخ اليومي</p>
                  <p className="text-sm text-blue-600">كل يوم الساعة 03:00 ص</p>
                </div>
              </div>
              <Badge className="bg-green-100 text-green-800">مفعّل</Badge>
            </div>

            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-purple-600 p-2 rounded">
                  <Calendar className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-purple-900">النسخ الأسبوعي</p>
                  <p className="text-sm text-purple-600">كل أحد الساعة 02:00 ص</p>
                </div>
              </div>
              <Badge className="bg-green-100 text-green-800">مفعّل</Badge>
            </div>

            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-orange-600 p-2 rounded">
                  <Calendar className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-orange-900">النسخ الشهري</p>
                  <p className="text-sm text-orange-600">أول كل شهر الساعة 01:00 ص</p>
                </div>
              </div>
              <Badge className="bg-green-100 text-green-800">مفعّل</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* سجل النسخ الاحتياطية */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>سجل النسخ الاحتياطية</CardTitle>
            <Button variant="outline" size="sm">
              <Upload className="h-4 w-4 ml-2" />
              استيراد نسخة
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {backupHistory.map((backup) => (
              <div
                key={backup.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-4">
                  <div className="bg-blue-100 p-3 rounded-lg">
                    <Database className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{backup.name}</h3>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {backup.date}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {backup.time}
                      </span>
                      <span className="flex items-center gap-1">
                        <HardDrive className="h-3 w-3" />
                        {backup.size}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge className={getTypeColor(backup.type)}>{backup.type}</Badge>
                      <Badge className="bg-green-100 text-green-800 flex items-center gap-1">
                        <CheckCircle className="h-3 w-3" />
                        {backup.status}
                      </Badge>
                      <span className="text-xs text-gray-500">{backup.files}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDownloadBackup(backup.name)}
                  >
                    <Download className="h-4 w-4 ml-1" />
                    تحميل
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-blue-600"
                    onClick={() => handleRestoreBackup(backup.name)}
                  >
                    <RefreshCw className="h-4 w-4 ml-1" />
                    استعادة
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-red-600 hover:text-red-700"
                    onClick={() => handleDeleteBackup(backup.name)}
                  >
                    <Trash2 className="h-4 w-4 ml-1" />
                    حذف
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* تحذيرات */}
      <Card className="border-orange-200 bg-orange-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-orange-900 mb-2">نصائح مهمة:</h3>
              <ul className="text-sm text-orange-800 space-y-1 list-disc list-inside">
                <li>احتفظ بنسخة احتياطية خارجية في مكان آمن</li>
                <li>تحقق من سلامة النسخ الاحتياطية بشكل دوري</li>
                <li>قم باختبار عملية الاستعادة للتأكد من صحتها</li>
                <li>لا تقم بحذف النسخ القديمة إلا بعد التأكد من النسخ الجديدة</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
