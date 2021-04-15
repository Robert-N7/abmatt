!define VERSION "0.9.42"
!define PROGRAM_NAME "ANoob's Brres Material Tool ${VERSION}"
InstallDir "$Documents\abmatt"
Name "${PROGRAM_NAME}"
OutFile "install.exe"
Icon "etc\abmatt\icon.ico"
LicenseData LICENSE
# Request admin rights
RequestExecutionLevel user
!include LogicLib.nsh

page license
page directory
page instfiles

Function .onInit
UserInfo::GetAccountType
pop $0
#${If} $0 != "admin"
 #   MessageBox mb_iconstop "Administrator rights required!"
  #  SetErrorLevel 740   # ERROR_ELEVATION_REQUIRED
   # Quit
# ${EndIf}
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
# Shortcuts
CreateShortCut "$DESKTOP\abmatt.lnk" "$INSTDIR\bin\abmatt-gui.exe"
CreateDirectory "$SMPROGRAMS\abmatt"
CreateShortCut "$SMPROGRAMS\abmatt\abmatt.lnk" "$INSTDIR\bin\abmatt-gui.exe"
CreateShortCut "$SMPROGRAMS\abmatt\uninstall.lnk" "$INSTDIR\uninstall.exe"
# etc
SetOutPath "$INSTDIR\etc\abmatt"
SetOverwrite off    # don't overwrite user files!
File /a /r "etc\abmatt\"
# SetOverwrite on
SectionEnd

# UNINSTALL
Section "Uninstall"
SetOutPath "$INSTDIR\.."
RMDir /r "$INSTDIR\*.*"
EnVar::DeleteValue "PATH" "$INSTDIR\bin\abmatt.exe"
RMDir /r "$SMPROGRAMS\abmatt"
Delete "$DESKTOP\abmatt.lnk"
SectionEnd

Function .onInstSuccess
  MessageBox MB_OK "Success! Use the desktop icon to start the program."
FunctionEnd

Function un.onUninstSuccess
  MessageBox MB_OK "Abmatt has been removed."
FunctionEnd