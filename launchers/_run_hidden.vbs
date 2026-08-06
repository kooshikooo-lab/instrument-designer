Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
repo = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
scriptName = WScript.Arguments(0)
py = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python312\python.exe"
If Not fso.FileExists(py) Then py = "python"
args = ""
For i = 1 To WScript.Arguments.Count - 1
    args = args & " " & Chr(34) & WScript.Arguments(i) & Chr(34)
Next
cmd = Chr(34) & py & Chr(34) & " " & Chr(34) & repo & "\scripts\" & scriptName & Chr(34) & args
sh.Run cmd, 0, False
