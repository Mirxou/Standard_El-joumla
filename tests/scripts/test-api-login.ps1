# PowerShell script لاختبار Login API
# Test Login API using PowerShell

param(
    [string]$BaseUrl = "http://localhost:8000",
    [switch]$CreateUser
)

Write-Host "🧪 اختبار Login API على: $BaseUrl" -ForegroundColor Cyan
Write-Host "=" * 50

# إنشاء مستخدم تجريبي إذا طُلب
if ($CreateUser) {
    Write-Host "`n🔧 إنشاء مستخدم تجريبي..." -ForegroundColor Yellow
    python scripts/test_login.py --create-user
    Write-Host ""
}

# بيانات Login
$loginData = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

Write-Host "📤 Request:" -ForegroundColor Green
Write-Host "   URL: $BaseUrl/api/v1/auth/login"
Write-Host "   Method: POST"
Write-Host "   Body: $loginData"

try {
    # طلب Login
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" `
        -Method Post `
        -Body $loginData `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    Write-Host "`n📥 Response:" -ForegroundColor Green
    Write-Host "   ✅ Login نجح!" -ForegroundColor Green
    
    Write-Host "`n📋 بيانات الاستجابة:" -ForegroundColor Cyan
    Write-Host "   Access Token: $($response.access_token.Substring(0, [Math]::Min(50, $response.access_token.Length)))..."
    Write-Host "   Token Type: $($response.token_type)"
    Write-Host "   User ID: $($response.user_id)"
    Write-Host "   Username: $($response.username)"
    
    # حفظ Token
    $token = $response.access_token
    
    # اختبار Protected Endpoint
    Write-Host "`n🔒 اختبار Protected Endpoint: /api/v1/auth/me" -ForegroundColor Cyan
    Write-Host "=" * 50
    
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $meResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/me" `
        -Method Get `
        -Headers $headers `
        -ErrorAction Stop
    
    Write-Host "`n📋 بيانات المستخدم:" -ForegroundColor Cyan
    $meResponse | ConvertTo-Json -Depth 10 | Write-Host
    
    Write-Host "`n✅ جميع الاختبارات نجحت!" -ForegroundColor Green
    
} catch {
    Write-Host "`n❌ خطأ:" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   Status Code: $statusCode" -ForegroundColor Red
        
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            $errorData = $responseBody | ConvertFrom-Json
            Write-Host "   Error: $($errorData.detail)" -ForegroundColor Red
        } catch {
            Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "   $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "`n💡 تأكد من أن الـ API يعمل:" -ForegroundColor Yellow
        Write-Host "   uvicorn src.api.app:app --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
    }
}

Write-Host "`n" + ("=" * 50)
Write-Host "✅ انتهى الاختبار" -ForegroundColor Cyan

