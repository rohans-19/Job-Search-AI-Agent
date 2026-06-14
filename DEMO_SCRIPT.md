# 🎬 Demo Video Script — Job Search AI Agent (5–7 minutes)

A scene-by-scene script for recording the final demo. Each scene has an on-screen
action and a suggested voice-over. Total runtime ≈ 6 minutes.

> Recording tip: use OBS / Loom at 1080p. Have your `.env` keys set and run
> `streamlit run app.py` before you start so live jobs load instantly.

---

## Scene 0 — Title (0:00–0:20)
**Show:** Title card → "Job Search AI Agent · A 9-Agent Career Assistant for the Indian Job Market".
**Say:** "Hi — this is Job Search AI, an AI career assistant that finds real, live jobs,
matches them to your résumé, and helps you manage your entire job hunt. It's built on a
nine-agent pipeline and tuned for the Indian market — salaries in LPA, Indian cities,
and culture insights."

## Scene 1 — The Architecture (0:20–1:00)
**Show:** README mermaid diagram of the 9-agent pipeline.
**Say:** "Behind the UI, nine specialized agents run in sequence — parsing your résumé,
extracting skills, discovering jobs from Adzuna and Jooble, then scoring each role on
location, salary, work preference, and company culture before a recommendation agent
re-ranks everything and writes career advice."

## Scene 2 — Search + Résumé Upload (1:00–2:15)
**Show:** The dashboard. Upload a PDF résumé → detected skill chips appear.
Enter role "Data Scientist", city "Bangalore", salary 15 LPA, Remote, click **Search Jobs**.
**Say:** "I'll upload my résumé — instantly it detects my skills as chips. Then I set my
target role, city, expected salary in LPA, and work mode. One click runs the full pipeline."
**Show:** Spinner → results, the stats strip, and job cards with matched-skill badges + culture insights.

## Scene 3 — Filters, Sorting & Export (2:15–3:15)
**Show:** Use the **Sort by** dropdown (Salary high→low), filter by **Source**, toggle
"Only with salary info", raise **Min rec score**. Open the **Table View** tab, then the
**Export** tab → download **PDF report** and **CSV**.
**Say:** "Results are fully interactive — sort by recommendation score or salary, filter by
source or score, and switch to a table view. Then export a polished PDF report or CSV to
share or keep." Open the downloaded PDF on screen.

## Scene 4 — Résumé Analysis (3:15–4:10)
**Show:** Go to **📄 Resume Analysis**. Show skills-by-category, type "Machine Learning
Engineer" → role-fit % bar, "you have / consider strengthening", suggestions. Download the
**Skills-Profile PDF**.
**Say:** "The Résumé Analysis page breaks my skills into categories and scores how well I
fit a target role — showing exactly what I'm missing — then exports a tailored one-page
skills profile."

## Scene 5 — Company Research (4:10–4:50)
**Show:** Go to **🏢 Company Research**, search "Infosys" → culture score tiles + summary + links.
**Say:** "Before applying, I research the company — work-life balance, growth, salary
competitiveness, remote-friendliness — plus authoritative links, cached locally for speed."

## Scene 6 — Application Tracker (4:50–5:40)
**Show:** Back on the dashboard, click **Track** on a job (set status Applied). Go to
**📋 Application Tracker** → Kanban columns. Move a card from Applied → Interview, delete one,
export the tracker.
**Say:** "Every job I save becomes a card in the tracker. I move applications through Saved,
Applied, Interview, Offer, or Rejected, and export the whole board anytime."

## Scene 7 — Analytics + Close (5:40–6:20)
**Show:** Go to **📊 Analytics** → funnel, most-searched roles/cities, salary distribution,
connector reliability.
**Say:** "Finally, the Analytics dashboard turns my activity into insight — my application
funnel, conversion rate, salary spread, and which job sources are most reliable. Everything
runs locally and deploys to Render in minutes. Thanks for watching!"

---

## Shot checklist
- [ ] `.env` keys set; app pre-loaded
- [ ] A sample PDF résumé ready
- [ ] Downloads folder visible for showing exported PDF/CSV
- [ ] At least one tracked job already saved (so the tracker isn't empty)
- [ ] Run a few searches beforehand so Analytics has data
