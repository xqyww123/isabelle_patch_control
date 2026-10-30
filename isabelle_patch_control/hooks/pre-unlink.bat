@echo off
"%PREFIX%\python.exe" -I -X utf8 -m isabelle_patch_control conda-hook pre-unlink <feature>
if not errorlevel 1 if errorlevel 0 goto :end
echo isabelle-patch-control could not run, so <feature> may still be applied to Isabelle (files under "%PREFIX%\isa" may still carry its changes).>> "%PREFIX%\.messages.txt"
echo If you are updating or reinstalling, for example conda update --all: when it finishes, run isabelle-patch-control status.>> "%PREFIX%\.messages.txt"
echo If you are removing <feature>, run these three commands in order, adding to the second and third every other feature package this command removed, at the versions conda listed above:>> "%PREFIX%\.messages.txt"
echo   conda install -p "%PREFIX%" -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control>> "%PREFIX%\.messages.txt"
echo   conda install -p "%PREFIX%" -c https://conda.qiyuan.me -c conda-forge <package>=<version>>> "%PREFIX%\.messages.txt"
echo   conda remove -p "%PREFIX%" <package>>> "%PREFIX%\.messages.txt"
:end
