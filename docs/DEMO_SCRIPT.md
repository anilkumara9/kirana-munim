# Demo script and storyboard (matches kirana-munim-demo-v2.mp4, about 2:05)
Layout: app recorded at phone width (405x720) on the right, large captions on the left. Three generated voices: narrator Yashraj, test speech Shubham, app replies Shivani. Disclosed in the video.
1. Opener: Kirana Munim, built on Gnani Prisma and Timbre.
2. Narration: udhaar by voice in Hindi, Kannada or English. Disclosure that every voice is generated.
3. Hindi test speech "Ramesh ko 200 rupaye udhaar": orb records, Prisma transcript, staged review, Timbre reads it back, nothing saved until confirmed. Save.
4. Server restart: ledger still shows Rs 200. Tap the customer: statement with running balance and copy-only reminder.
5. Kannada test speech (Ramesh paid 200): the name comes back in Kannada script, the app suggests the existing customer, Save is blocked until the shopkeeper picks it. Balance after payment is shown. Save: balance Rs 0, statement.
6. Typed tests (no Gnani call): unclear entry blocks Save; payment above the balance is refused.
7. What is real, and what is not tested yet (real voices, noisy shops, physical microphones).
Recorded live by tests/record_demo.py against the real app with real Gnani calls; mixed by tests/mux_demo.py.
