$dcmodifyPath="C:\\Apps\\dcmodify.exe"
$storescuPath="C:\\Apps\\storescu.exe"
$movescuPath="C:\\Apps\\movescu.exe"
$orthancPath = "C:\\Program Files\\Orthanc Server\\Orthanc.exe"

Write-Host "Clearing setup"
###########################
Remove-Item -Path .\Storage* -Recurse

Write-Host "Starting setup"
##########################

Start-Process -FilePath $orthancPath -ArgumentList "--verbose .\configPACS.json"
Start-Process -FilePath $orthancPath -ArgumentList "--verbose .\configMiddleman.json"
Start-Process -FilePath $orthancPath -ArgumentList "--verbose .\configWorkstation.json"

do {
  Write-Host "waiting..."
  Start-Sleep 1      
} until(Test-NetConnection 127.0.0.1 -Port 8245 | Where-Object { $_.TcpTestSucceeded } )

Write-Host "Setup started"

Write-Host "Generating test files"
##################################

Copy-Item -Path ..\..\dicomFiles\source.dcm -Destination current.dcm
Copy-Item -Path ..\..\dicomFiles\source.dcm -Destination prior.dcm
$currentDate="20200323"
$priorDate="20190323"

& $dcmodifyPath -i "StudyInstanceUID=1.1" -i "SeriesInstanceUID=1.1.1" -i "SOPInstanceUID=1.1.1.1" -i "StudyDate=$priorDate" -i "SeriesDate=$priorDate"  prior.dcm
& $dcmodifyPath -i "StudyInstanceUID=2.1" -i "SeriesInstanceUID=2.1.1" -i "SOPInstanceUID=2.1.1.1" -i "StudyDate=$currentDate" -i "SeriesDate=$currentDate"  current.dcm

Write-Host "Pushing test files to local PACS"
#############################################

& $storescuPath 127.0.0.1 4245 prior.dcm
& $storescuPath 127.0.0.1 4245 current.dcm

# Write-Host "Sending current study from PACS to Middleman"
& $movescuPath -v 127.0.0.1 4245 --move MIDDLEMAN --aetitle PACS -k StudyInstanceUID=2.1
