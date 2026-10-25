---
name: email-writer
description: Write, rewrite, and reply to emails in a clear, natural, audience-appropriate voice. Use whenever the user asks to draft an email, write a message to someone, reply to or respond to an email or message they paste in, improve or polish an existing draft, make an email sound more professional (or friendlier, firmer, shorter, etc.), or match a specific tone — even if they don't say the word "email" (e.g. "can you write to my boss about...", "how should I respond to this?", "make this sound nicer", "help me follow up with a client", "soạn giúp tôi một email", "viết thư trả lời"). Handles English and Vietnamese, formal and casual.
---

# Email Writer

Write emails people actually want to read and answer. The goal is a message that is clear, appropriately toned, and easy to act on — not a wall of polished-sounding filler. Deliver **two or three distinct options** by default so the user can pick the voice they like.

## Core principles

- **Lead with the point.** Put the reason you're writing in the first sentence or two. Busy people skim; don't bury the ask under pleasantries.
- **One email, one job.** If the email is doing three unrelated things, say so and offer to split it. Don't force everything into one message.
- **Match the relationship.** The same request to your manager, a client, and a friend should read differently. The greeting, level of directness, and sign-off are where tone mostly lives.
- **Sound like a person, not a template.** Avoid corporate filler and AI-sounding clichés (see "What to avoid"). Keep sentences short and concrete.
- **End with a clear next step.** A specific question, a deadline, a request to review — whatever moves it forward. "Let me know your thoughts" is a last resort, not a default.
- **Respect the language and culture.** Follow the conventions of whichever language you're writing in (see below). Don't mix English and Vietnamese styles within one email.

## Workflow

1. **Figure out the goal.** What outcome does the user want from the recipient — information, a decision, a meeting, an apology, an introduction? If the audience, relationship, or desired outcome is unclear, ask one or two focused questions, then go. Bias toward drafting over interrogating.
2. **Check what's already there.** If the user pasted an email to reply to, extract the questions/asks and answer them all. If they gave a draft to improve, preserve its facts, intent, and any attachments/numbers/names exactly.
3. **Draft the options.** Produce 2–3 variations that differ in a meaningful way (e.g. brief vs. warm, direct vs. diplomatic, formal vs. casual) rather than three near-identical rewordings. Label each option with what it's for.
4. **Deliver.** Give the email(s) in ready-to-send form (subject + greeting + body + sign-off), followed by a one-line note on the key choice or tradeoff per option. Offer a placeholder name if none was provided (e.g. `[Your name]`).

## Email anatomy

Build each email from these parts, tuned to the tone:

- **Subject line** — specific and short (roughly 3–8 words). State the topic or the ask, not just "Hello" or "Quick question." For replies, reuse the original subject with a `Re:` prefix; change it only if the topic changed.
- **Greeting** — chosen by formality and relationship (see table below).
- **Opening** — one line of context or courtesy, only if it's genuinely needed. Skip it when the relationship is well-established and you're getting straight to business.
- **Body** — the point, then any necessary detail. Use short paragraphs and, when there are multiple items, a numbered list. Numbers, dates, and specific asks go here.
- **Closing** — restate the ask or next step if the body was long; otherwise skip straight to sign-off.
- **Sign-off** — matched to the greeting's formality.

## Tone and greeting/sign-off by relationship

Use these as defaults, then adjust to the actual relationship. The greeting and sign-off should sit at the same formality level.

| Context | Greeting (EN) | Sign-off (EN) | Greeting (VI) | Sign-off (VI) |
|---|---|---|---|---|
| Formal / first contact | `Dear [Title] [Name],` | `Sincerely,` / `Kind regards,` | `Kính gửi [Anh/Chị/Ông/Bà] [Name],` | `Trân trọng,` |
| Professional / known contact | `Hi [Name],` / `Hello [Name],` | `Best regards,` / `Best,` | `[Anh/Chị] [Name] thân mến,` / `Chào [Anh/Chị] [Name],` | `Trân trọng,` / `Thân ái,` |
| Casual / internal team | `Hi [Name],` / `Hey [Name],` | `Thanks,` / `Cheers,` | `Chào [Name],` / `[Name] ơi,` | `Thân,` / `Cảm ơn,` |

Notes:
- In Vietnamese, "anh/chị" (older peer), "em" (younger), "cô/chú" (older relative/aunt/uncle), and "ông/bà" (very formal) depend on age and relationship. If you don't know, default to the neutral `Chào [Name]` or ask the user how to address the recipient.
- In English, when you don't know the name, `Dear Hiring Manager,` / `Dear [Team] team,` / `To whom it may concern,` are fallbacks; prefer the specific person or team when possible.
- Don't over-formalize an established relationship — "Dear Mr. Chen" to a coworker you chat with daily reads as cold.

## Language handling

- **Detect the language** from the user's message and the recipient's context, and write in that language. If the user writes in Vietnamese, reply in Vietnamese; if English, English — unless they ask otherwise.
- **Keep names, company names, product names, and technical terms** in their original language even inside the other language.
- **Vietnamese specifics:** use correct diacritics throughout. Prefer the natural first-person "mình/tôi/em/anh/chị" consistently within one email — don't switch between them. Use "Dạ"/"Vâng" for politeness in formal replies where natural.
- **English specifics:** watch subject–verb agreement and punctuation; use contractions ("I'll", "we're") in casual/neutral tones, avoid them in very formal ones.

## What to avoid

- **AI-sounding filler:** "I hope this email finds you well", "Just circling back", "Per my last email", "I wanted to reach out", "touching base", "going forward", "at your earliest convenience". Rewrite these as plain statements.
- **Empty politeness** that pads the email without adding meaning. A short, direct email is more respectful than a long, vague one.
- **Over-apologizing** ("sorry to bother you", "apologies for the delay" twice). One genuine apology where warranted is enough.
- **Walls of text.** Break into short paragraphs; use a list when there are 2+ distinct items.
- **Vague asks.** "Let me know your thoughts" → "Could you confirm by Friday whether we can ship this?"
- **Mixing languages** in a single sentence, or mixing formal and casual conventions within one email.
- **Inventing facts.** Never make up names, dates, amounts, or commitments. Use placeholders like `[date]`, `[amount]`, `[name]` when something is unknown, and flag it.

## Rewriting and replying

- **Rewrite/improve:** keep every fact, figure, name, and attachment reference from the original. Fix structure, tone, clarity, and length; don't add new claims. If the user asked for a specific change ("more formal", "shorter", "firmer but polite", "friendlier"), make that the focus of at least one option.
- **Reply:** answer every question or request in the incoming email. Mirror the sender's level of formality, but a touch warmer is fine. Quote or reference the original only when needed to disambiguate; don't restate what they already wrote.

## Edge cases

- **No recipient or context given:** draft a sensible version and use placeholders, or ask one clarifying question if the audience genuinely changes the email (e.g. manager vs. client vs. friend).
- **Sensitive or emotional topics** (apologies, complaints, bad news, salary, resignation): favor the more measured/diplomatic option, keep it brief, avoid defensiveness, and don't over-explain. Note the tradeoff in your one-line summary.
- **Very short request** ("email John about the meeting"): make reasonable assumptions (meeting = propose a time), state them in one line, and draft — don't interrogate.
- **The user wants a single tone, not options:** honor it and return one polished email instead of forcing multiple.
- **Non-email messages** (Slack/DM, SMS, LinkedIn message): apply the same principles but shorten further, and drop the subject line and formal sign-off.

## Examples

**Example 1 — draft (professional, English)**

Request: *Write to my manager asking to move our 1:1 from Thursday to Friday.*

Option A — brief:
> **Subject:** Reschedule our Thursday 1:1
>
> Hi [Name],
>
> Could we move our Thursday 1:1 to Friday? I have a scheduling conflict Thursday afternoon. I'm free any time Friday after 10am.
>
> Thanks,
> [Your name]

Option B — with context:
> **Subject:** Moving our 1:1 to Friday
>
> Hi [Name],
>
> I'd like to move our 1:1 from Thursday to Friday — a client call came up Thursday afternoon that I can't shift. Does Friday after 10am work for you?
>
> Best,
> [Your name]

**Example 2 — reply (Vietnamese)**

Incoming: *"Anh ơi, mai mình họp lúc mấy giờ ạ?"*

> **Subject:** Re: Lịch họp
>
> Chào em,
>
> Mai mình họp lúc 9h sáng nhé, ở phòng họp tầng 3.
>
> Cảm ơn em,
> [Your name]

## Output format

Return the email(s) as ready-to-send text — each with a subject line, greeting, body, and sign-off. When giving multiple options, label each briefly (`Option A — brief`, `Option B — warm`) and add a single line underneath explaining the key difference. Don't wrap the email in extra commentary; the email itself is the deliverable.
