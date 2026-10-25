@echo off
"%PREFIX%\python.exe" -I -X utf8 -m isabelle_patch_control conda-hook pre-unlink <feature>
if not errorlevel 1 if errorlevel 0 goto :end
echo isabelle-patch-control could not run, so <feature> may still be applied to Isabelle (files under "%PREFIX%\isa" may still carry its changes). If you are updating or reinstalling, for example conda update --all: when it finishes, run isabelle-patch-control status. If you are removing <feature>, run these three commands in order: 1. conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control  2. conda install -c https://conda.qiyuan.me -c conda-forge <package>=<version>, adding every other feature package this command removed, at the versions conda listed above  3. conda remove <package> and those same packages>> "%PREFIX%\.messages.txt"
:end
exit /b 0
