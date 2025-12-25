"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import {
  Users,
  Plus,
  Search,
  Shield,
  Edit,
  Trash2,
  Mail,
  Phone,
  Calendar,
  Lock,
  UserCheck,
  UserX,
} from "lucide-react"
import { toast } from "sonner"
import { useEffect } from "react"
import { fetchFromAPI } from "@/lib/db/client"

export default function UsersManagement() {
  const [searchTerm, setSearchTerm] = useState("")
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)

  const [users, setUsers] = useState<any[]>([])

  const loadUsers = async () => {
    try {
      const response = await fetchFromAPI('/users');
      if (response && Array.isArray(response.users)) {
        const mapped = response.users.map((u: any) => ({
          id: u.user_id,
          name: u.full_name || u.username,
          email: u.username, // using username as email representation for now if email missing
          phone: "-", // Not in UserInfo response
          role: "مستخدم", // Placeholder, role_id mapping needed
          status: u.is_active ? "نشط" : "غير نشط",
          lastLogin: "-",
          createdAt: "-",
          permissions: [],
        }));
        setUsers(mapped);
      }
    } catch (e) {
      console.error(e);
      toast.error("فشل تحميل المستخدمين");
    }
  }

  useEffect(() => {
    loadUsers();
  }, [])

  const getRoleColor = (role: string) => {
    switch (role) {
      case "مدير النظام":
        return "bg-red-100 text-red-800"
      case "محاسب":
        return "bg-blue-100 text-blue-800"
      case "مدير مخزون":
        return "bg-purple-100 text-purple-800"
      case "موظف مبيعات":
        return "bg-green-100 text-green-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getStatusColor = (status: string) => {
    return status === "نشط" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
  }

  const filteredUsers = users.filter(
    (user) =>
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.role.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleAddUser = () => {
    toast.success("تم إضافة المستخدم بنجاح")
    setIsAddDialogOpen(false)
  }

  const handleToggleStatus = (userName: string, currentStatus: string) => {
    const newStatus = currentStatus === "نشط" ? "غير نشط" : "نشط"
    toast.info(`تم ${newStatus === "نشط" ? "تفعيل" : "إيقاف"} حساب ${userName}`)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">إدارة المستخدمين</h1>
          <p className="text-gray-600">إدارة المستخدمين والصلاحيات والوصول</p>
        </div>
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="h-4 w-4 ml-2" />
              إضافة مستخدم
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-blue-600" />
                إضافة مستخدم جديد
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="user-name">الاسم الكامل *</Label>
                  <Input id="user-name" placeholder="أحمد محمد" />
                </div>
                <div>
                  <Label htmlFor="user-email">البريد الإلكتروني *</Label>
                  <Input id="user-email" type="email" placeholder="user@standard.com" />
                </div>
                <div>
                  <Label htmlFor="user-phone">رقم الجوال</Label>
                  <Input id="user-phone" type="tel" placeholder="05XXXXXXXX" />
                </div>
                <div>
                  <Label htmlFor="user-role">الدور الوظيفي *</Label>
                  <Select>
                    <SelectTrigger id="user-role">
                      <SelectValue placeholder="اختر الدور" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="admin">مدير النظام</SelectItem>
                      <SelectItem value="accountant">محاسب</SelectItem>
                      <SelectItem value="inventory">مدير مخزون</SelectItem>
                      <SelectItem value="sales">موظف مبيعات</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="user-password">كلمة المرور *</Label>
                  <Input id="user-password" type="password" placeholder="••••••••" />
                </div>
                <div>
                  <Label htmlFor="user-password-confirm">تأكيد كلمة المرور *</Label>
                  <Input id="user-password-confirm" type="password" placeholder="••••••••" />
                </div>
              </div>

              <div className="space-y-3">
                <Label>الصلاحيات</Label>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm">إدارة المبيعات</span>
                    <Switch />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm">إدارة المخزون</span>
                    <Switch />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm">إدارة التقارير</span>
                    <Switch />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm">إدارة المستخدمين</span>
                    <Switch />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  إلغاء
                </Button>
                <Button onClick={handleAddUser} className="bg-blue-600 hover:bg-blue-700">
                  <Users className="h-4 w-4 ml-2" />
                  إضافة المستخدم
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* البحث */}
      <div className="relative">
        <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <Input
          placeholder="البحث عن مستخدم..."
          className="pr-10"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* إحصائيات */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي المستخدمين</p>
                <p className="text-2xl font-bold text-blue-600">{users.length}</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-lg">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">نشط</p>
                <p className="text-2xl font-bold text-green-600">
                  {users.filter((u) => u.status === "نشط").length}
                </p>
              </div>
              <div className="bg-green-100 p-3 rounded-lg">
                <UserCheck className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">غير نشط</p>
                <p className="text-2xl font-bold text-gray-600">
                  {users.filter((u) => u.status === "غير نشط").length}
                </p>
              </div>
              <div className="bg-gray-100 p-3 rounded-lg">
                <UserX className="h-6 w-6 text-gray-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">المسؤولين</p>
                <p className="text-2xl font-bold text-red-600">
                  {users.filter((u) => u.role === "مدير النظام").length}
                </p>
              </div>
              <div className="bg-red-100 p-3 rounded-lg">
                <Shield className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* قائمة المستخدمين */}
      <Card>
        <CardHeader>
          <CardTitle>المستخدمين ({filteredUsers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredUsers.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-4">
                  <Avatar className="h-12 w-12">
                    <AvatarFallback className="bg-blue-100 text-blue-600 font-semibold">
                      {user.name
                        .split(" ")
                        .slice(0, 2)
                        .map((n: string) => n[0])
                        .join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h3 className="font-semibold text-gray-900">{user.name}</h3>
                    <div className="flex items-center gap-3 mt-1">
                      <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Mail className="h-3 w-3" />
                        {user.email}
                      </div>
                      <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Phone className="h-3 w-3" />
                        {user.phone}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge className={getRoleColor(user.role)}>{user.role}</Badge>
                      <Badge className={getStatusColor(user.status)}>{user.status}</Badge>
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        آخر دخول: {user.lastLogin}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleToggleStatus(user.name, user.status)}
                  >
                    {user.status === "نشط" ? (
                      <>
                        <Lock className="h-4 w-4 ml-1" />
                        إيقاف
                      </>
                    ) : (
                      <>
                        <UserCheck className="h-4 w-4 ml-1" />
                        تفعيل
                      </>
                    )}
                  </Button>
                  <Button size="sm" variant="outline">
                    <Edit className="h-4 w-4 ml-1" />
                    تعديل
                  </Button>
                  <Button size="sm" variant="outline" className="text-red-600 hover:text-red-700">
                    <Trash2 className="h-4 w-4 ml-1" />
                    حذف
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
