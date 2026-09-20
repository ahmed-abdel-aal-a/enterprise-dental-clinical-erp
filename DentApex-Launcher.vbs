' ==============================================================================
' DentApex Arabic Edition - Silent Launcher (No Black Windows)
' ==============================================================================
Option Explicit

Dim WshShell, FSO, CurrentDir, BatPath

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' تحديد المسار الفيزيائي لمجلد المشروع ديناميكياً
CurrentDir = FSO.GetParentFolderName(WScript.ScriptFullName)
BatPath = CurrentDir & "\bin\run_services.bat"

If FSO.FileExists(BatPath) Then
    ' تشغيل السكريبت في الخلفية بصمت كامل (WindowStyle = 0, WaitOnReturn = False)
    WshShell.Run Chr(34) & BatPath & Chr(34), 0, False
Else
    MsgBox "تعذر العثور على ملف تشغيل الخدمات:" & vbCrLf & BatPath, vbCritical + vbMsgBoxRight, "خطأ في تشغيل DentApex"
End If

Set WshShell = Nothing
Set FSO = Nothing
