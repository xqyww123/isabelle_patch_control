# isabelle-patch-control

GitHub: <https://github.com/xqyww123/isabelle_patch_control>

`isabelle-patch-control` applies the Isabelle *feature packages* installed in a conda environment
to that environment's Isabelle, reverses them when they are removed, and reports the state of
every feature. It is a framework: it carries no patches of its own; each feature package carries its
own. How it works inside: [develop.md](develop.md).

The text between the two rules below is the text every feature package's README starts with, with
`<package>` and `<feature>` replaced by that package's own names; it lives in
[`common-readme.md`](common-readme.md) and the release workflow copies it from there.

---

## Isabelle and its feature packages

Isabelle is the conda package `isabelle`, the official release unchanged. A *feature package*
changes Isabelle's sources inside your environment when it is installed and puts them back when it
is removed. The tool that does this, `isabelle-patch-control`, comes in with the feature packages as
their dependency. A feature package is built on Isabelle itself or on one other feature package,
which conda installs with it, so `status` may list more features than you named. Two feature
packages built on the same feature package, or both directly on Isabelle, do not work together.

Install Isabelle with the feature package `<package>`:

```
conda create -n isabelle -c https://conda.qiyuan.me -c conda-forge isabelle <package>
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
package.) It names every feature in the environment, first the ones `<package>` is built on, then
`<feature>`. A healthy environment ends like this:

```
Feature `<feature>` is applied.

Everything is in order.
```

If it ends with `Everything is in order.`, you are done; otherwise its last lines say what to do.

With the environment activated, update everything in it later with this, then run
`isabelle-patch-control status` again. `<version>` is the version of `isabelle` that
`conda list --full-name isabelle` shows, such as `2026`; `conda update --all` would instead move the
environment to a newer Isabelle release once the channel has one. When the update brings a new build
of `isabelle`, it deletes this environment's Isabelle user directory (its heaps, `etc/settings`,
components registered by hand), as removing Isabelle does.

```
conda install --update-all "isabelle==<version>" -c https://conda.qiyuan.me -c conda-forge
```

What to do when a feature cannot be applied or conda printed `Rolling back transaction`, how
removing and re-installing packages work, and more: `isabelle-patch-control help`.


---

## Documentation

- [reference.md](reference.md): every command, option, message and exit code.
- [develop.md](develop.md): how the tool works inside, the layout of the package, the tests.
- [The SKILL `isabelle-patch-feature`](.claude/skills/isabelle-patch-feature/SKILL.md): how the
  features in MLML (<https://github.com/xqyww123/MLML>) are developed, released and upgraded to a
  new Isabelle release.
- [RELEASE.md](RELEASE.md): the reference behind the SKILL's release steps: why each checklist
  point matters, the files of the package directory, how the packages are built and published.
- [AGENTS.md](AGENTS.md): what to do in each situation, for users and AI agents; `isabelle-patch-control help` prints it.
- Plan and review record: `ai-artifacts/ISABELLE_PATCH_CONTROL_PLAN.md`.

