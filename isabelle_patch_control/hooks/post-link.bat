@echo off
if not exist "%PREFIX%\Scripts\isabelle-patch-control.exe" goto :notool
"%PREFIX%\python.exe" -I -X utf8 -m isabelle_patch_control conda-hook post-link
if not errorlevel 1 if errorlevel 0 goto :end
echo isabelle-patch-control: the hook could not run. Run: conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control; then: isabelle-patch-control apply>> "%PREFIX%\.messages.txt"
goto :end
:notool
if not exist "%PREFIX%\share\isabelle_patch_control\features.d\" goto :end
echo isabelle-patch-control is not installed, so the installed Isabelle feature packages are not applied. Run: conda install -c https://conda.qiyuan.me -c conda-forge isabelle-patch-control; then: isabelle-patch-control apply>> "%PREFIX%\.messages.txt"
:end
