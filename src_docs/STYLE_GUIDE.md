# Documentation Style Guide

Rules for writing `vexy-lines-run` documentation.

## Voice and tone

- **Second person, active voice.** "Click **+** to add files" not "Files can be
  added by clicking the plus button."
- **Direct.** State what the user does and what happens.  Omit filler phrases
  ("simply", "just", "easily", "please note that").
- **Precise over friendly.** "The toggle is hidden when format is not MP4" is
  better than "The audio toggle might not show up in some cases."
- No exclamation marks.

## Structure

- Start every page with a one-sentence statement of purpose.
- Use H2 (`##`) for major sections, H3 (`###`) for subsections.  Avoid H4.
- Lead with the common case.  Put edge cases, errors, and caveats in later
  sections or collapsed admonitions.
- Tables for comparisons (format options, platform notes, error messages).
- Fenced code blocks for every command, snippet, and file path.

## Language

- Package name: `vexy-lines-run` (lowercase, hyphenated) in prose and as the
  PyPI name.  `vexy_lines_run` only in Python import paths.
- "The app" not "the application" or "the tool."
- "Export ▶" (with the Unicode play symbol) when referring to the button label.
- "Style panel" not "style picker" or "style selector."
- "`.lines` file" (backtick around the extension, space before "file").
- "MCP" when referring to the protocol or server; "Vexy Lines app" when
  referring to the desktop application that runs the server.
- Frame numbers are 1-indexed in user-facing text ("frame 1" = first frame).

## Code blocks

Specify the language for every fenced block:

````markdown
```bash
pip install vexy-lines-run
```
````

Use `bash` for shell commands, `python` for Python snippets, `bat` for
Windows batch commands, `yaml` for YAML.

## File and path conventions

- Use POSIX paths in examples unless the example is Windows-specific.
- Truncate long paths with `…` from the left: `…/projects/art/kitty.lines`.
- Use `<placeholder>` angle-bracket syntax for values the user must supply.

## Admonitions

Use MkDocs admonitions sparingly:

```markdown
!!! note
    For something genuinely easy to miss.

!!! warning
    For something that causes data loss or a hard-to-debug failure.
```

Do not use admonitions for normal caveats — put those inline.

## Screenshots and diagrams

- ASCII art diagrams are preferred over images when the structure can be
  expressed clearly in text (layout grids, pipeline flows).
- When referencing a screenshot, add alt text that describes what is shown
  functionally: `![Lines tab: nine files loaded, purple lettering preview](...)`.
- Do not use screenshots for error dialogs or text that can be reproduced as
  a code block.

## Changelog entries

Format: `YYYY-MM-DD — Short Title (Issue #N if applicable)`

Then bullet points grouped by type:

```markdown
- **feat**: What was added.
- **fix**: What was corrected.
- **docs**: Documentation-only change.
- **refactor**: Internal restructuring with no user-visible effect.
- **test**: Test additions or fixes.
```

End each changelog entry with `- **test**: N tests passing.`

## Navigation

New pages go in `mkdocs.yml` under `nav:` in logical reading order:

1. Overview / index
2. Installation and troubleshooting
3. User-facing guides (GUI Tour, GUI Guide)
4. Technical reference (video processing, API reference)
5. Examples
6. Changelog

Do not nest nav entries more than one level deep.
