; Script generated by the HM NIS Edit Script Wizard.

; HM NIS Edit Wizard helper defines
!define PRODUCT_NAME "Album Cover Art Downloader"
!define PRODUCT_VERSION "1.6.5"
!define PRODUCT_PUBLISHER "Sami Ky�stil�"
!define PRODUCT_WEB_SITE "http://unrealvoodoo.org/hiteck/projects/albumart"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\albumart-qt.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; MUI 1.67 compatible ------
!include "MUI.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; License page
;!insertmacro MUI_PAGE_LICENSE "Copying.txt"
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\albumart-qt.exe"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\Readme.txt"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "AlbumArtSetup.exe"
InstallDir "$PROGRAMFILES\Album Cover Art Downloader"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File "..\win32\_imaging.pyd"
  File "..\win32\_socket.pyd"
  File "..\win32\_ssl.pyd"
  File "..\win32\albumart-qt.exe"
  File "..\win32\copying.txt"
  File "..\win32\mingwm10.dll"
  File "..\win32\pyexpat.pyd"
  File "..\win32\python24.dll"
  File "..\win32\qt-mt3.dll"
  File "..\win32\qt.pyd"
  File "..\win32\readme.txt"
  File "..\win32\sip.pyd"
  File "..\win32\zlib.pyd"

  CreateDirectory "$SMPROGRAMS\Album Cover Art Downloader"
  CreateShortCut "$SMPROGRAMS\Album Cover Art Downloader\Album Cover Art Downloader.lnk" "$INSTDIR\albumart-qt.exe"
  CreateShortCut "$DESKTOP\Album Cover Art Downloader.lnk" "$INSTDIR\albumart-qt.exe"
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\Album Cover Art Downloader\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\Album Cover Art Downloader\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\albumart-qt.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\albumart-qt.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd


Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\_imaging.pyd"
  Delete "$INSTDIR\_socket.pyd"
  Delete "$INSTDIR\_ssl.pyd"
  Delete "$INSTDIR\albumart-qt.exe"
  Delete "$INSTDIR\copying.txt"
  Delete "$INSTDIR\mingwm10.dll"
  Delete "$INSTDIR\pyexpat.pyd"
  Delete "$INSTDIR\python24.dll"
  Delete "$INSTDIR\qt-mt3.dll"
  Delete "$INSTDIR\qt.pyd"
  Delete "$INSTDIR\readme.txt"
  Delete "$INSTDIR\sip.pyd"
  Delete "$INSTDIR\zlib.pyd"

  Delete "$SMPROGRAMS\Album Cover Art Downloader\Uninstall.lnk"
  Delete "$SMPROGRAMS\Album Cover Art Downloader\Website.lnk"
  Delete "$DESKTOP\Album Cover Art Downloader.lnk"
  Delete "$SMPROGRAMS\Album Cover Art Downloader\Album Cover Art Downloader.lnk"

  RMDir "$SMPROGRAMS\Album Cover Art Downloader"
  RMDir "$INSTDIR\share\albumart"
  RMDir "$INSTDIR\share"
  RMDir "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd
