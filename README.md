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
