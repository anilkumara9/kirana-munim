# Kirana Munim - voice udhaar ledger for neighbourhood shops

**Problem.** Neighbourhood shops in India keep udhaar (credit) on paper or in memory. Owners are busy, hands are full, and many are more at ease speaking Hindi or Kannada than typing in an app.

**What it does.** The shopkeeper holds a button and says one sentence, for example "Ramesh ko 200 rupaye udhaar". The app turns the speech into a proposed entry (customer, amount, credit or payment) and shows it for review. Nothing is saved until the shopkeeper confirms. Then the entry is written to a local ledger in whole paise, and the app shows who owes what. Unclear entries block Save, and a payment larger than the balance is refused. If a spoken name sounds like an existing customer in another script (for example Ramesh and रमेश), the app suggests that account, shows the balance before and after, and blocks Save until the shopkeeper picks it or chooses New customer. Tapping a customer shows a statement with a running balance and a reminder text to copy (never sent automatically).

**Gnani models used.** **Prisma v3.0** (speech to text, with a Kannada/Hindi/English language hint) transcribes the entry. **Timbre v3.0** (text to speech) reads the proposed entry back aloud for review. The entry parser is rule-based code in the repo; no other AI model is used.

**Who it is for.** Small shop owners who want a hands-free ledger in their own language. Categories: Mixed Vibes (code-mixed Hindi, Kannada, English) and Real Deal (a real everyday need).

**Tested so far (Nov 12, 2026).** Real Gnani calls with computer-generated test speech: Hindi credit, Kannada payment with the existing-customer suggestion, spoken reply, save, restart persistence and settling a balance, all in a recorded demo (about 2 min). Name matching is a coarse rule-based sound key, not general transliteration. Local automated tests cover the parser, UI, microphone path, cancel behaviour and the usage guard. Honest limits: no real human voices, physical microphones or noisy shops tested yet; Prisma can mis-hear number words, which is why review comes first. Local single-user demo, not a deployed product.

**Contribution.** Project prepared for Anil Kumara (2026 graduate, New Horizon College of Engineering). The code, demo and documents were produced with an AI assistant. The speech models in the app are Gnani's Prisma (speech to text) and Timbre (text to speech); no other AI model runs inside the app.
