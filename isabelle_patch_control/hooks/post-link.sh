if [ -x "$PREFIX/bin/isabelle-patch-control" ]; then
  "$PREFIX/bin/python" -I -X utf8 -m isabelle_patch_control conda-hook post-link \
    || echo "isabelle-patch-control: the hook could not run. Run: conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle-patch-control; then: isabelle-patch-control apply" >> "$PREFIX/.messages.txt"
elif [ -d "$PREFIX/share/isabelle_patch_control/features.d" ]; then
  echo "isabelle-patch-control is not installed, so the installed Isabelle feature packages are not applied. Run: conda install -c https://conda.qiyuan.me -c conda-forge isabelle-patch-control; then: isabelle-patch-control apply" >> "$PREFIX/.messages.txt"
fi
