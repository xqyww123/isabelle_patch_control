## Isabelle and its feature packages

Isabelle is the conda package `isabelle`, the official release unchanged. A *feature package*,
such as `isabelle-light-locale`, changes Isabelle's sources inside your environment when it is
installed and puts them back when it is removed. The tool that does this, `isabelle-patch-control`,
comes in with the feature packages as their dependency. A feature package is built on Isabelle itself
or on one other feature package, which conda installs with it, so `status` may list more features than
you named. Two feature packages built on the same feature package, or both directly on Isabelle, do
not work together.

Install Isabelle with a feature package:

```
conda create -n isabelle -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale
```

Name `isabelle` itself, as above: otherwise conda installs it only as a dependency, and removing
the last feature package later removes Isabelle too, with this environment's Isabelle user
directory. Give both `-c` arguments to every `conda create`, `conda install` and `conda update`:
without them conda does not see the Isabelle packages, or lacks the `python` and `git` the tool
needs. (You can leave them out if both channels are in your global `.condarc`.)

Check that every feature is in place:

```
conda activate isabelle
isabelle-patch-control status
```

(`command not found` means that the environment is not activated, or that it has no feature
package.) A healthy environment looks like this:

```
Checked the Isabelle sources in /home/you/miniconda3/envs/isabelle/isa against 4 feature packages.

Feature `expose_foreign` is applied.
Feature `future_assign_interrupt` is applied.
Feature `fast_abbrev_printing` is applied.
Feature `light_locale` is applied.

Everything is in order.
```

If it ends with `Everything is in order.`, you are done; otherwise its last lines say what to do.

With the environment activated, update everything in it later with this, then run
`isabelle-patch-control status` again. `<version>` is the version of `isabelle` that
`conda list --full-name isabelle` shows, such as `2025.2`; `conda update --all` would instead move the
environment to a newer Isabelle release once the channel has one. When the update brings a new build
of `isabelle`, it deletes this environment's Isabelle user directory (its heaps, `etc/settings`,
components registered by hand), as removing Isabelle does.

```
conda install --update-all "isabelle==<version>" -c https://conda.qiyuan.me -c conda-forge
```

What to do when a feature cannot be applied or conda printed `Rolling back transaction`, how
removing and re-installing packages work, and more: `isabelle-patch-control help`.
