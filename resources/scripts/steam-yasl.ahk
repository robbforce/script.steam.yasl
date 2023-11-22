; (Y)et (A)nother (S)team (L)auncher autohotkey script by Nathaniel Roark, 2023-11-17.
;
; Inspired by Steam Launcher by teeedub: https://github.com/teeedubb/teeedubb-xbmc-repo & http://forum.xbmc.org/showthread.php?tid=157499
; Also inspired by Kodi-Launches-Playnite-Addon by hoksilato2: https://github.com/hoksilato2/Kodi-Launches-Playnite-Addon
; which was forked from Kodi-Launches-Steam-Addon by BrosMakingSoftware. :)
;
; The original Steam Launcher ahk script has been so heavily re-factored that only the logic flow is intact. Instead of
; polling for the Steam window, this uses window messages to watch for destroyed or minimized events. Other notable
; changes include parsing the command-line paramters into an array, using the PID of the executed process for the win
; commands, and the ability to restore Steam from the system tray.
;
; Thanks go out to Fanatic Guru for the TrayIcon and WinHook libraries:
; https://gist.github.com/tmplinshi/83c52a9dffe65c105803d026ca1a07da
; https://www.autohotkey.com/boards/viewtopic.php?t=59149
;
; Manual script usage: steam-yasl.exe "e:\path\to\steam.exe" "d:\path\to\kodi.exe" "0/1" "true/false" "scriptpath/false" "scriptpath/false" "Steam parameters" "0" "true/false"
; Example: steam-yasl.exe "C:\Program Files\Steam\steam.exe" "C:\Program Files\Kodi\kodi.exe" "0" "false" "false" "false" "" "0" "true"
; Command-line parameters:
;   $1 = Steam executable
;   $2 = Kodi executable
;   $3 = 0 - Quit Kodi, 1 - Minimize Kodi, 3 - Do nothing
;   $4 = Kodi portable mode
;   $5 = pre script
;   $6 = post script
;   $7 = additional command-line parameters to pass to Steam (see https://developer.valvesoftware.com/wiki/Command_Line_Options)
;   $8 = force kill kodi and how long to wait for, greater than 0 = true
;   %9 = run Steam in Big Picture mode, true or false
;
; Change the 'steam.launcher.script.revision' number below to 999 to preserve changes through addon updates, otherwise
; it'll be overwritten. You'll need to install AutoHotKey to compile this .ahk file into an .exe, to work with the addon.
;
; steam.launcher.script.revision=001

#Requires AutoHotkey v2.0
#SingleInstance force
#include WinHook.ahk
#include TrayIcon.ahk
DetectHiddenWindows(0)

OnExit(ObjBindMethod(WinHook.Event, "UnHookAll"))

If (A_Args.Length < 9) {
  MsgBox "This script requires 9 arguments, but it only received " . A_Args.Length . ". See script file for details."
  ExitApp
}

; Set some variables. Trying to use A_Args directly results in a compilation error in autohotkey, especially when running
; without all parameters. This loop and referencing this array gets around that. It also allows us to replace the legacy
; parameter variables with something more readable.
Global Parameters := {}
For Index, Value in A_Args
  Parameters[Index] := Value
SplitPath Parameters.1, &SteamExe, &SteamDir
SplitPath Parameters.2, &KodiExe, &KodiDir
QuitOrMinKodi := Parameters.3
PortableKodi := Parameters.4
PreScript := Parameters.5
PostScript := Parameters.6
SteamCommands := Parameters.7
ForceKillTime := Parameters.8
BigPicture := Parameters.9

KodiClass := "Kodi"
SteamWindowExe := "steamwebhelper.exe"

; Uncomment the following line and add the PID of a running app to see the title and class in a msgbox.
;GetProcessInfo(20400)

; ----------------------------------------------------------------------------------------------------------------------
; Execute pre-Steam script.
If (PreScript != "false") {
  RunWait '"' . PreScript . '"',, "Hide"
}

; ----------------------------------------------------------------------------------------------------------------------
; Check first if Steam is in the system tray, use another approach and commands to activate the window.
oIcons := {}
oIcons := TrayIcon_GetInfo(SteamExe)

; Use the process name to make sure the system icon was found and send a double left-click to retore the window.
If (oIcons[1].process = SteamExe) {
  TrayIcon_Button(SteamExe, "L", True)
  WinWaitActive "ahk_exe " . SteamWindowExe,, 5
}

; Check if Steam is running for the current user and launch or focus it.
varPID := ProcessExist(SteamExe, A_UserName)
If (varPID > 0) {
  If (WinExist("ahk_pid " . varPID)) {
    WinRestore "ahk_pid " . varPID
    WinActivate "ahk_pid " . varPID
  }
}
Else {
  Try {
    If (BigPicture = "true") {
      ; Launch Steam and store the PID in a local variable.
      Run '"' . SteamDir . '\' . SteamExe . '" ' . SteamCommands . ' steam://open/bigpicture',, &varPID
    }
    Else {
      ; Launch Steam and store the PID in a local variable.
      Run '"' . SteamDir . '\' . SteamExe . '" ' . SteamCommands,, &varPID
    }
  }
  Catch
    Msgbox "There was an error trying to run the Steam exe."
}
SteamLoop()

; ----------------------------------------------------------------------------------------------------------------------
SteamLoop() {
  ; Wait for Steam to load. Set timeout to 5, so this script doesn't hang.
  WinWaitActive "ahk_pid " . varPID,, 5

  ; Register win hooks to detect when Steam is closed or minimized.
  WinHook.Event.Add(0x8001, 0x8001, "SteamClosedEvent", varPID, "Steam")
  ;WinHook.Event.Add(0x0016, 0x0016, "SteamMinimizedEvent", varPID, "Steam")

  ; If requested, close / kill Kodi for the current user.
  If (QuitOrMinKodi = "0") {
    varPID := ProcessExist(KodiExe, A_UserName)
    If (varPID > 0) {
      varError := ProcessClose(varPID)

      ; If the process failed to close (ProcessClose will return 0 on failure) and a timeout parameter
      ; was supplied, then try again with the tskill command.
      If (varError = 0 And ForceKillTime > 0) {
        Run A_ComSpec . " /c timeout /t " . ForceKillTime . " && tskill " . varPID,, "Hide"
      }
    }
  }

  ; Or minimize Kodi instead.
  If (QuitOrMinKodi = "1") And (WinExist("ahk_class " . KodiClass)) {
    WinMinimize
  }

  Return
}

; ----------------------------------------------------------------------------------------------------------------------
OpenKodi() {
  ; Execute post Steam script.
  If (PostScript != "false") {
    RunWait '"' . PostScript . '"',, "Hide"
  }

  ; If Kodi is running for the current user, but minimized, store the PID in a local variable and restore the window.
  varPID := ProcessExist(KodiExe, A_UserName)
  If (varPID > 0) {
    If (QuitOrMinKodi = "1") And (WinExist("ahk_pid " . varPID)) {
      WinRestore "ahk_pid " . varPID
      WinActivate "ahk_pid " . varPID
    }
  }

  ; Run the Kodi executable if the script closed it earlier.
  If (QuitOrMinKodi = "0") {
    varRunCmd := KodiDir . "\" . KodiExe

    ; Check if it should run in portable mode or not.
    If (PortableKodi = "true") {
      varRunCmd := varRunCmd . " -p"
    }

    Try {
      ; Launch Kodi and store the PID in a local variable.
      Run varRunCmd,, &varPID
    }
    Catch
      Msgbox "There was an error trying to run the Kodi exe."
  }

  ; Wait for Kodi to load. Set timeout, so this script doesn't hang.
  WinWaitActive "ahk_pid " . varPID,, 10

  ; ----------------------------------------------------------------------------------------------------------------------
  ; Check if Steam re-opened after an update or the user switched to the dekstop / fullscreen exe.
  varHWND := WinWaitActive("ahk_exe " . SteamWindowExe,, 30)
  If (varHWND > 0) {
    ; Set the PID variable again.
    varPID := ProcessExist(SteamExe, A_UserName)
    If (varPID > 0) {
      ; Unhook events just in case, since we'll be adding new event hooks.
      WinHook.Event.UnHookAll()

      ; Run the pre-Steam script again if needed.
 ;     If (PreScript != "false") {
 ;       RunWait '"' . PreScript . '"',, "Hide"
 ;     }

      ; Go back to listening for the close event.
      SteamLoop()
    }
  }
}

; ----------------------------------------------------------------------------------------------------------------------
; Call this function with the PID you need info from. Ex: GetProcessInfo(21964)
GetProcessInfo(p_pid) {
  If (WinExist("ahk_pid " . p_pid)) {
    varHwnd := WinGetID("ahk_pid " . p_pid)
    varProcessName := WinGetProcessName("ahk_pid " . p_pid)
    varWindowTitle := WinGetTitle("ahk_exe " . varProcessName)
    varWindowClass := WinGetClass("ahk_exe " . varProcessName)
  }
  MsgBox "PID: " . p_pid . "`n" . "hWnd: " . varHwnd . "`n" . "Process name: " . varProcessName . "`n" . "Window title: " . varWindowTitle . "`n" . "Window class: " . varWindowClass
}

; ----------------------------------------------------------------------------------------------------------------------
; Simulate the Process, Exist command, but apply a filter for the current user.
ProcessExist(varProcessName, processOwnerUserName := "") {
  varQuery := "Select ProcessId from Win32_Process WHERE Name LIKE '%" . varProcessName . "%'"

  For varProcess in ComObjGet("winmgmts:").ExecQuery(varQuery, "WQL", 48) {
    If (processOwnerUserName != "") {
      currentProcessOwnerUserName := ComVar()
      varProcess.GetOwner(currentProcessOwnerUserName.ref)
      If (currentProcessOwnerUserName[] != processOwnerUserName)
        Continue
    }
    ; This will exit the loop early with the PID.
    Return varProcess.processID
  }
  ; If we've landed outside the loop, then the process wasn't found. Simulate the Process, Exist command by returning 0.
  Return 0
}

; ----------------------------------------------------------------------------------------------------------------------
; These com functions are required by the ProcessExist function, to query Win32_Process.
ComVar(Type := 0xC) {
  static base := { __Get: "ComVarGet", __Set: "ComVarSet", __Delete: "ComVarDel" }
  ; Create an array of 1 VARIANT.  This method allows built-in code to take
  ; care of all conversions between VARIANT and AutoHotkey internal types.
  arr := ComObjArray(Type, 1)
  ; Lock the array and retrieve a pointer to the VARIANT.
  DllCall("oleaut32\SafeArrayAccessData", "ptr", ComObjValue(arr), "ptr*", &arr_data)
  ; Store the array and an object which can be used to pass the VARIANT ByRef.
  ;Return { ref: ComObjParameter(0x4000|Type, arr_data), _: arr, base: base }
  Return { ref: ComValue(0x4000|Type, arr_data), _: arr, base: base }
}

; Called when script accesses an unknown field.
ComVarGet(cv, p*) {
  If p.MaxIndex() = "" ; No name/parameters, i.e. cv[]
    Return cv._[0]
}

; Called when script sets an unknown field.
ComVarSet(cv, v, p*) {
  If p.MaxIndex() = "" ; No name/parameters, i.e. cv[]:=v
    Return cv._[0] := v
}

; Called when the object is being freed.
ComVarDel(cv) {
  ; This must be done to allow the internal array to be freed.
  DllCall("oleaut32\SafeArrayUnaccessData", "ptr", ComObjValue(cv._))
}

; ----------------------------------------------------------------------------------------------------------------------
; This event is only fired when Steam is closed, re-open Kodi.
SteamClosedEvent(hWinEventHook, Win_Event, Win_Hwnd, idObject, idChild, dwEventThread, dwmsEventTime) {
  OpenKodi()
}

; This event is only fired when Steam is minimized, re-open Kodi.
; SteamMinimizedEvent(hWinEventHook, Win_Event, Win_Hwnd, idObject, idChild, dwEventThread, dwmsEventTime)
; {
;   GoSub, OpenKodi
; }
