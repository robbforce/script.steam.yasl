# (Y)et (A)nother (S)team (L)auncher, Kodi addon script modified by Nathaniel Roark, 2020-11-11.
#
# Based on the Steam Launcher by teeedubb. http://forum.xbmc.org/showthread.php?tid=157499
# and Kodi Launches Playnite by hoksilato2. https://github.com/hoksilato2/Kodi-Launches-Playnite-Addon
# Steam Launcher was based on Rom Collection Browser as a guide, plus borrowed ideas and code from it.
#
# Only supporting Windows for now, so all other OS support has been commented out.
import os
import sys
import subprocess
import time
from pathlib import Path, PurePath
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

addon = xbmcaddon.Addon(id='script.steam.yasl')
addonPath = addon.getAddonInfo('path')
addonIcon = addon.getAddonInfo('icon')
addonVersion = addon.getAddonInfo('version')
dialog = xbmcgui.Dialog()
language = addon.getLocalizedString
scriptid = 'script.steam.yasl'

# This is a pointer to the module object instance itself.
this = sys.modules[__name__]

# Assign other module scope variables.
this.steam_win = addon.getSettingString("SteamWin")
this.kodi_win = addon.getSettingString("KodiWin")
#this.steam_linux = addon.getSettingString("steamLinux")
#this.kodi_linux = addon.getSettingString("KodiLinux")
#this.steam_osx = addon.getSettingString("steamOsx")
#this.kodi_osx = addon.getSettingString("KodiOsx")
this.delete_user_script = addon.getSettingBool("DelUserScript")
this.quit_kodi = addon.getSettingInt("QuitKodi")
this.busy_dialog_time = addon.getSettingInt("BusyDialogTime")
this.script_update_check = addon.getSettingBool("ScriptUpdateCheck")
this.file_path_check = addon.getSettingBool("FilePathCheck")
this.kodi_portable = addon.getSettingBool("KodiPortable")
this.pre_script_enabled = addon.getSettingBool("PreScriptEnabled")
this.pre_script = addon.getSettingString("PreScript")
this.post_script_enabled = addon.getSettingBool("PostScriptEnabled")
this.post_script = addon.getSettingString("PostScript")
this.os_win = xbmc.getCondVisibility('system.platform.windows')
#this.os_osx = xbmc.getCondVisibility('system.platform.osx')
#this.os_linux = xbmc.getCondVisibility('system.platform.linux')
#this.os_android = xbmc.getCondVisibility('system.platform.android')
#this.wmctrl_check = addon.getSettingBool("WmctrlCheck")
this.suspend_audio = addon.getSettingBool("SuspendAudio")
this.custom_script_folder_enabled = addon.getSettingBool("CustomScript")
this.custom_script_folder = addon.getSettingString("CustomScriptFolder")
this.minimize_kodi = addon.getSettingBool("MinimizeKodi")
this.steam_parameters = addon.getSettingString("SteamParameters")
this.force_kill_kodi = addon.getSettingInt("ForceKillKodi")
this.big_picture = addon.getSettingBool("BigPicture")

def log(msg):
  msg = msg.encode(txt_encode)
  xbmc.log(f'{scriptid}: {msg}')

def get_addon_install_path():
  path = xbmcvfs.translatePath(addon.getAddonInfo('path'))
  return path

def get_addon_data_path():
  path = xbmcvfs.translatePath('special://profile/addon_data/%s/' % scriptid)
  if not xbmcvfs.exists(path):
    log(f'addon userdata folder does not exist, creating: {path}')
    try:
      xbmcvfs.mkdirs(path)
      log(f'created directory: {path}')
    except:
      log(f'ERROR: failed to create directory: {path}')
      dialog.notification(language(50212), language(50215), addonIcon, 5000)
  return path

def copy_launcher_scripts_to_userdata():
  oldBasePath = PurePath(get_addon_install_path()).joinpath('resources', 'scripts')
  if this.os_win:
    oldPath = PurePath.joinpath(oldBasePath, 'steam-yasl.ahk')
    newPath = PurePath(ScriptsPath).joinpath('steam-yasl.ahk')
    copy_file(oldPath, newPath)
    oldPath = PurePath.joinpath(oldBasePath, 'steam-yasl.exe')
    newPath = PurePath(ScriptsPath).joinpath('steam-yasl.exe')
    copy_file(oldPath, newPath)
  # elif this.os_linux + this.os_osx:
  #   oldPath = os.path.join(oldBasePath, 'steam-yasl.sh')
  #   newPath = os.path.join(ScriptsPath, 'steam-yasl.sh')
  #   copy_file(oldPath, newPath)

def copy_file(oldPath, newPath):
  # xbmcvfs only works with strings and it wants directories to end with a slash, so convert these.
  oldPath = str(oldPath)
  newDir = str(newPath.parents[0]) + '\\'
  newPath = str(newPath)
  if not xbmcvfs.exists(newDir):
    log(f'userdata scripts folder does not exist, creating: {newDir}')
    if not xbmcvfs.mkdirs(newDir):
      log(f'ERROR: failed to create userdata scripts folder: {newDir}')
      dialog.notification(language(50212), language(50215), addonIcon, 5000)
      sys.exit()
  if not xbmcvfs.exists(newPath):
    log(f'script file does not exist, copying to userdata: {newPath}')
    if not xbmcvfs.copy(oldPath, newPath):
      log(f'ERROR: failed to copy script file to userdata: {oldPath}')
      dialog.notification(language(50212), language(50215), addonIcon, 5000)
      sys.exit()
  else:
    log(f'script file already exists, skipping copy to userdata: {newPath}')

# def make_script_executable():
#   scriptPath = os.path.join(ScriptsPath, 'steam-yasl.sh')
#   if os.path.isfile(scriptPath):
#     if '\r\n' in open(scriptPath,'rb').read():
#       log('Windows line endings found in %s, converting to unix line endings.' % scriptPath)
#       with open(scriptPath, 'rb') as f:
#         content = f.read()
#         content = content.replace('\r\n', '\n')
#       with open(scriptPath, 'wb') as f:
#         f.write(content)
#     if not stat.S_IXUSR & os.stat(scriptPath)[stat.ST_MODE]:
#       log('steam-yasl.sh not executable: %s' % scriptPath)
#       try:
#         os.chmod(scriptPath, stat.S_IRWXU)
#         log('steam-yasl.sh now executable: %s' % scriptPath)
#       except:
#         log('ERROR: unable to make steam-yasl.sh executable, exiting: %s' % scriptPath)
#         dialog.notification(language(50212), language(50215), addonIcon, 5000)
#         sys.exit()
#       log('steam-yasl.sh executable: %s' % scriptPath)

def delete_userdata_scripts():
  if this.delete_user_script == True:
    log(f'deleting userdata scripts, option enabled: delete_user_script = {str(this.delete_user_script)}')
    scriptFile = str(PurePath(ScriptsPath).joinpath('steam-yasl.ahk'))
    delete_file(scriptFile)
    scriptFile = str(PurePath(ScriptsPath).joinpath('steam-yasl.exe'))
    delete_file(scriptFile)
    scriptFile = str(PurePath(ScriptsPath).joinpath('steam-yasl.sh'))
    delete_file(scriptFile)
  elif this.delete_user_script == False:
    log(f'skipping deleting userdata scripts, option disabled: delete_user_script = {str(this.delete_user_script)}')

def delete_file(scriptFile):
  if xbmcvfs.exists(scriptFile):
    log(f'found and deleting: {scriptFile}')
    if not xbmcvfs.delete(scriptFile):
      log(f'ERROR: deleting failed: {scriptFile}')
      dialog.notification(language(50212), language(50215), addonIcon, 5000)
    addon.setSettingBool(id="DelUserScript", value=False)

def file_check():
  # if this.os_linux:
  #   if wmctrlCheck == 'true':
  #     if subprocess.call(["which", "wmctrl"]) != 0:
  #       log('ERROR: System program "wmctrl" not present, install it via you system package manager or if you are running the SteamOS compositor disable the addon option "Check for program wmctrl" (ONLY FOR CERTAIN USE CASES!!)')
  #       dialog.notification(language(50212), language(50215), addonIcon, 5000)
  #       sys.exit()
  #     else:
  #       log('wmctrl present, checking if a window manager is running...')
  #                               display = None
  #                               if 'DISPLAY' in os.environ: display = os.environ['DISPLAY'] # We inherited DISPLAY from Kodi, pass it down
  #                               else:
  #                                   for var in open('/proc/%d/environ' % os.getppid()).read().split('\x00'):
  #                                       if var.startswith('DISPLAY='): display = var[8:] # Read DISPLAY from parent process if present
  #       if display is None or subprocess.call('DISPLAY=%s wmctrl -l' % display, shell=True) != 0:
  #         log('ERROR: A window manager is NOT running - unless you are using the SteamOS compositor Steam BPM needs a windows manager. If you are using the SteamOS compositor disable the addon option "Check for program wmctrl"')
  #         dialog.notification(language(50212), language(50215), addonIcon, 5000)
  #         sys.exit()
  #       else:
  #         log('A window manager is running...')
  #   if minimiseKodi == True:
  #     if subprocess.call(["which", "xdotool"]) != 0:
  #       log('ERROR: Minimised Kodi enabled and system program "xdotool" not present, install it via you system package manager. Xdotool is required to minimise Kodi.')
  #       dialog.notification(language(50212), language(50215), addonIcon, 5000)
  #       sys.exit()
  #     else:
  #       log('xdotool present...')
  if this.file_path_check == True:
    log(f'running program file check, option is enabled: filePathCheck = {str(this.file_path_check)}')
    if this.os_win:
      this.steam_win = addon.getSettingString("SteamWin")
      this.kodi_win = addon.getSettingString("KodiWin")
      SteamExe = xbmcvfs.validatePath(this.steam_win)
      KodiExe = xbmcvfs.validatePath(this.kodi_win)
      executable_check(SteamExe, KodiExe)
    # elif this.os_osx:
    #   this.steam_osx = addon.getSetting("steamOsx")
    #   kodiOsx = addon.getSetting("KodiOsx")
    #   steamExe = os.path.join(this.steam_osx)
    #   kodiExe = os.path.join(kodiOsx)
    #   executable_check(steamExe, kodiExe)
    # elif this.os_linux:
    #   this.steam_linux = addon.getSetting("steamLinux")
    #   this.kodi_linux = addon.getSetting("KodiLinux")
    #   steamExe = os.path.join(this.steam_linux)
    #   kodiExe = os.path.join(this.kodi_linux)
    #   executable_check(steamExe, kodiExe)
  else:
    log(f'skipping program file check, option disabled: filePathCheck = {this.file_path_check}')

def executable_check(SteamExe, KodiExe):
  if xbmcvfs.exists(SteamExe):
    log(f'Steam executable exists: {SteamExe}')
  else:
    file_check_dialog(SteamExe)
  if xbmcvfs.exists(KodiExe):
    log(f'Kodi executable exists: {KodiExe}')
  else:
    file_check_dialog(KodiExe)

def file_check_dialog(programExe):
  log(f'ERROR: dialog to go to addon settings because executable does not exist: {programExe}')
  if dialog.yesno(language(50212), programExe, language(50210), language(50211)):
    log('yes selected, opening addon settings')
    addon.openSettings()
    file_check()
    sys.exit()
  else:
    log(f'ERROR: no selected with invalid executable, exiting: {programExe}')
    sys.exit()

def script_version_check():
  if this.script_update_check == True:
    log('usr scripts are set to be checked for updates...')
    if this.delete_user_script == False:
      log('usr scripts are not set to be deleted, running version check...')
      sysScriptDir = PurePath(get_addon_install_path()).joinpath('resources', 'scripts')
      if this.os_win:
        sysScriptPath = PurePath.joinpath(sysScriptDir, 'steam-yasl.ahk')
        usrScriptPath = PurePath(ScriptsPath).joinpath('steam-yasl.ahk')
        if Path(usrScriptPath).is_file():
          compare_file(sysScriptPath, usrScriptPath)
        else:
          log('usr script does not exist, skipping version check')
      # elif this.os_linux + this.os_osx:
      #   sysScriptPath = os.path.join(sysScriptDir, 'steam-yasl.sh')
      #   usrScriptPath = os.path.join(ScriptsPath, 'steam-yasl.sh')
      #   if os.path.isfile(os.path.join(usrScriptPath)):
      #     compare_file(sysScriptPath, usrScriptPath)
      #   else:
      #     log('usr script does not exist, skipping version check')
    else:
      log('usr scripts are set to be deleted, no version check needed')
  else:
    log('usr scripts are set to not be checked for updates, skipping version check')

def compare_file(sysScriptPath, usrScriptPath):
  scriptSysVer = '000'
  scriptUsrVer = '000'
  if Path(sysScriptPath).is_file():
    with xbmcvfs.File(str(sysScriptPath)) as f:
      for line in f.read().split('\n'):
        if "steam.launcher.script.revision=" in line:
          scriptSysVer = line[37:39]
          break
    log(f'sys "steam.launcher.script.revision=": {scriptSysVer}')
  if Path(usrScriptPath).is_file():
    with xbmcvfs.File(str(usrScriptPath)) as f:
      for line in f.read().split('\n'):
        if "steam.launcher.script.revision=" in line:
          scriptUsrVer = line[37:39]
          break
    log(f'usr "steam.launcher.script.revision=": {scriptUsrVer}')
  if int(scriptSysVer) > int(scriptUsrVer):
    log(f'system scripts have been updated: sys:{scriptSysVer} > usr:{scriptUsrVer}')
    if dialog.yesno(language(50113), language(50213), language(50214)):
      this.delete_user_script = True
      log(f'yes selected, option delete_user_script enabled: {str(this.delete_user_script)}')
    else:
      this.delete_user_script = False
      this.script_update_check = False
      addon.setSettingBool(id="ScriptUpdateCheck", value=False)
      log(f'no selected, script update check disabled: ScriptUpdateCheck = {str(this.script_update_check)}')
  else:
    log('userdata scripts are up to date')

def quit_kodi_dialog():
  if this.quit_kodi == 2:
    log(f'quit setting: {str(this.quit_kodi)} selected, asking user to pick')
    if dialog.yesno('YA Steam Launcher', language(50053)):
      this.quit_kodi = 0
    else:
      this.quit_kodi = 1
  if this.quit_kodi == 1 and this.minimize_kodi == False:
    this.quit_kodi = 3
  log(f'quit setting selected: {str(this.quit_kodi)}')

def kodi_busy_dialog():
  if this.busy_dialog_time != 0:
    xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
    log('busy dialog started')
    time.sleep(this.busy_dialog_time)
    xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
    log(f'busy dialog stopped after: {str(this.busy_dialog_time)} seconds')

def set_pre_post_script_parameters():
  if this.pre_script_enabled == False or this.pre_script == '':
    this.pre_script = 'false'
  elif this.pre_script_enabled == True:
    if not os.path.isfile(os.path.join(this.pre_script)):
      log(f'pre-steam script does not exist, disabling!: "{this.pre_script}"')
      this.pre_script = 'false'
      dialog.notification(language(50212), language(50215), addonIcon, 5000)
  log(f'pre steam script: {this.pre_script}')
  if this.post_script_enabled == False or this.post_script == '':
    this.post_script = 'false'
  elif this.post_script_enabled == True:
    if not os.path.isfile(os.path.join(this.post_script)):
      log(f'post-steam script does not exist, disabling!: "{this.post_script}"')
      this.post_script = 'false'
      dialog.notification(language(50212), language(50215), addonIcon, 5000)
  log(f'post steam script: {this.post_script}')

def launch_steam():
  # if this.os_android:
  #   cmd = "com.valvesoftware.android.steam.community"
  #   log('attempting to launch: "%s"' % cmd)
  #   xbmc.executebuiltin('XBMC.StartAndroidActivity("%s")' % cmd)
  #   kodi_busy_dialog()
  #   sys.exit()
  # elif this.os_win:
  if this.os_win:
    SteamLauncher = str(PurePath(ScriptsPath).joinpath('steam-yasl.exe'))
    SteamWin = this.steam_win
    log(f'steam launcher exe: {SteamLauncher}')
    cmd = f'"{SteamLauncher}" "{SteamWin}" "{this.kodi_win}" "{str(this.quit_kodi)}" "{str(this.kodi_portable).lower()}" "{this.pre_script}" "{this.post_script}" "{this.steam_parameters}" "{str(this.force_kill_kodi)}" "{this.big_picture}"'
  # elif this.os_osx:
  #   SteamLauncher = os.path.join(ScriptsPath, 'steam-yasl.sh')
  #   cmd = '"%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s"' % (SteamLauncher, this.steam_osx, this.kodi_osx, str(this.quit_kodi), str(this.kodi_portable).lower(), this.pre_script, this.post_script, this.steam_parameters, str(this.force_kill_kodi), this.big_picture)
  # elif this.os_linux:
  #   SteamLauncher = os.path.join(ScriptsPath, 'steam-yasl.sh')
  #   cmd = '"%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s" "%s"' % (SteamLauncher, this.steam_linux, this.kodi_linux, str(this.quit_kodi), str(this.kodi_portable).lower(), this.pre_script, this.post_script, this.steam_parameters, str(this.force_kill_kodi), this.big_picture)
  try:
    log(f'attempting to launch: {cmd}')
    if this.suspend_audio == True:
      xbmc.audioSuspend()
      log('audio suspended')
    if this.quit_kodi != 0 and this.suspend_audio == True:
      proc_h = subprocess.Popen(cmd, shell=True, close_fds=False)
      kodi_busy_dialog()
      log('waiting for Steam to exit')
      while proc_h.returncode is None:
        xbmc.sleep(1000)
        proc_h.poll()
      log('start resuming audio....')
      xbmc.audioResume()
      log('audio resumed')
      del proc_h
    else:
      subprocess.Popen(cmd, shell=True, close_fds=True)
      kodi_busy_dialog()
  except:
    log(f'ERROR: failed to launch: {cmd}')
    dialog.notification(language(50212), language(50215), addonIcon, 5000)

#HACK: sys.getfilesystemencoding() is not supported on all systems (e.g. Android)
txt_encode = 'utf-8'
try:
  txt_encode = sys.getfilesystemencoding()
except:
  pass
#osAndroid returns linux + android
# if this.os_android:
#   this.os_linux = 0
#   txt_encode = 'utf-8'
log(f'*running YASL v{addonVersion}')
#log('running on os_android, os_osx, os_linux, os_win: %s %s %s %s ' % (this.os_android, this.os_osx, this.os_linux, this.os_win))
log(f'running on os_win: {this.os_win}')
log(f'system text encoding in use: {txt_encode}')
if this.custom_script_folder_enabled == True:
  ScriptsPath = this.custom_script_folder
else:
  ScriptsPath = PurePath(get_addon_data_path()).joinpath('scripts')
script_version_check()
delete_userdata_scripts()
copy_launcher_scripts_to_userdata()
file_check()
#make_script_executable()
set_pre_post_script_parameters()
quit_kodi_dialog()
launch_steam()
