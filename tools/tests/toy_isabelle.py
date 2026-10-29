"""The toy isabelle of the toy channel (tools/tests/toy-channel.sh; patch tool plan decision 15),
shipped as isa/bin/isabelle.py and run by the environment's python from isa/bin/isabelle (bash) and
isa/bin/isabelle.bat.  It answers what the hooks and tools/accept ask:

  getenv -b ISABELLE_HOME_USER|ISABELLE_HOME   on Windows in the /cygdrive/ form isabelle.bat prints
  version [-i]                                 the identifier, or etc/ISABELLE_ID
  components -u|-x <dir>                       <dir> added to or removed from the user's etc/components

As the isabelle package's post-link, `--rerun-post-links` re-runs the post-link of every installed
package that depends on isabelle directly, dependencies first (plan §0 items 26, 33, 34; the CI plan
implements the real one).  One self-contained file: python writes no __pycache__ for a script.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

WINDOWS = os.name == "nt"
HOME = Path(__file__).resolve().parent.parent          # isa/
PREFIX = HOME.parent


def cygwin(p: Path) -> str:
    s = p.as_posix()
    return f"/cygdrive/{s[0].lower()}{s[2:]}" if WINDOWS and s[1:2] == ":" else s


def user_dir() -> Path:
    return Path.home() / ".isabelle" / f"Isabelle2025-2-conda-{PREFIX.name}"


def components(verb: str, entry: str):
    f = user_dir() / "etc" / "components"
    if verb == "-x" and not f.is_file():
        return
    lines = f.read_text().splitlines() if f.is_file() else []
    lines = (lines + [entry] if entry not in lines else lines) if verb == "-u" else [x for x in lines if x != entry]
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name("components.new")
    tmp.write_text("".join(x + "\n" for x in lines))
    os.replace(tmp, f)


def rerun_post_links():
    records = {d["name"]: d for p in (PREFIX / "conda-meta").glob("*.json") if (d := json.loads(p.read_text()))}
    direct = {n: d for n, d in records.items() if any(dep.split()[0] == "isabelle" for dep in d.get("depends", []))}
    order, seen = [], set()

    def visit(n):
        if n not in seen:
            seen.add(n)
            for dep in direct[n].get("depends", []):
                if dep.split()[0] in direct:
                    visit(dep.split()[0])
            order.append(n)
    for n in sorted(direct):
        visit(n)
    for n in order:
        d = direct[n]
        if WINDOWS:
            script = PREFIX / "Scripts" / f".{n}-post-link.bat"
            command = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(script)]
        else:
            script = PREFIX / "bin" / f".{n}-post-link.sh"
            command = ["bash", str(script)]
        if script.is_file():
            subprocess.run(command, env={**os.environ, "PREFIX": str(PREFIX), "PKG_NAME": n,
                                         "PKG_VERSION": d["version"], "PKG_BUILDNUM": str(d["build_number"])})


def main(args: list[str]) -> int:
    match args:
        case ["getenv", "-b", "ISABELLE_HOME_USER"]:
            print(cygwin(user_dir()))
        case ["getenv", "-b", "ISABELLE_HOME"]:
            print(cygwin(HOME))
        case ["version"]:
            print((HOME / "etc" / "ISABELLE_IDENTIFIER").read_text().strip())
        case ["version", "-i"]:
            print((HOME / "etc" / "ISABELLE_ID").read_text().strip())
        case ["components", ("-u" | "-x") as verb, entry]:
            components(verb, entry)
        case ["--rerun-post-links"]:
            rerun_post_links()
        case _:
            print(f"toy isabelle: {' '.join(args)}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
