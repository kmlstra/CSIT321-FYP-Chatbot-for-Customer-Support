# API端点测试脚本
# 测试所有服务的API端点可用性

Write-Host "=== API端点测试开始 ===" -ForegroundColor Green
Write-Host ""

# 定义测试端点
$endpoints = @(
    @{Name="Backend API"; URL="http://localhost:8000/health"; Port=8000},
    @{Name="Rasa Server"; URL="http://localhost:5005/status"; Port=5005},
    @{Name="Rasa Actions"; URL="http://localhost:5055/health"; Port=5055},
    @{Name="Frontend"; URL="http://localhost:3000"; Port=3000}
)

# 测试结果统计
$successCount = 0
$totalCount = $endpoints.Count

foreach ($endpoint in $endpoints) {
    Write-Host "测试 $($endpoint.Name) (端口 $($endpoint.Port))..." -NoNewline
    
    try {
        # 使用Invoke-WebRequest测试端点
        $response = Invoke-WebRequest -Uri $endpoint.URL -Method GET -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host " ✅ 成功 (状态码: $($response.StatusCode))" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host " ⚠️ 警告 (状态码: $($response.StatusCode))" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host " ❌ 失败 - $($_.Exception.Message)" -ForegroundColor Red
        
        # 尝试测试端口是否开放
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.ConnectAsync("localhost", $endpoint.Port).Wait(3000)
            if ($tcpClient.Connected) {
                Write-Host "   端口 $($endpoint.Port) 已开放，但HTTP请求失败" -ForegroundColor Yellow
                $tcpClient.Close()
            } else {
                Write-Host "   端口 $($endpoint.Port) 未开放" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "   端口 $($endpoint.Port) 未开放" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "=== 测试结果汇总 ===" -ForegroundColor Cyan
Write-Host "成功: $successCount/$totalCount" -ForegroundColor Green
Write-Host "失败: $($totalCount - $successCount)/$totalCount" -ForegroundColor Red

if ($successCount -eq $totalCount) {
    Write-Host "🎉 所有API端点测试通过！" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️ 部分API端点测试失败，请检查服务状态" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=== Docker服务状态检查 ===" -ForegroundColor Cyan
try {
    $dockerServices = docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    Write-Host $dockerServices
} catch {
    Write-Host "无法获取Docker服务状态: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 测试完成 ===" -ForegroundColor Green