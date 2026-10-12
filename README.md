# Philosophy a Day

A concise, source-linked introduction to one philosophical idea each day. The archive spans traditions, periods, and disciplines; each entry distinguishes an idea's early roots from its later systematic development where needed.

The site is published with GitHub Pages at <https://art22s.github.io/philosophy-a-day/>. Daily editions are stored as JSON in `reports/` and rendered into the home page by `scripts/publish.py`.

## Add an edition

Create a UTF-8 JSON file at `reports/YYYY-MM-DD-HHMMSSNNNNNNNNN.json` with `date`, `title`, `when`, `people`, `origin`, `idea`, `relevance`, and a non-empty `sources` array of `{ "name", "url" }` objects. The local timestamp makes every run a distinct edition, including multiple editions on the same day. Then run:

```sh
python3 scripts/publish.py reports/YYYY-MM-DD-HHMMSSNNNNNNNNN.json
```

The publisher validates and escapes all content, commits only the report and generated `index.html`, pushes without force, and checks the public page for the new edition.
