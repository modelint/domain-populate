# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this does

`domain-populate` (package `mi-domain-populate`, command `domaindb`) takes a **populated Shlaer-Mellor
metamodel** (an mmdb `*.ral` TclRAL database describing one or more modeled domains) and, for **each**
domain in it, generates a standalone TclRAL database (`<Alias>.ral`) whose schema and referential
constraints are derived from the metamodel and whose instances come from a context file. It is one stage
in the Model Integration xUML toolchain — the input mmdb is produced upstream by `xuml-populate`'s
`modeldb` command; the output domain db is consumed downstream.

The three inputs (see README for the full example):
- `-s` **system**: the populated metamodel `*.ral` file (e.g. `mmdb_elevator.ral`).
- `-c` **context**: a `*.sip` scenario instance population file (parsed by the `sip-parser` package) giving
  initial instances + initial states per class.
- `-t` **types**: a `*.yaml` map from each domain-model Scalar (user type) to a TclRAL system type
  (`string`, `int`, `double`, `boolean`).

## Commands

```bash
# Install for development (editable + dev deps: pytest, bump2version)
pip install -e ".[dev]"

# Run against the bundled example (from within a scratch dir)
domaindb -E                              # copy src/examples/ -> ./examples in cwd
domaindb -s mmdb_elevator.ral -c EVMAN_one_bank1.sip -t EVMAN_types.yaml -o
#   -o  also writes a human-readable <alias>.txt dump per domain
#   -v  verbose: print metamodel + each domain db as tables to console
#   -D  debug: dump metamodel schema to mmdb.txt
#   -L  keep the domaindb.log file (deleted on exit otherwise)

# Tests (pytest configured with pythonpath=src; note: no test files exist yet)
pytest
pytest path/to/test_file.py::test_name

# Release: bumps version in pyproject.toml AND src/dpop/__init__.py, commits, tags
bump2version patch      # or minor / major

# Build & publish (needs the [build] extra: build, twine)
python -m build
```

The `working/` directory holds real input/output files used for manual runs — run `domaindb` from there.

## Architecture

Everything is driven from `System.__init__` — construction *is* execution; there are no separate "run"
methods. The call chain is a cascade of constructors, each doing its work as a side effect of being built:

```
__main__.main
  └─ System(...)                          system.py
       ├─ MetamodelDB.load()              metamodel_db.py — loads mmdb into a PyRAL session
       ├─ reads System + Modeled Domain from mmdb to find each domain
       └─ DomainModelDB(name, alias, …)   domain_model_db.py  (one per domain)
            ├─ Database.open_session(alias)   creates the target TclRAL db
            ├─ build_class_relvars()          Class/Attribute/Identifier -> relvars
            ├─ sort_rels()                    partition rnums: assoc / non-assoc / gen / ordinal
            ├─ build_simple_assocs()          -> Relvar.create_association
            ├─ build_associative_rels()       -> Relvar.create_correlation
            ├─ build_gen_rels()               -> Relvar.create_partition
            ├─ populate() -> Context(self)    context.py — parse sip, expand refs, insert instances
            └─ save()                         Database.save -> <alias>.ral
```

### Key concept: everything is a query against the metamodel

The schema is not hand-coded — it is *reconstructed* by restricting/projecting metamodel relations
(`Class`, `Attribute`, `Identifier_Attribute`, `Association`, `Association_Class`, `Perspective`,
`Attribute_Reference`, `Generalization`, `Subclass`, …) via PyRAL's `Relation` algebra ops. When you need
to understand where a value comes from, trace the `Relation.restrict/project/semijoin/subtract` calls back
to the metamodel relation being queried. Multiplicity strings from the metamodel (`M`, `1`, plus a `c`
suffix when `Conditional == 'True'`) are mapped to PyRAL `Mult` enums via `mult_tclral` in
`domain_model_db.py`.

### Reference expansion (the hard part: context.py)

`Context.__init__` is the most intricate code. A `.sip` population row references other instances by
**alias** (e.g. `@P`) instead of repeating referential attribute values. The code:
1. Expands each class header, replacing every relationship reference (`Rnum>ToClass`) with the concrete
   `from_attribute`(s) it resolves to, looked up in the metamodel's `Attribute_Reference` relation.
2. For each instance row, fills referential attribute values by finding the aliased instance in the
   referenced class's population and copying its `to_attribute` value.
3. Casts each string value to a Python type via `cast_to_dbtype` (looks up the attribute's Scalar in the
   metamodel, then the Scalar's TclRAL type in the user `-t` map). **Booleans are special**: TclRAL wants
   the literal strings `'TRUE'`/`'FALSE'`, not Python bools.
4. Builds a namedtuple per class and inserts all classes inside a single PyRAL `Transaction` (`insert()`).

Initial states (`lifecycle_istates`, `ma_istates`) are parsed and stored but **not** acted on here — a
downstream (unpublished) command consumes them. Single assigners are a known TODO.

### Conventions & gotchas

- **Spaces -> underscores everywhere.** Model class/attribute names contain spaces; TclRAL relvar and
  attribute names cannot. Nearly every metamodel-derived name is passed through `.replace(' ', '_')`
  before it reaches PyRAL. When adding code that names relvars/attrs, do the same.
- **PyRAL is the sole DB interface.** All database work goes through the `pyral` package
  (`Database`, `Relvar`, `Relation`, `Transaction`, `rtypes`). Don't shell out to TclRAL directly.
- **`mmdb`** — the metamodel database's PyRAL session name — is the constant in `db_names.py`; each domain
  db's session name is its `alias`.
- **Exceptions** live in `exceptions.py`; all derive from `DPOPException`. Raise these (not bare
  `Exception`) and log with `_logger.exception(msg)` before raising, matching existing code.
- Currently only single-domain systems are exercised/tested, though the loop over domains is general.