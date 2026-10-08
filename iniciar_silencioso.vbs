Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\mrburger"
WshShell.Run "cmd /c C:\mrburger\iniciar_windows.bat", 0, False
Set WshShell = Nothing
