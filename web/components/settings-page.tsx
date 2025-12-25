"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import {
  Settings,
  Building2,
  Bell,
  Shield,
  Database,
  Palette,
  Users,
  Mail,
  Save,
  RefreshCw,
} from "lucide-react"
import { toast } from "sonner"

export default function SettingsPage() {
  const [companyName, setCompanyName] = useState("Standard")
  const [companySlogan, setCompanySlogan] = useState("شعارنا للأبد")
  const [companyEmail, setCompanyEmail] = useState("info@standard.com")
  const [companyPhone, setCompanyPhone] = useState("0500000000")
  const [taxNumber, setTaxNumber] = useState("300000000000003")
  const [address, setAddress] = useState("الرياض - المملكة العربية السعودية")

  const [currency, setCurrency] = useState("SAR")
  const [language, setLanguage] = useState("ar")
  const [dateFormat, setDateFormat] = useState("DD/MM/YYYY")
  const [timeZone, setTimeZone] = useState("Asia/Riyadh")

  const [lowStockThreshold, setLowStockThreshold] = useState("10")
  const [criticalStockThreshold, setCriticalStockThreshold] = useState("5")
  const [expiryWarningDays, setExpiryWarningDays] = useState("30")

  const [emailNotifications, setEmailNotifications] = useState(true)
  const [smsNotifications, setSmsNotifications] = useState(false)
  const [lowStockAlerts, setLowStockAlerts] = useState(true)
  const [expiryAlerts, setExpiryAlerts] = useState(true)
  const [newOrderAlerts, setNewOrderAlerts] = useState(true)

  const [primaryColor, setPrimaryColor] = useState("#2563eb")
  const [secondaryColor, setSecondaryColor] = useState("#10b981")
  const [theme, setTheme] = useState("light")

  const handleSaveCompanyInfo = () => {
    toast.success("تم حفظ معلومات الشركة بنجاح")
  }

  const handleSaveSystemSettings = () => {
    toast.success("تم حفظ إعدادات النظام بنجاح")
  }

  const handleSaveInventorySettings = () => {
    toast.success("تم حفظ إعدادات المخزون بنجاح")
  }

  const handleSaveNotificationSettings = () => {
    toast.success("تم حفظ إعدادات التنبيهات بنجاح")
  }

  const handleSaveAppearanceSettings = () => {
    toast.success("تم حفظ إعدادات المظهر بنجاح")
  }

  const handleResetToDefaults = () => {
    toast.info("تم إعادة تعيين الإعدادات الافتراضية")
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">الإعدادات</h1>
          <p className="text-gray-600">إدارة إعدادات النظام والتخصيص الكامل</p>
        </div>
        <Button variant="outline" onClick={handleResetToDefaults}>
          <RefreshCw className="h-4 w-4 ml-2" />
          إعادة تعيين
        </Button>
      </div>

      <Tabs defaultValue="company" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="company">
            <Building2 className="h-4 w-4 ml-2" />
            الشركة
          </TabsTrigger>
          <TabsTrigger value="system">
            <Settings className="h-4 w-4 ml-2" />
            النظام
          </TabsTrigger>
          <TabsTrigger value="inventory">
            <Database className="h-4 w-4 ml-2" />
            المخزون
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="h-4 w-4 ml-2" />
            التنبيهات
          </TabsTrigger>
          <TabsTrigger value="appearance">
            <Palette className="h-4 w-4 ml-2" />
            المظهر
          </TabsTrigger>
        </TabsList>

        {/* معلومات الشركة */}
        <TabsContent value="company" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-blue-600" />
                معلومات الشركة
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="company-name">اسم الشركة *</Label>
                  <Input
                    id="company-name"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="company-slogan">الشعار</Label>
                  <Input
                    id="company-slogan"
                    value={companySlogan}
                    onChange={(e) => setCompanySlogan(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="company-email">البريد الإلكتروني</Label>
                  <Input
                    id="company-email"
                    type="email"
                    value={companyEmail}
                    onChange={(e) => setCompanyEmail(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="company-phone">رقم الهاتف</Label>
                  <Input
                    id="company-phone"
                    value={companyPhone}
                    onChange={(e) => setCompanyPhone(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="tax-number">الرقم الضريبي</Label>
                  <Input
                    id="tax-number"
                    value={taxNumber}
                    onChange={(e) => setTaxNumber(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="address">العنوان الكامل</Label>
                <Textarea
                  id="address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  rows={3}
                />
              </div>
              <div className="flex justify-end">
                <Button onClick={handleSaveCompanyInfo} className="bg-blue-600 hover:bg-blue-700">
                  <Save className="h-4 w-4 ml-2" />
                  حفظ التغييرات
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* إعدادات النظام */}
        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-green-600" />
                إعدادات النظام العامة
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="currency">العملة الافتراضية</Label>
                  <Select value={currency} onValueChange={setCurrency}>
                    <SelectTrigger id="currency">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="SAR">ريال سعودي (SAR)</SelectItem>
                      <SelectItem value="USD">دولار أمريكي (USD)</SelectItem>
                      <SelectItem value="EUR">يورو (EUR)</SelectItem>
                      <SelectItem value="AED">درهم إماراتي (AED)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="language">اللغة</Label>
                  <Select value={language} onValueChange={setLanguage}>
                    <SelectTrigger id="language">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ar">العربية</SelectItem>
                      <SelectItem value="en">English</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="date-format">تنسيق التاريخ</Label>
                  <Select value={dateFormat} onValueChange={setDateFormat}>
                    <SelectTrigger id="date-format">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                      <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                      <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="timezone">المنطقة الزمنية</Label>
                  <Select value={timeZone} onValueChange={setTimeZone}>
                    <SelectTrigger id="timezone">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Asia/Riyadh">الرياض (GMT+3)</SelectItem>
                      <SelectItem value="Asia/Dubai">دبي (GMT+4)</SelectItem>
                      <SelectItem value="Africa/Cairo">القاهرة (GMT+2)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex justify-end">
                <Button onClick={handleSaveSystemSettings} className="bg-green-600 hover:bg-green-700">
                  <Save className="h-4 w-4 ml-2" />
                  حفظ التغييرات
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* إعدادات المخزون */}
        <TabsContent value="inventory" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-purple-600" />
                إعدادات إدارة المخزون
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="low-stock">حد المخزون المنخفض</Label>
                  <Input
                    id="low-stock"
                    type="number"
                    value={lowStockThreshold}
                    onChange={(e) => setLowStockThreshold(e.target.value)}
                  />
                  <p className="text-xs text-gray-500 mt-1">عدد القطع</p>
                </div>
                <div>
                  <Label htmlFor="critical-stock">حد المخزون الحرج</Label>
                  <Input
                    id="critical-stock"
                    type="number"
                    value={criticalStockThreshold}
                    onChange={(e) => setCriticalStockThreshold(e.target.value)}
                  />
                  <p className="text-xs text-gray-500 mt-1">عدد القطع</p>
                </div>
                <div>
                  <Label htmlFor="expiry-warning">تنبيه انتهاء الصلاحية</Label>
                  <Input
                    id="expiry-warning"
                    type="number"
                    value={expiryWarningDays}
                    onChange={(e) => setExpiryWarningDays(e.target.value)}
                  />
                  <p className="text-xs text-gray-500 mt-1">أيام قبل الانتهاء</p>
                </div>
              </div>
              <div className="flex justify-end">
                <Button onClick={handleSaveInventorySettings} className="bg-purple-600 hover:bg-purple-700">
                  <Save className="h-4 w-4 ml-2" />
                  حفظ التغييرات
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* إعدادات التنبيهات */}
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-orange-600" />
                إعدادات التنبيهات والإشعارات
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Mail className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="font-medium">إشعارات البريد الإلكتروني</p>
                      <p className="text-sm text-gray-500">إرسال التنبيهات عبر البريد</p>
                    </div>
                  </div>
                  <Switch checked={emailNotifications} onCheckedChange={setEmailNotifications} />
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Bell className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium">إشعارات SMS</p>
                      <p className="text-sm text-gray-500">إرسال التنبيهات عبر الرسائل النصية</p>
                    </div>
                  </div>
                  <Switch checked={smsNotifications} onCheckedChange={setSmsNotifications} />
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Database className="h-5 w-5 text-orange-600" />
                    <div>
                      <p className="font-medium">تنبيهات المخزون المنخفض</p>
                      <p className="text-sm text-gray-500">عند وصول المخزون للحد الأدنى</p>
                    </div>
                  </div>
                  <Switch checked={lowStockAlerts} onCheckedChange={setLowStockAlerts} />
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Shield className="h-5 w-5 text-red-600" />
                    <div>
                      <p className="font-medium">تنبيهات انتهاء الصلاحية</p>
                      <p className="text-sm text-gray-500">عند اقتراب موعد انتهاء المنتجات</p>
                    </div>
                  </div>
                  <Switch checked={expiryAlerts} onCheckedChange={setExpiryAlerts} />
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Users className="h-5 w-5 text-purple-600" />
                    <div>
                      <p className="font-medium">تنبيهات الطلبات الجديدة</p>
                      <p className="text-sm text-gray-500">عند استلام طلب جديد</p>
                    </div>
                  </div>
                  <Switch checked={newOrderAlerts} onCheckedChange={setNewOrderAlerts} />
                </div>
              </div>
              <div className="flex justify-end">
                <Button onClick={handleSaveNotificationSettings} className="bg-orange-600 hover:bg-orange-700">
                  <Save className="h-4 w-4 ml-2" />
                  حفظ التغييرات
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* إعدادات المظهر */}
        <TabsContent value="appearance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5 text-pink-600" />
                إعدادات المظهر والألوان
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="theme">السمة</Label>
                  <Select value={theme} onValueChange={setTheme}>
                    <SelectTrigger id="theme">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">فاتح</SelectItem>
                      <SelectItem value="dark">داكن</SelectItem>
                      <SelectItem value="auto">تلقائي</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="primary-color">اللون الرئيسي</Label>
                  <div className="flex gap-2">
                    <Input
                      id="primary-color"
                      type="color"
                      value={primaryColor}
                      onChange={(e) => setPrimaryColor(e.target.value)}
                      className="h-10 w-20"
                    />
                    <Input value={primaryColor} readOnly className="flex-1" />
                  </div>
                </div>
                <div>
                  <Label htmlFor="secondary-color">اللون الثانوي</Label>
                  <div className="flex gap-2">
                    <Input
                      id="secondary-color"
                      type="color"
                      value={secondaryColor}
                      onChange={(e) => setSecondaryColor(e.target.value)}
                      className="h-10 w-20"
                    />
                    <Input value={secondaryColor} readOnly className="flex-1" />
                  </div>
                </div>
              </div>
              <div className="p-4 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">معاينة الألوان:</p>
                <div className="flex gap-3">
                  <div
                    className="h-16 w-16 rounded-lg shadow-md"
                    style={{ backgroundColor: primaryColor }}
                  />
                  <div
                    className="h-16 w-16 rounded-lg shadow-md"
                    style={{ backgroundColor: secondaryColor }}
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <Button onClick={handleSaveAppearanceSettings} className="bg-pink-600 hover:bg-pink-700">
                  <Save className="h-4 w-4 ml-2" />
                  حفظ التغييرات
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
