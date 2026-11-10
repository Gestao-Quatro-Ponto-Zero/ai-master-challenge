# 01c: research (sub-agent)

You are a research sub-agent in Daniel's G4 "AI Master" practical test (challenge 003, Lead Scorer).
I am the lead builder: I integrate and commit. You write ONE file and NEVER run git.
Time box: 20 minutes. At 20, stop and write what you have, marking what is missing.

## What this is for
We are building a pipeline-prioritisation tool for a non-technical B2B seller who opens it on
Monday morning. Two pains: time lost on deals that will not close, and good deals left to cool.
The tool orders each seller's OPEN deals, puts them in three groups (focar agora, manter aquecido,
deixar ir), explains each position with the deal's real factors, and picks a next step by rule;
a language model only words the explanation. The scoring will be transparent rules unless a
model provably ranks better. The CRM export is thin: per opportunity it has only the seller,
the product (with a list price), the account (sector, revenue, employees, country, parent), the
stage (Prospecting, Engaging, Won, Lost), the date the Engaging stage began, and the close date
and close value. There is NO activity log, no e-mails, no contact data, no stage history.

Your research changes three decisions. Answer only what changes them.

1. How are open deals ranked in practice? Expected value (chance times value), calibration of
   the chance, time decay or deal ageing ("stalled deal" rules relative to the usual sales cycle).
   What is the accepted way to turn "this deal is older than deals like it usually take" into
   a score a seller trusts? What do practitioners warn against (for example ranking by value
   alone, uncalibrated scores, black boxes sellers ignore)?
2. How are generated explanations kept grounded in the record? Techniques that keep a language
   model from stating a figure or a name that is not in the facts: templates or placeholders
   filled by code, structured output, citation of facts, post-generation checks. What is known
   to fail?
3. What does a seller see on the FIRST screen of current sales-prioritisation tools (for example
   Salesforce Einstein opportunity scoring and Pipeline Inspection, HubSpot deal score and
   prioritised task views, Gong or Clari deal boards, Pipedrive "rotting" deals)? What is the
   pattern that works: how many items, what is shown per item (score, top reasons, next step),
   how "at risk" or "going cold" is signalled, how "let go" is handled. We want the interface to
   start from a pattern that works and not from a table.

## Rules
- Primary sources first: vendor documentation, peer-reviewed or well-known practitioner papers,
  official product pages. Every claim carries its source: title, publisher, URL, the date of
  publication or last update when the page shows one, and the access date (run `date`).
  A claim you could not open and read yourself is marked "nao verificado" or left out.
- Do NOT read anything about this specific G4 challenge, its repository, its pull requests or
  other candidates' solutions, and do not research the dataset itself. Findings about the data
  come only from our own audit.
- Do not read anything on this machine outside the file you write.

## What to write (only this file)
`ai-master-challenge/submissions/daniel-resende/docs/pesquisa.md`
in Portuguese, at most two pages:
- one section per question: the findings (each with its source inline), then "O que isso muda
  no desenho" in two or three lines;
- a final list "Fontes" (title, publisher, URL, date of the source, date of access);
- a line at the top with the real start and end times from `date`.

## What to send back to me (final message, under 300 words)
For each question, the one or two findings that should change the design, with the source name.
Say what you could not verify.
