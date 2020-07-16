!define VERSION "0.6.0"
Name "ANoob's Brres Material Tool ${VERSION}"
OutFile "install.exe"
InstallDir "$PROGRAMFILES64\abmatt"
ShowInstDetails "nevershow"
ShowUninstDetails "nevershow"
# Request admin rights
RequestExecutionLevel admin
!include LogicLib.nsh
Function .onInit
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    MessageBox mb_iconstop "Administrator rights required!"
    SetErrorLevel 740   # ERROR_ELEVATION_REQUIRED
    Quit
${EndIf}
FunctionEnd


# INSTALL
Section "install"
SetOutPath "$INSTDIR"
WriteUninstaller "$INSTDIR\uninstall.exe"
File README.md
File LICENSE
# bin
SetOutPath "$INSTDIR\bin"
EnVar::AddValue "PATH" "$INSTDIR\bin"
File "bin\abmatt.exe"
# etc
SetOutPath "$INSTDIR\etc\abmatt"
File "etc\abmatt\presets.txt"
File "etc\abmatt\config.conf"
SectionEnd

# UNINSTALL
Section "Uninstall"
RMDir /r "$INSTDIR\*.*"
EnVar::DeleteValue "PATH" "$INSTDIR\bin"
SectionEnd