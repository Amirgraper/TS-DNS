# Set the execution policy to Bypass for the process
Set-ExecutionPolicy Bypass -Scope Process -Force

# Add the necessary assembly for Windows Forms
Add-Type -AssemblyName System.Windows.Forms

$dns1 = "1.1.1.1"
$dns2 = "1.0.0.1"

$adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }
foreach ($adapter in $adapters) {
    $connection_name = $adapter.Name
    $current_dns = (Get-DnsClientServerAddress -InterfaceAlias $connection_name).ServerAddresses

    if ($current_dns -notcontains $dns1 -or $current_dns -notcontains $dns2) {
        Set-DnsClientServerAddress -InterfaceAlias $connection_name -ServerAddresses $dns1,$dns2
    } else {
        Set-DnsClientServerAddress -InterfaceAlias $connection_name -ResetServerAddresses
    }
}