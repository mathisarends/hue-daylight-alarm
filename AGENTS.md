# Working conventions

- No module-level docstrings. Don't add a `"""..."""` docstring at the top of a
  file explaining what it contains or the conventions it follows.
- Be sparing with comments and docstrings. Don't restate what the code already
  says, don't explain a name that is already clear, and don't narrate the plan
  for future work. Write one only where the code cannot carry the point itself
  -- a non-obvious constraint, a decision that looks wrong without the reason,
  a foreign API behaving unexpectedly. When in doubt, leave it out.
- Commit in small, incremental steps once the behavior of a change has been
  verified (tests pass, lint is clean). Prefer several small commits over one
  large one.
- Ask the user before committing when something is unclear or the change is
  critical/risky, so they can review the diff first.
- Commit straight to `main`. Don't open a side branch for ordinary work --
  this is a single-maintainer project and the branch only adds a merge step.
