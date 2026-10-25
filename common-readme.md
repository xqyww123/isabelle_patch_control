## Isabelle and its feature packages

Isabelle is the conda package `isabelle`, the official release unchanged. A *feature package*,
such as `isabelle-light-locale`, changes Isabelle's sources inside your environment when it is
installed and puts them back when it is removed. The tool that does this, `isabelle-patch-control`,
comes in with the feature packages as their dependency.

Install Isabelle with a feature (always name `isabelle` itself, see below):

```
conda create -n isabelle -c https://conda.qiyuan.me -c conda-forge isabelle isabelle-light-locale
```

Update everything in the environment:

```
conda update --all -c https://conda.qiyuan.me -c conda-forge
```

Give both `-c` arguments every time: the Isabelle channel has no `python` and no `git`, which the
tool needs, and conda-forge has them. (You can leave them out only if both channels are in your
global `.condarc`; a `.condarc` inside the environment does not apply to `conda ... -n`.)

Name `isabelle` in the install command: a feature package depends on one exact build of
`isabelle`, so conda would install Isabelle anyway, but only as a dependency. Removing the feature
package later would then remove Isabelle and its user directory with it, because conda removes
dependencies nobody asked for. Naming `isabelle` makes it a package you asked for, so it stays.

To see what is installed and whether every feature is in place:

```
isabelle-patch-control status
```

Each line is one feature: `applied` means its changes are present in Isabelle's sources;
`not-applied` means they are not; `half-applied` means some of its files have them and some do
not; `CONFLICT` means a file has content the tool does not recognise, and the message says how to
fix it. `isabelle-patch-control status -v` lists every changed file.

After a feature is applied or reversed, Isabelle rebuilds every heap that was not built from
exactly these sources on first use (HOL takes several minutes). To do it right away:
`isabelle build -b HOL`.
