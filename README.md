# Job Application Research Agent

An agent that turns a job posting and a company name into a one-page interview prep brief.

## How it works
1. **Fetch** the posting (URL, or a text file if the site needs JavaScript).
2. **Extract** must-haves, nice-to-haves and responsibilities as structured JSON.
3. **Research** the company using a web search tool (recent news, priorities).
4. **Draft** a brief that maps each requirement to a talking point.
5. **Self-check**: a second model call reviews the draft for uncovered requirements and unsupported claims, and the agent revises up to 2 times.

## Run it
```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key
python agent.py --company "Acme" --url "https://example.com/jobs/123"
```
Output goes to `briefs/<company>.md`.

## Add before publishing
- A sample brief for one real company in `examples/`
- A short note on what the self-check caught and where the agent still gets things wrong
# Job-Research-Agent

## What I learned

**The first version missed the most important topic.** I tested the agent on a Bank of America Digital Assets analyst posting. The first brief covered the company's earnings but contained no news about stablecoins or tokenization, which is the core of the role. The cause was in my code: the research step received only the company name, so it never searched for anything related to the job.

**Fixing it took three iterations.**
1. I passed the role title into the research step. The brief improved, picking up a Global Payments product announcement, but still had no digital-asset news.
2. I added a second, role-specific search. It still returned nothing on stablecoins, even though a manual search showed such news existed.
3. I saved the raw research to `briefs/last-research.md` so I could see what the search returned, then rewrote the prompt to use specific search terms (for example "company + stablecoin" and "company + tokenization"). The final brief included the stablecoin, tokenized deposit and digital-asset leadership news.

Seeing the intermediate output was what made the problem fixable. Before I saved it, I could only guess why the agent was missing things.

**The output still needs human review.**
- Facts varied between runs. The same event appeared with different dates, and one run reported a "17% fall" that another run attached to a different metric.
- The final draft dropped a caveat from the research stage (that no primary Bank of America source was found for the 2026 items), which made some claims sound more certain than the evidence supports.
- The draft also dropped the earnings and anti-money-laundering item that was useful for the role's risk and governance side.
- Many of the digital-asset items come from secondary sources and should be verified against primary sources before use.

**Next improvements:** attach a source link to each claim, carry confidence labels from research through to the final brief, and add an automated check that flags claims with no source.

Sample outputs are in `examples/`: `after.md` (final brief) and `research-after.md` (raw research).
