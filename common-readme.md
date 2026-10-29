## Isabelle and its feature packages

Isabelle is the conda package `isabelle`, the official release unchanged. A *feature package*,
such as `isabelle-light-locale`, changes Isabelle's sources inside your environment when it is
installed and puts them back when it is removed. The tool that does this, `isabelle-patch-control`,
comes in with the feature packages as their dependency.

Two names used below: `<prefix>` is the environment's directory (`$CONDA_PREFIX` once the
environment is activated, `conda env list` shows it), and `isa/` is Isabelle's own directory inside
it, `<prefix>/isa`.

Install Isabelle with a feature (always name `isabelle` itself, see below):

```
conda create -n isabelle -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale
```

Update everything in the environment, then check:

```
conda update --all -c https://conda.qiyuan.me -c conda-forge
isabelle-patch-control status
```

If every feature line of the second command says `applied`, you are done. Give both `-c` arguments every time: the Isabelle channel has no `python` and no `git`, which the
tool needs, and conda-forge has them. (You can leave them out only if both channels are in your
global `.condarc`; a `.condarc` inside the environment does not apply to `conda ... -n`.) If you
forget them, conda does not see the Isabelle channel and cannot update `isabelle` or the feature
packages; run the command again with both.

Name `isabelle` in the install command: a feature package depends on one exact build of
`isabelle`, so conda would install Isabelle anyway, but only as a dependency. Removing the feature
package later would then remove Isabelle and its user directory with it, because conda removes
dependencies nobody asked for. Naming `isabelle` makes it a package you asked for, so it stays.

To see what is installed and whether every feature is in place, with the environment activated
(`conda activate isabelle`; without activating: `conda run -n isabelle isabelle-patch-control status`):

```
isabelle-patch-control status
```

The command exists only in an environment that has a feature package installed (it comes in as
their dependency); `command not found` means either that the environment is not activated or that
no feature package is installed there. A healthy environment looks like this, and the command
exits 0:

```
tree /home/you/miniconda3/envs/isabelle/isa   features.d /home/you/miniconda3/envs/isabelle/share/isabelle_patch_control/features.d
applied expose_foreign          Isabelle2025-2/expose_foreign/1          1 file
applied future_assign_interrupt Isabelle2025-2/future_assign_interrupt/1 1 file
applied light_locale            Isabelle2025-2/light_locale/1            32 files
```

The first line says where the tool looked; each line after it is one feature, listed from the
bottom of the chain upwards. `applied` on every feature line (and exit code 0) means everything is
fine. With no feature package installed the command prints `no feature packages installed` and
exits 0, which is also fine. Otherwise: `not-applied` means the feature's changes are not in
Isabelle's sources, and `half-applied` that some of its files have them and some do not; in both
cases run `isabelle-patch-control apply`, which puts in place whatever is missing and nothing else.
`CONFLICT` means a file has content the tool does not recognise; *When something went wrong* below
says how to fix it. `(hole below)` after an `applied` line means a feature printed above it in the
list is not fully applied; fix that feature first, as described for its state.
`isabelle-patch-control status -v` lists every changed file.

Installing, updating or removing packages applies and reverses the features by itself, so after
one of those commands you do not run `apply`; you run it when a message from conda asked you to
(the tool's messages are the paragraphs of conda's output that start with `isabelle-patch-control:`;
they say when the tool could not run or another run held its lock), or after `status` showed
`not-applied` or `half-applied`.

After a feature is applied or reversed, Isabelle rebuilds every heap that was not built from
exactly these sources on first use (HOL takes several minutes). To do it right away:
`isabelle build -b HOL`.

## Removing, re-installing, and what conda does on its own

- `conda remove isabelle-light-locale` reverses the feature's changes and deletes the files it
  created. conda also removes every package that was installed only as a dependency and that
  nothing you asked for still needs: the feature packages below it in the chain,
  `isabelle-patch-control`, and `isabelle` itself if you never named it. `conda remove --force
  <package>` removes that one package and nothing else; the tool still reverses its changes.
- Installing a package that is already installed changes nothing and does not make it a package
  you asked for (`conda env export --from-history` lists the packages you did ask for by name).
  `conda install --force-reinstall <package>` does, at the price of reversing and re-applying its
  changes. For `isabelle` the price is higher: the `isabelle` package deletes the environment's
  Isabelle user directory whenever it is removed or replaced (see below).
- Every `conda install` / `conda update` of `isabelle` or of a feature package re-applies the
  installed features by itself: a new `isabelle` build re-applies every feature, and a new version
  of one feature package re-applies it and the features above it.
- Features form a chain, each built on the one below. When a feature reports `CONFLICT`, the tool
  applies none of the features above it until the CONFLICT is fixed. Re-installing a feature
  package below the CONFLICT reverses it and everything above it, then re-applies up to the
  CONFLICT again. `isabelle-patch-control status -v` names the file; *You edited a file under
  `isa/`* below says how to fix it.
- Only conda runs the step that reverses a feature on removal. mamba 2.x, micromamba and pixi do
  not, so a feature removed with them leaves its changes in Isabelle, and the files it created stay.
  To get the original sources back and the remaining features re-applied, reinstall `isabelle` as
  described under *You edited a file under `isa/`*; the created files stay even then, but nothing
  loads them any more.

## When something went wrong

**A conda command was interrupted (Ctrl-C).** conda rolls the whole command back and deletes
`conda-meta/history`, after which it no longer treats the directory as an environment; the
changes the command had already made under `isa/` stay. Until repaired, every `isabelle` command
may print `### Missing Isabelle component`. `isabelle-patch-control status` prints the repair
while `history` is missing. Either recreate the environment in place,

```
conda create -p <prefix> -c https://conda.qiyuan.me -c conda-forge <every package you want to keep, and the one that was being installed>
```

(conda itself will not list the environment's packages while `history` is missing; `ls
<prefix>/conda-meta` shows one `<package>-<version>-<build>.json` per installed package), or
restore the file and install again:

```
touch <prefix>/conda-meta/history        # Windows: type nul > "<prefix>\conda-meta\history"
conda install -c https://conda.qiyuan.me -c conda-forge <those same packages>
```

If you do not want that feature after all, repair first, then `conda remove <its package>`: the
tool then reverses its changes and deletes its files, which a reinstall of `isabelle` alone would
not do for files the feature created.

**You edited a file under `isa/`.** `isabelle-patch-control status` reports the file as
`CONFLICT` (if `status -v` marks the file `(created by the feature)`, see the next paragraph
instead: a reinstall does not fix that case and costs the user directory). If you remember exactly
what you changed, undo it and run `isabelle-patch-control apply`. Otherwise save your edit elsewhere
and reinstall `isabelle`. Before that, copy anything of your own out of `isa/` and out of this
environment's Isabelle user directory (`isabelle getenv -b ISABELLE_HOME_USER` prints it; it is a
directory under `~/.isabelle`): the reinstall deletes that
directory, with the heaps built in it, its `etc/settings` and preferences, and every component you
registered by hand with `isabelle components -u`. Installed packages register their components
again; your own settings do not come back. Then:

```
conda install -c https://conda.qiyuan.me -c conda-forge --force-reinstall isabelle
```

Every file of the `isabelle` package is replaced and the installed features are re-applied; run
`isabelle-patch-control status` afterwards. If the edit was made *in place* (an editor that writes
into the existing file, such as vim with `backupcopy=auto`), it went through the hard link into
conda's package cache, and a plain reinstall would bring the edit back. The CONFLICT message
detects this case and names the cache directory to delete first; conda re-creates it from the
downloaded archive. Other environments built from the same cache (`conda env list`) may share the
edited file without reporting anything; reinstall `isabelle` there too. A personal edit of a file
that a feature also changes reads `CONFLICT` again every time; make such experiments in a separate
Isabelle installation (for example the official release), not under `isa/`.

**You edited a file a feature created.** Move your copy aside, then `isabelle-patch-control apply`.

