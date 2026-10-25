---
name: vietnamese-translator
description: Translate text into natural, fluent Vietnamese while keeping technical terms, code identifiers, and product names in English, and preserving the original formatting (Markdown, code blocks, lists, headings, links, tables). Use whenever the user asks to translate something to Vietnamese — phrases like "translate to Vietnamese", "dịch sang tiếng Việt", "việt hóa", "bản tiếng Việt", or provides text and asks for a Vietnamese version, even if they don't say the word "translate" explicitly (e.g. "put this in Vietnamese", "can I get this in tiếng Việt?").
---

# Vietnamese Translator

Translate text into natural, fluent Vietnamese. This is for technical documentation and articles, so the goal is clear, idiomatic technical Vietnamese — not a word-for-word rendering — while keeping technical vocabulary in English exactly as the source uses it.

## The one core rule

**Technical terms stay in English. Everything else becomes Vietnamese.**

Read the whole passage before translating. The line that matters is between *technical vocabulary* (which is conventionally kept in English in Vietnamese technical writing) and *ordinary prose* (which is translated naturally). When in doubt, keep a term in English if a Vietnamese developer reading technical docs would expect to see it untranslated.

### Keep in English

- **Domain and technical terms**: `API`, `SDK`, `cache`, `buffer`, `thread`, `process`, `database`, `framework`, `library`, `server`, `client`, `request`, `response`, `endpoint`, `repository`, `branch`, `commit`, `deployment`, `container`, `cluster`, `load balancer`, `middleware`, `callback`, `namespace`, `schema`, `query`, `migration`, etc.
- **Acronyms and initialisms**: `CPU`, `RAM`, `HTTP`, `HTML`, `CSS`, `JSON`, `YAML`, `REST`, `SQL`, `TLS`, `CI/CD`, `DNS`, `URL`, `URI`.
- **Product, brand, and tool names**: `React`, `Docker`, `Kubernetes`, `Git`, `Node.js`, `PostgreSQL`, `AWS`, `Vercel`, `Tailwind`.
- **Code identifiers**: function, variable, class, and method names, e.g. `getUser`, `handleSubmit`, `UserService`.
- **Commands, flags, and syntax**: `npm install`, `git push --force`, `curl -X POST`, `--recursive`.
- **File paths and URLs**: `/src/utils/helper.ts`, `https://example.com/docs`, `package.json`.
- **Units and version numbers**: `500ms`, `2.4GHz`, `v3.1.0`, `10GB`.

### Translate to Vietnamese

Everything that is ordinary language: verbs, everyday nouns, adjectives, explanations, instructions, transitions, examples, caveats. For example, "you can cache the result" becomes *bạn có thể cache kết quả* — the verb and object are Vietnamese, `cache` stays English.

### Handle the in-between

Some words sit between technical and everyday. These are fine either way; pick what reads naturally and stay consistent within the passage:

- `user`, `data`, `test`, `build`, `run` are often kept in English in technical writing (*người dùng* is also fine for `user`). Choose one convention per passage and hold it.
- `bug`, `fix`, `feature`, `issue` are frequently kept in English. Either keep or translate (*lỗi*, *sửa*, *tính năng*, *vấn đề*), but be consistent.
- Short imperative commands in docs ("Run", "Install", "Configure") translate naturally as verbs (*Chạy*, *Cài đặt*, *Cấu hình*).

## Preserve formatting exactly

Reproduce the source structure, changing only the prose. Do not reformat.

- **Markdown**: keep headings, bold, italic, blockquotes, horizontal rules, and their nesting levels exactly as given.
- **Code blocks and inline code**: leave them completely untouched — never translate inside backticks or fenced code blocks, even if a comment inside is in English.
- **Links**: keep the URL and the link text translated, e.g. `[see the docs](https://...)` → `[xem tài liệu](https://...)`. If the link text is a code identifier, leave it.
- **Lists and tables**: keep the same items, rows, and columns; translate the cell and list-item text. Keep table header alignment rows (`---`, `:--:`).
- **HTML/JSX embedded in docs**: translate only visible text; leave tags, attributes, class names, and values alone.

## Translation quality

- **Natural, not literal.** Restructure sentences so they read like idiomatic Vietnamese. English passives ("the file is saved") often read better as active or as Vietnamese's more flexible subject-dropping style (*tệp được lưu* or *hệ thống lưu tệp*). "It is important to…" becomes *cần…* rather than a clunky literal rendering.
- **Correct diacritics.** Every Vietnamese word must carry the correct tone marks (dấu sắc, huyền, hỏi, ngã, nặng) and vowel marks (ă, â, ê, ô, ơ, ư). Never drop diacritics.
- **Register.** Match the source's tone — formal for official docs, conversational for blog posts and tutorials. Address the reader as *bạn* (or *quý khách* for very formal) consistently.
- **Keep technical terms in their original form.** Do not pluralize English nouns with Vietnamese markers, and do not add diacritics to English words. `APIs`, `caches`, `servers` stay as they are.
- **Respect English-only conventions.** Keep camelCase, snake_case, and kebab-case identifiers exactly as written, with no added spaces or punctuation.

## Workflow

1. Read the full source once to understand context and which terms recur (so you can stay consistent).
2. Translate the prose, keeping the formatting structure intact.
3. Review: check that every technical term you intended to keep is still in English, diacritics are correct, and the Vietnamese reads naturally. Run the bundled checker to catch the mechanical failures: `python scripts/check_format.py --source src.md --target vi.md` — it verifies fenced code blocks are byte-identical, no inline-code token or URL was dropped, headings/tables kept their shape, and the target actually contains Vietnamese diacritics.
4. Output only the translation (or the translation alongside the source if the user asked for a side-by-side comparison). If the source was very long, you may offer a summary of what you changed, but the default deliverable is just the translated text.

## Examples

**Example 1 — README snippet**

Source:
```markdown
## Caching

The server caches responses in memory to reduce latency. You can clear the cache by restarting the service.
```

Translation:
```markdown
## Caching

Máy chủ cache các phản hồi trong bộ nhớ để giảm độ trễ. Bạn có thể xóa cache bằng cách khởi động lại service.
```

**Example 2 — instruction**

Source:
> Run `npm run build` to compile the project. If it fails, check that your `NODE_ENV` is set correctly.

Translation:
> Chạy `npm run build` để biên dịch dự án. Nếu thất bại, hãy kiểm tra xem biến `NODE_ENV` đã được đặt đúng chưa.

## Edge cases

- **Short or ambiguous text** (a title, a button label, a single sentence): translate it plainly; do not add commentary or ask for clarification unless it is genuinely untranslatable without context.
- **Already-partially-Vietnamese text**: translate the remaining non-Vietnamese prose, leave existing Vietnamese and technical terms as they are, and keep the whole consistent.
- **Code-only content**: if there is no prose to translate, say so and return the code unchanged rather than forcing a translation.
- **Untranslatable puns or idioms**: prefer a natural Vietnamese equivalent over a literal rendering; if none fits, translate the meaning and drop a brief note.
