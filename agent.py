"""Job Application Research Agent.

Steps: fetch posting -> extract requirements -> research company (web search)
-> role-specific research -> draft brief -> self-check -> revise -> save.
Usage:
  export ANTHROPIC_API_KEY=...
  python agent.py --company "Acme" --url "https://..."
  python agent.py --company "Acme" --posting-file posting.txt
"""
import argparse, json, re
from pathlib import Path
import anthropic, requests
from bs4 import BeautifulSoup

MODEL = "claude-sonnet-5-5"
client = anthropic.Anthropic()
MAX_REVISIONS = 2


def log(step, msg=""):
    print(f"[{step}] {msg}")


def ask(prompt, tools=None, max_tokens=2000):
    kwargs = dict(model=MODEL, max_tokens=max_tokens,
                  messages=[{"role": "user", "content": prompt}])
    if tools:
        kwargs["tools"] = tools
    resp = client.messages.create(**kwargs)
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def parse_json(text):
    return json.loads(re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip())


def fetch_posting(url):
    html = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" "))[:12000]


def extract_requirements(posting):
    out = ask("Extract from this job posting. Reply with JSON only, keys: "
              "title, must_haves (list), nice_to_haves (list), responsibilities (list).\n\n" + posting)
    return parse_json(out)


def research_company(company, role_title):
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}]
    return ask(f"Research {company}. Summarize in under 250 words: what they do, "
               "recent news (last 6 months) with dates, and any announcements, products "
               f"or initiatives specifically relevant to the role '{role_title}'. "
               "Only state facts you found.",
               tools=tools, max_tokens=3000)


def research_topic(company, reqs):
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]
    focus = json.dumps({"title": reqs.get("title"), "nice_to_haves": reqs.get("nice_to_haves")})
    return ask(f"Search the web for {company} news related to this role: {focus}. "
               f"Try specific searches such as '{company} digital assets', "
               f"'{company} stablecoin', '{company} tokenization'. Summarize in under 200 words "
               "with dates and source names. Prefer primary sources and major outlets. "
               "If you find nothing, say so plainly.",
               tools=tools, max_tokens=3000)


def draft_brief(company, reqs, research, feedback=None, previous=None):
    prompt = (f"Write a one-page interview prep brief for a candidate applying to {company}.\n"
              f"Role requirements (JSON): {json.dumps(reqs)}\n\nCompany research:\n{research}\n\n"
              "Sections: Company snapshot, What the role needs, Recent news to mention, "
              "Talking points (map each must-have to something the candidate could discuss), "
              "Questions to ask. Markdown. Do not invent facts beyond the research.")
    if feedback:
        prompt += f"\n\nRevise this previous draft to fix these issues:\n{feedback}\n\nPrevious draft:\n{previous}"
    return ask(prompt, max_tokens=2500)


def check_brief(brief, reqs, research):
    out = ask("You are a strict reviewer. Check the brief against the requirements and research. "
              "Flag: must-haves not covered, claims not supported by the research. "
              'Reply with JSON only: {"ok": bool, "issues": [strings]}.\n\n'
              f"Requirements: {json.dumps(reqs)}\n\nResearch:\n{research}\n\nBrief:\n{brief}")
    return parse_json(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--company", required=True)
    p.add_argument("--url")
    p.add_argument("--posting-file")
    a = p.parse_args()

    log("1/5 fetch", a.url or a.posting_file)
    posting = fetch_posting(a.url) if a.url else Path(a.posting_file).read_text()
    log("2/5 extract")
    reqs = extract_requirements(posting)
    log("3/5 research", a.company)
    research = research_company(a.company, reqs.get("title", ""))
    research += "\n\nRole-specific research:\n" + research_topic(a.company, reqs)
    Path("briefs").mkdir(exist_ok=True)
    Path("briefs/last-research.md").write_text(research)
    log("3/5 research", "saved briefs/last-research.md")
    log("4/5 draft")
    brief = draft_brief(a.company, reqs, research)
    for i in range(MAX_REVISIONS):
        review = check_brief(brief, reqs, research)
        log("5/5 check", f"ok={review['ok']} issues={len(review['issues'])}")
        if review["ok"]:
            break
        brief = draft_brief(a.company, reqs, research, "\n".join(review["issues"]), brief)

    out = Path("briefs") / f"{re.sub(r'[^a-z0-9]+', '-', a.company.lower())}.md"
    out.write_text(brief)
    log("done", f"saved {out}")


if __name__ == "__main__":
    main()
