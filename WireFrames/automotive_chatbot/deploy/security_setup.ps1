# Security Setup Script for Automotive Chatbot (Windows)
# This script configures comprehensive security settings for Windows production environment

param(
    [switch]$Force,
    [string]$LogPath = "C:\Logs\SecuritySetup.log"
)

# Ensure running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator"
    exit 1
}

# Create log directory
$LogDir = Split-Path $LogPath -Parent
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage -ForegroundColor $(if($Level -eq "ERROR"){"Red"} elseif($Level -eq "WARN"){"Yellow"} else{"Green"})
    Add-Content -Path $LogPath -Value $LogMessage
}

function Write-LogError {
    param([string]$Message)
    Write-Log -Message $Message -Level "ERROR"
}

function Write-LogWarn {
    param([string]$Message)
    Write-Log -Message $Message -Level "WARN"
}

# Install Windows Features and Security Tools
function Install-SecurityFeatures {
    Write-Log "Installing Windows security features..."
    
    try {
        # Enable Windows Defender features
        Enable-WindowsOptionalFeature -Online -FeatureName "Windows-Defender-Default-Definitions" -All -NoRestart
        
        # Install Windows Subsystem for Linux (for security tools)
        Enable-WindowsOptionalFeature -Online -FeatureName "Microsoft-Windows-Subsystem-Linux" -All -NoRestart
        
        # Enable Hyper-V (for containerization security)
        Enable-WindowsOptionalFeature -Online -FeatureName "Microsoft-Hyper-V-All" -All -NoRestart
        
        Write-Log "Windows security features installed successfully"
    }
    catch {
        Write-LogError "Failed to install security features: $($_.Exception.Message)"
    }
}

# Configure Windows Firewall
function Configure-WindowsFirewall {
    Write-Log "Configuring Windows Firewall..."
    
    try {
        # Enable Windows Firewall for all profiles
        Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
        
        # Set default actions
        Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultInboundAction Block
        Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultOutboundAction Allow
        
        # Remove existing rules for our application
        Get-NetFirewallRule -DisplayName "Automotive Chatbot*" | Remove-NetFirewallRule -ErrorAction SilentlyContinue
        
        # Allow SSH (if OpenSSH is installed)
        New-NetFirewallRule -DisplayName "Automotive Chatbot - SSH" -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow
        
        # Allow HTTP and HTTPS
        New-NetFirewallRule -DisplayName "Automotive Chatbot - HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
        New-NetFirewallRule -DisplayName "Automotive Chatbot - HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
        
        # Allow application ports
        New-NetFirewallRule -DisplayName "Automotive Chatbot - Frontend" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow
        New-NetFirewallRule -DisplayName "Automotive Chatbot - Backend API" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
        New-NetFirewallRule -DisplayName "Automotive Chatbot - RASA Core" -Direction Inbound -Protocol TCP -LocalPort 5005 -Action Allow
        New-NetFirewallRule -DisplayName "Automotive Chatbot - RASA Actions" -Direction Inbound -Protocol TCP -LocalPort 5055 -Action Allow
        
        # Allow monitoring ports (restricted to local network)
        New-NetFirewallRule -DisplayName "Automotive Chatbot - Prometheus" -Direction Inbound -Protocol TCP -LocalPort 9090 -Action Allow -RemoteAddress LocalSubnet
        New-NetFirewallRule -DisplayName "Automotive Chatbot - Grafana" -Direction Inbound -Protocol TCP -LocalPort 3001 -Action Allow -RemoteAddress LocalSubnet
        New-NetFirewallRule -DisplayName "Automotive Chatbot - Node Exporter" -Direction Inbound -Protocol TCP -LocalPort 9100 -Action Allow -RemoteAddress LocalSubnet
        
        # Enable logging
        Set-NetFirewallProfile -Profile Domain,Public,Private -LogAllowed True -LogBlocked True -LogMaxSizeKilobytes 32767
        
        Write-Log "Windows Firewall configured successfully"
    }
    catch {
        Write-LogError "Failed to configure Windows Firewall: $($_.Exception.Message)"
    }
}

# Configure Windows Defender
function Configure-WindowsDefender {
    Write-Log "Configuring Windows Defender..."
    
    try {
        # Enable real-time protection
        Set-MpPreference -DisableRealtimeMonitoring $false
        
        # Enable cloud protection
        Set-MpPreference -MAPSReporting Advanced
        Set-MpPreference -SubmitSamplesConsent SendAllSamples
        
        # Configure scan settings
        Set-MpPreference -ScanAvgCPULoadFactor 50
        Set-MpPreference -CheckForSignaturesBeforeRunningScan $true
        
        # Enable network protection
        Set-MpPreference -EnableNetworkProtection Enabled
        
        # Configure exclusions for application directories
        Add-MpPreference -ExclusionPath "C:\automotive-chatbot"
        Add-MpPreference -ExclusionPath "C:\ProgramData\Docker"
        
        # Schedule daily quick scan
        $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command Start-MpScan -ScanType QuickScan"
        $Trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
        $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        Register-ScheduledTask -TaskName "Automotive Chatbot - Daily Antivirus Scan" -Action $Action -Trigger $Trigger -Principal $Principal -Force
        
        Write-Log "Windows Defender configured successfully"
    }
    catch {
        Write-LogError "Failed to configure Windows Defender: $($_.Exception.Message)"
    }
}

# Configure User Account Control (UAC)
function Configure-UAC {
    Write-Log "Configuring User Account Control..."
    
    try {
        # Set UAC to highest level
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "ConsentPromptBehaviorAdmin" -Value 2
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "ConsentPromptBehaviorUser" -Value 3
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "EnableInstallerDetection" -Value 1
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "EnableLUA" -Value 1
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "EnableVirtualization" -Value 1
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "PromptOnSecureDesktop" -Value 1
        
        Write-Log "User Account Control configured successfully"
    }
    catch {
        Write-LogError "Failed to configure UAC: $($_.Exception.Message)"
    }
}

# Configure Windows Update
function Configure-WindowsUpdate {
    Write-Log "Configuring Windows Update..."
    
    try {
        # Install PSWindowsUpdate module if not present
        if (!(Get-Module -ListAvailable -Name PSWindowsUpdate)) {
            Install-Module -Name PSWindowsUpdate -Force -AllowClobber
        }
        
        # Configure automatic updates
        $AutoUpdatePath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
        if (!(Test-Path $AutoUpdatePath)) {
            New-Item -Path $AutoUpdatePath -Force | Out-Null
        }
        
        # Enable automatic updates
        Set-ItemProperty -Path $AutoUpdatePath -Name "NoAutoUpdate" -Value 0
        Set-ItemProperty -Path $AutoUpdatePath -Name "AUOptions" -Value 4  # Auto download and install
        Set-ItemProperty -Path $AutoUpdatePath -Name "ScheduledInstallDay" -Value 0  # Every day
        Set-ItemProperty -Path $AutoUpdatePath -Name "ScheduledInstallTime" -Value 3  # 3 AM
        
        # Schedule weekly update check
        $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command Get-WUInstall -AcceptAll -AutoReboot"
        $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "01:00AM"
        $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        Register-ScheduledTask -TaskName "Automotive Chatbot - Weekly Windows Update" -Action $Action -Trigger $Trigger -Principal $Principal -Force
        
        Write-Log "Windows Update configured successfully"
    }
    catch {
        Write-LogError "Failed to configure Windows Update: $($_.Exception.Message)"
    }
}

# Configure Event Log Monitoring
function Configure-EventLogMonitoring {
    Write-Log "Configuring Event Log monitoring..."
    
    try {
        # Increase security log size
        wevtutil sl Security /ms:1073741824  # 1GB
        wevtutil sl System /ms:536870912     # 512MB
        wevtutil sl Application /ms:536870912 # 512MB
        
        # Enable audit policies
        auditpol /set /category:"Logon/Logoff" /success:enable /failure:enable
        auditpol /set /category:"Account Logon" /success:enable /failure:enable
        auditpol /set /category:"Account Management" /success:enable /failure:enable
        auditpol /set /category:"Privilege Use" /success:enable /failure:enable
        auditpol /set /category:"System" /success:enable /failure:enable
        
        # Create event log monitoring script
        $MonitorScript = @'
# Event Log Monitor for Automotive Chatbot
param([string]$LogPath = "C:\Logs\SecurityEvents.log")

$Events = @(
    @{LogName="Security"; ID=4625; Description="Failed logon"},
    @{LogName="Security"; ID=4648; Description="Logon with explicit credentials"},
    @{LogName="Security"; ID=4720; Description="User account created"},
    @{LogName="Security"; ID=4726; Description="User account deleted"},
    @{LogName="System"; ID=7034; Description="Service crashed"},
    @{LogName="System"; ID=7035; Description="Service started/stopped"}
)

$StartTime = (Get-Date).AddHours(-1)

foreach ($Event in $Events) {
    $EventLogs = Get-WinEvent -FilterHashtable @{LogName=$Event.LogName; ID=$Event.ID; StartTime=$StartTime} -ErrorAction SilentlyContinue
    
    if ($EventLogs) {
        foreach ($Log in $EventLogs) {
            $Message = "[{0}] {1} - {2}: {3}" -f $Log.TimeCreated, $Event.LogName, $Event.Description, $Log.Message
            Add-Content -Path $LogPath -Value $Message
        }
    }
}
'@
        
        $MonitorScript | Out-File -FilePath "C:\Scripts\EventLogMonitor.ps1" -Encoding UTF8 -Force
        
        # Create scripts directory
        if (!(Test-Path "C:\Scripts")) {
            New-Item -ItemType Directory -Path "C:\Scripts" -Force | Out-Null
        }
        
        # Schedule hourly event log monitoring
        $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\Scripts\EventLogMonitor.ps1"
        $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)
        $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        Register-ScheduledTask -TaskName "Automotive Chatbot - Event Log Monitor" -Action $Action -Trigger $Trigger -Principal $Principal -Force
        
        Write-Log "Event Log monitoring configured successfully"
    }
    catch {
        Write-LogError "Failed to configure Event Log monitoring: $($_.Exception.Message)"
    }
}

# Configure Registry Security
function Configure-RegistrySecurity {
    Write-Log "Configuring Registry security settings..."
    
    try {
        # Disable unnecessary services
        $ServicesToDisable = @(
            "Telnet",
            "RemoteRegistry",
            "Messenger",
            "NetMeeting Remote Desktop Sharing"
        )
        
        foreach ($Service in $ServicesToDisable) {
            $ServiceObj = Get-Service -Name $Service -ErrorAction SilentlyContinue
            if ($ServiceObj) {
                Stop-Service -Name $Service -Force -ErrorAction SilentlyContinue
                Set-Service -Name $Service -StartupType Disabled -ErrorAction SilentlyContinue
                Write-Log "Disabled service: $Service"
            }
        }
        
        # Configure network security settings
        $NetworkSecurityPath = "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
        Set-ItemProperty -Path $NetworkSecurityPath -Name "SynAttackProtect" -Value 1
        Set-ItemProperty -Path $NetworkSecurityPath -Name "EnableICMPRedirect" -Value 0
        Set-ItemProperty -Path $NetworkSecurityPath -Name "DisableIPSourceRouting" -Value 2
        
        # Configure SMB security
        $SMBPath = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
        Set-ItemProperty -Path $SMBPath -Name "RequireSecuritySignature" -Value 1
        Set-ItemProperty -Path $SMBPath -Name "EnableSecuritySignature" -Value 1
        
        # Disable LLMNR and NetBIOS
        $LLMNRPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient"
        if (!(Test-Path $LLMNRPath)) {
            New-Item -Path $LLMNRPath -Force | Out-Null
        }
        Set-ItemProperty -Path $LLMNRPath -Name "EnableMulticast" -Value 0
        
        Write-Log "Registry security settings configured successfully"
    }
    catch {
        Write-LogError "Failed to configure Registry security: $($_.Exception.Message)"
    }
}

# Configure Application Security
function Configure-ApplicationSecurity {
    Write-Log "Configuring application security settings..."
    
    try {
        # Create application directory with proper permissions
        $AppPath = "C:\automotive-chatbot"
        if (!(Test-Path $AppPath)) {
            New-Item -ItemType Directory -Path $AppPath -Force | Out-Null
        }
        
        # Set directory permissions
        $Acl = Get-Acl $AppPath
        $Acl.SetAccessRuleProtection($true, $false)
        
        # Add SYSTEM full control
        $SystemRule = New-Object System.Security.AccessControl.FileSystemAccessRule("SYSTEM", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
        $Acl.SetAccessRule($SystemRule)
        
        # Add Administrators full control
        $AdminRule = New-Object System.Security.AccessControl.FileSystemAccessRule("Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
        $Acl.SetAccessRule($AdminRule)
        
        # Add application service account read/execute
        $ServiceRule = New-Object System.Security.AccessControl.FileSystemAccessRule("IIS_IUSRS", "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow")
        $Acl.SetAccessRule($ServiceRule)
        
        Set-Acl -Path $AppPath -AclObject $Acl
        
        # Create secure configuration directory
        $ConfigPath = "C:\automotive-chatbot\config"
        if (!(Test-Path $ConfigPath)) {
            New-Item -ItemType Directory -Path $ConfigPath -Force | Out-Null
        }
        
        # Restrict config directory access
        $ConfigAcl = Get-Acl $ConfigPath
        $ConfigAcl.SetAccessRuleProtection($true, $false)
        $ConfigAcl.SetAccessRule($SystemRule)
        $ConfigAcl.SetAccessRule($AdminRule)
        Set-Acl -Path $ConfigPath -AclObject $ConfigAcl
        
        Write-Log "Application security settings configured successfully"
    }
    catch {
        Write-LogError "Failed to configure application security: $($_.Exception.Message)"
    }
}

# Configure Backup Security
function Configure-BackupSecurity {
    Write-Log "Configuring backup security..."
    
    try {
        # Create backup script
        $BackupScript = @'
# Secure Backup Script for Automotive Chatbot
param(
    [string]$BackupPath = "C:\Backups",
    [string]$EncryptionPassword = "AutoChatBot2024!"
)

$Date = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupPath\automotive_chatbot_backup_$Date.zip"

# Create backup directory
if (!(Test-Path $BackupPath)) {
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
}

# Backup application files
Compress-Archive -Path "C:\automotive-chatbot" -DestinationPath $BackupFile -Force

# Encrypt backup (requires 7-Zip)
if (Test-Path "C:\Program Files\7-Zip\7z.exe") {
    & "C:\Program Files\7-Zip\7z.exe" a -p"$EncryptionPassword" "$BackupFile.7z" "$BackupFile"
    Remove-Item $BackupFile -Force
}

# Clean old backups (keep 7 days)
Get-ChildItem $BackupPath -Filter "*.7z" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item -Force

Write-Host "Backup completed: $BackupFile.7z"
'@
        
        $BackupScript | Out-File -FilePath "C:\Scripts\SecureBackup.ps1" -Encoding UTF8 -Force
        
        # Schedule daily backup
        $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\Scripts\SecureBackup.ps1"
        $Trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
        $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        Register-ScheduledTask -TaskName "Automotive Chatbot - Daily Backup" -Action $Action -Trigger $Trigger -Principal $Principal -Force
        
        Write-Log "Backup security configured successfully"
    }
    catch {
        Write-LogError "Failed to configure backup security: $($_.Exception.Message)"
    }
}

# Main execution function
function Main {
    Write-Log "Starting Windows security setup for Automotive Chatbot..."
    
    try {
        Install-SecurityFeatures
        Configure-WindowsFirewall
        Configure-WindowsDefender
        Configure-UAC
        Configure-WindowsUpdate
        Configure-EventLogMonitoring
        Configure-RegistrySecurity
        Configure-ApplicationSecurity
        Configure-BackupSecurity
        
        Write-Log "Security setup completed successfully!"
        Write-Log "Please review the configuration and test all services"
        Write-Log "Remember to:"
        Write-Log "  1. Update email addresses in monitoring scripts"
        Write-Log "  2. Configure AWS CLI for cloud backups"
        Write-Log "  3. Test firewall rules and adjust as needed"
        Write-Log "  4. Set up SSL certificates for HTTPS"
        Write-Log "  5. Configure monitoring alerts"
        
        Write-LogWarn "System may require a reboot to apply all changes"
        
        if ($Force) {
            Write-Log "Force parameter specified, rebooting system in 60 seconds..."
            shutdown /r /t 60 /c "Security configuration completed, rebooting system"
        }
    }
    catch {
        Write-LogError "Security setup failed: $($_.Exception.Message)"
        exit 1