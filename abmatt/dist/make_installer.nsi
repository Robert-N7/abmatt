!define VERSION "0.7.2"
!define PROGRAM_NAME "ANoob's Brres Material Tool ${VERSION}"
InstallDir "$PROGRAMFILES32\abmatt"
Name "${PROGRAM_NAME}"
OutFile "install.exe"
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
File /a /r "bin\"
# etc
SetOutPath "$INSTDIR\etc\abmatt"
File /a /r "etc\abmatt\"
SectionEnd

# UNINSTALL
Section "Uninstall"
SetOutPath "$INSTDIR\.."
RMDir /r "$INSTDIR\*.*"
EnVar::DeleteValue "PATH" "$INSTDIR\bin\abmatt.exe"
SectionEnd

Function .onInstSuccess
  # MessageBox MB_OK "Success! Start by using 'abmatt' from the command line."
  Quit
FunctionEnd

Function un.onUninstSuccess
  MessageBox MB_OK "Abmatt has been removed."
  Quit
FunctionEnd