param(
    [string]$GtkPath = "C:\Program Files\GTK3-Runtime Win64\bin"
)

if (-Not (Test-Path $GtkPath)) {
    Write-Host "❌ المسار $GtkPath غير موجود. تأكد من تثبيت GTK واستخدم المسار الصحيح."
    exit 1
}

$currentPath = [Environment]::GetEnvironmentVariable("PATH", [EnvironmentVariableTarget]::Machine)
if ($currentPath -notlike "*${GtkPath}*") {
    [Environment]::SetEnvironmentVariable("PATH", $currentPath + ";" + $GtkPath, [EnvironmentVariableTarget]::Machine)
    Write-Host "✅ تمت إضافة $GtkPath إلى متغير البيئة PATH (على مستوى النظام). أعد تشغيل الجهاز أو الترمينال."
} else {
    Write-Host "ℹ️ المسار $GtkPath موجود بالفعل في PATH."
}
