# Working conventions

- No module-level docstrings. Don't add a `"""..."""` docstring at the top of a
  file explaining what it contains or the conventions it follows.
- Commit in small, incremental steps once the behavior of a change has been
  verified (tests pass, lint is clean). Prefer several small commits over one
  large one.
- Ask the user before committing when something is unclear or the change is
  critical/risky, so they can review the diff first.
- Commit straight to `main`. Don't open a side branch for ordinary work --
  this is a single-maintainer project and the branch only adds a merge step.
