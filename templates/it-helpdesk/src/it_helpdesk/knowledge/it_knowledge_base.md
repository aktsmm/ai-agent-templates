# IT Knowledge Base

## Password & Account Management

### Password Reset — Self-Service

1. Go to https://passwordreset.company.com
2. Enter your corporate email address
3. Verify your identity via:
   - SMS code to registered mobile
   - Microsoft Authenticator push notification
   - Security questions (backup method)
4. Create a new password meeting these requirements:
   - Minimum 12 characters
   - At least 1 uppercase, 1 lowercase, 1 number, 1 special character
   - Cannot reuse last 10 passwords
   - Cannot contain your name or username
5. Sign out of all sessions and sign back in with the new password

**If self-service fails**: Contact the IT Service Desk at ext. 5000 or email helpdesk@company.com.

### Account Lockout

Accounts lock after 5 failed login attempts within 15 minutes.

**Resolution Steps**:
1. Wait 30 minutes for automatic unlock, OR
2. Use the self-service portal at https://passwordreset.company.com, OR
3. Call IT Service Desk (ext. 5000) for immediate unlock

**Common Causes**:
- Saved passwords in old browser sessions
- Mobile email client using old password
- Cached credentials in mapped network drives
- VPN client using old credentials

### Multi-Factor Authentication (MFA) Setup

**Supported MFA Methods**:
- Microsoft Authenticator app (recommended)
- SMS verification code
- Hardware security key (FIDO2)

**Setup Steps**:
1. Go to https://mysignins.microsoft.com/security-info
2. Click "Add sign-in method"
3. Select your preferred method
4. Follow the on-screen instructions
5. Test by signing out and back in

**MFA Troubleshooting**:
- App not showing notifications → Check phone notification settings
- Time-based codes wrong → Sync your phone clock (Settings > Date & Time > Auto)
- Lost phone → Contact IT for temporary access code

### Access Requests

To request access to a system or application:
1. Submit a request via the IT Service Portal: https://serviceportal.company.com
2. Your manager will receive an approval email
3. Upon approval, access is provisioned within 4 business hours
4. You will receive a confirmation email with login instructions

## Software Support

### Microsoft 365 — Common Issues

**Teams Not Starting**:
1. Close Teams completely (check system tray)
2. Clear Teams cache: Delete contents of `%appdata%\Microsoft\Teams\Cache`
3. Also delete: `%appdata%\Microsoft\Teams\blob_storage`
4. Restart Teams
5. If still failing, uninstall and reinstall from https://teams.microsoft.com/downloads

**Outlook Not Syncing**:
1. Check internet connectivity
2. Try Outlook on the web (https://outlook.office365.com)
3. Restart Outlook in Safe Mode: `outlook.exe /safe`
4. Repair Office: Settings > Apps > Microsoft 365 > Modify > Online Repair
5. If profile is corrupted: Control Panel > Mail > Show Profiles > Add new profile

**Excel/Word Crashes**:
1. Open in Safe Mode: Hold Ctrl while launching
2. Disable add-ins: File > Options > Add-ins > Manage COM Add-ins
3. Repair Office installation
4. Check for updates: File > Account > Update Options > Update Now

### VPN Client (GlobalProtect)

**Installation**:
1. Download from https://vpn.company.com
2. Run installer with admin rights
3. Portal address: vpn.company.com
4. Sign in with corporate credentials + MFA

**Cannot Connect**:
1. Check internet connectivity (try browsing a website)
2. Restart the GlobalProtect service
3. Check if another VPN is running (conflicts)
4. Try a different network (coffee shop vs home)
5. Reinstall VPN client if persistent

**Disconnects Frequently**:
1. Check Wi-Fi signal strength
2. Disable Wi-Fi power saving: Network adapter > Properties > Power Management
3. Update network adapter drivers
4. Check with IT if split-tunnel settings need updating

### Software Installation Requests

**Standard Software** (self-install via Company Portal):
- Microsoft 365 suite
- Adobe Acrobat Reader
- Google Chrome / Mozilla Firefox
- Zoom Meetings
- Slack Desktop
- 7-Zip, Notepad++

**Requires Approval**:
- Adobe Creative Cloud → Manager approval + license check
- Visual Studio / JetBrains IDEs → Manager approval
- Specialized / department-specific tools → IT review

**Process**:
1. Open Company Portal app or https://portal.company.com
2. Search for the software
3. Click "Install" (standard) or "Request" (approval needed)
4. Standard installs complete within 15 minutes
5. Approval-based requests take 1-2 business days

## Network & Connectivity

### Wi-Fi Connection

**Corporate Wi-Fi (CorpNet)**:
- SSID: CorpNet
- Authentication: 802.1X with corporate credentials
- Auto-connects when on company devices

**Guest Wi-Fi (GuestNet)**:
- SSID: GuestNet
- Open network with captive portal
- 24-hour access, auto-renews

**Wi-Fi Troubleshooting**:
1. Forget the network and reconnect
2. Run: `netsh wlan show interfaces` to check signal
3. Move closer to an access point
4. Check if the issue is floor-specific (AP problem)
5. Report persistent issues with your location details

### DNS & Proxy Issues

**Cannot Reach Internal Sites**:
1. Run: `nslookup intranet.company.com`
2. If fails, flush DNS: `ipconfig /flushdns`
3. Check DNS settings: should be `10.1.1.10` and `10.1.1.11`
4. Reset TCP/IP: `netsh int ip reset` (requires admin)
5. Restart network adapter

**Proxy Configuration**:
- Auto-detect should be ON
- PAC URL: http://proxy.company.com/proxy.pac
- Manual proxy (if needed): proxy.company.com:8080
- Bypass list: *.company.com; 10.*; 192.168.*; localhost

### Firewall Issues

**Common Blocked Applications**:
- If a business application is blocked, submit a firewall exception request
- Include: application name, port numbers, destination IPs
- Standard SLA: 2 business days for review and implementation

## Hardware Support

### Laptop Issues

**Laptop Won't Turn On**:
1. Disconnect all peripherals
2. Hold power button for 15 seconds (hard reset)
3. Connect charger and wait 5 minutes
4. Try power on again
5. If no response, try removing battery (if removable) and AC reset

**Laptop Running Slow**:
1. Restart (shutdown is not the same as restart on Win 10/11)
2. Check Task Manager (Ctrl+Shift+Esc) for high CPU/memory processes
3. Free up disk space (aim for 20% free)
4. Disable startup programs: Task Manager > Startup tab
5. Run disk cleanup: `cleanmgr`
6. Check for Windows updates

**Blue Screen (BSOD)**:
1. Note the error code (e.g., DRIVER_IRQL_NOT_LESS_OR_EQUAL)
2. Restart the computer
3. If recurring, boot into Safe Mode
4. Check for driver updates
5. Run memory diagnostic: `mdsched.exe`
6. Contact IT with error code for analysis

### Monitor & Display

**External Monitor Not Detected**:
1. Check cable connections (both ends)
2. Try a different cable (HDMI, DisplayPort, USB-C)
3. Press Win+P and select "Extend" or "Duplicate"
4. Update display drivers: Device Manager > Display adapters
5. Try a different port on the docking station

**Monitor Flickering**:
1. Check cable connection
2. Change refresh rate: Settings > Display > Advanced > Refresh rate
3. Update graphics drivers
4. Try with a different cable
5. If on docking station, try direct connection

### Printer Issues

**Cannot Print**:
1. Check printer is online: Settings > Devices > Printers
2. Clear print queue: restart Print Spooler service
3. Remove and re-add the printer
4. Check network connectivity to print server
5. Install latest printer driver from IT portal

**Printer Setup** (Network Printers):
1. Open Settings > Devices > Printers & scanners
2. Click "Add a printer or scanner"
3. If not found, click "The printer I want isn't listed"
4. Enter printer path: `\\printserver\PrinterName`
5. Floor printer list: https://intranet.company.com/printers

### Equipment Requests

**New Equipment**:
- Standard laptop refresh cycle: 4 years
- Request form: https://serviceportal.company.com/hardware
- Manager approval required for all hardware
- Standard SLA: 5-7 business days

**Available Standard Equipment**:
| Type | Model | Specs |
|------|-------|-------|
| Laptop (Standard) | Lenovo ThinkPad T14 | i5, 16GB, 256GB SSD |
| Laptop (Power User) | Lenovo ThinkPad P16 | i7, 32GB, 512GB SSD, dGPU |
| Monitor | Dell U2723QE | 27" 4K USB-C |
| Docking Station | Lenovo USB-C Gen 2 | 3x USB-A, 2x USB-C, HDMI, DP |
| Keyboard | Logitech MK850 | Wireless combo with mouse |
| Headset | Jabra Evolve2 55 | Wireless, noise cancelling |

## Service Desk Information

### Contact & Hours

- **Phone**: Extension 5000 (internal) / +81-3-XXXX-5000 (external)
- **Email**: helpdesk@company.com
- **Portal**: https://serviceportal.company.com
- **Hours**: Monday-Friday 08:00-20:00 JST
- **After-hours**: Critical issues only — call +81-3-XXXX-5001

### Priority Levels

| Priority | Response SLA | Resolution SLA | Examples |
|----------|-------------|----------------|----------|
| Critical | 15 minutes | 2 hours | System-wide outage, security incident |
| High | 1 hour | 4 hours | Account lockout, VPN down for remote worker |
| Medium | 4 hours | 1 business day | Software crash, printer issue |
| Low | 1 business day | 3 business days | New equipment request, access request |
