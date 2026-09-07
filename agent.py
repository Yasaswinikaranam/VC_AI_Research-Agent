import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from tavily import TavilyClient


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

CLAUDE_MODEL = os.getenv(
    "CLAUDE_MODEL",
    "claude-sonnet-4-6"
)

if not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY is missing from your .env file."
    )

if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY is missing from your .env file."
    )


# ============================================================
# CLIENTS
# ============================================================

claude = Anthropic(
    api_key=ANTHROPIC_API_KEY
)

tavily = TavilyClient(
    api_key=TAVILY_API_KEY
)


# ============================================================
# TAVILY SEARCH
# ============================================================

def search_web(query, max_results=4):

    try:

        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=False
        )

        results = []

        for item in response.get("results", []):

            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", "")
            })

        return results

    except Exception as e:

        print(f"Search error for '{query}': {e}")

        return []


# ============================================================
# RESEARCH COMPANY
# ============================================================

def research_company(company):

    print("\n" + "=" * 80)
    print(f"RESEARCHING {company.upper()}...")
    print("=" * 80)

    queries = [

        f"{company} company overview product customers business model",

        f"{company} funding investors valuation revenue traction",

        f"{company} market size TAM SAM SOM industry",

        f"{company} competitors competitive landscape",

        f"{company} technology moat differentiation",

        f"{company} founders team background",

        f"{company} risks challenges competitors",

        f"{company} latest news 2026"

    ]

    all_sources = []

    for query in queries:

        print(f"\nSearching: {query}")

        results = search_web(
            query,
            max_results=4
        )

        for result in results:

            all_sources.append(result)

    # Remove duplicate URLs
    unique_sources = {}

    for source in all_sources:

        url = source.get("url", "")

        if url and url not in unique_sources:

            unique_sources[url] = source

    return list(unique_sources.values())


# ============================================================
# BUILD RESEARCH CONTEXT
# ============================================================

def build_context(sources):

    context = ""

    for i, source in enumerate(sources, start=1):

        context += f"""

SOURCE {i}

TITLE:
{source.get("title", "")}

URL:
{source.get("url", "")}

CONTENT:
{source.get("content", "")}

------------------------------------------------------------

"""

    return context


# ============================================================
# CLAUDE ANALYSIS
# ============================================================

def analyze_company(company, sources):

    research_context = build_context(sources)

    prompt = f"""
You are an experienced venture capital analyst.

Analyze the company: {company}

You have been provided with web research collected using a search API.

IMPORTANT RULES:

1. Use ONLY information supported by the provided research.
2. Do not invent revenue, valuation, funding, customer numbers,
   market sizes, or other facts.
3. If information is unavailable, explicitly say "Not available".
4. Clearly distinguish facts from estimates.
5. TAM/SAM/SOM may be estimates when exact numbers are unavailable,
   but clearly explain the methodology and assumptions.
6. Think like a VC analyst evaluating an investment opportunity.
7. Be concise but substantive.
8. Return ONLY valid JSON.
9. Do not use markdown.
10. Every important factual claim should reference a source number
    such as "Source 2".

Create the following JSON structure:

{{
    "company": "{company}",

    "company_overview": "",

    "target_customers": "",

    "business_model": "",

    "market": {{
        "description": "",
        "tam": {{
            "value": "",
            "methodology": "",
            "assumptions": ""
        }},
        "sam": {{
            "value": "",
            "methodology": "",
            "assumptions": ""
        }},
        "som": {{
            "value": "",
            "methodology": "",
            "assumptions": ""
        }}
    }},

    "competitors": [
        {{
            "name": "",
            "description": "",
            "strength": "",
            "weakness": ""
        }}
    ],

    "moat": "",

    "traction": "",

    "team": "",

    "risks": [
        ""
    ],

    "investment_thesis": "",

    "investment_score_inputs": {{
        "market": 0,
        "traction": 0,
        "moat": 0,
        "business_model": 0,
        "competition": 0,
        "team": 0,
        "risk": 0
    }},

    "key_sources": [
        {{
            "source_number": 0,
            "title": "",
            "url": ""
        }}
    ]
}}

SCORING RULES:

Give each factor a score from 0 to 10.

MARKET:
10 = enormous and rapidly growing market
5 = moderate opportunity
0 = very small or declining market

TRACTION:
10 = exceptional revenue/customer/growth evidence
5 = early but promising
0 = no meaningful evidence

MOAT:
10 = extremely difficult to replicate
5 = moderate differentiation
0 = commodity/easy to copy

BUSINESS MODEL:
10 = highly scalable, attractive economics
5 = reasonable model
0 = poor or unclear economics

COMPETITION:
10 = strong competitive position
5 = significant competition
0 = extremely crowded with weak differentiation

TEAM:
10 = exceptional founders/team with highly relevant experience
5 = credible team
0 = weak or unavailable information

RISK:
10 = LOW risk
5 = moderate risk
0 = extremely high risk

For RISK, remember that a HIGHER score means LOWER risk.

RESEARCH:

{research_context}
"""

    print("\nAnalyzing research with Claude...")

    response = claude.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=7000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    text = response.content[0].text.strip()

    # Remove accidental markdown fences
    if text.startswith("```"):

        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        print("\nClaude returned invalid JSON.")
        print(text)

        raise


# ============================================================
# VC INVESTMENT SCORE ENGINE
# ============================================================

def calculate_score(scores):

    weights = {

        "market": 0.20,

        "traction": 0.20,

        "moat": 0.15,

        "business_model": 0.10,

        "competition": 0.10,

        "team": 0.10,

        "risk": 0.15
    }

    weighted_components = {}

    total_score = 0

    for category, weight in weights.items():

        score = float(
            scores.get(category, 0)
        )

        # Keep score between 0 and 10
        score = max(
            0,
            min(score, 10)
        )

        contribution = score * weight

        weighted_components[category] = {

            "score": score,

            "weight": weight,

            "contribution": contribution
        }

        total_score += contribution

    return (
        round(total_score, 2),
        weighted_components
    )


# ============================================================
# INVESTMENT RECOMMENDATION
# ============================================================

def determine_recommendation(score):

    if score >= 8.0:

        return "INVEST"

    elif score >= 6.5:

        return "CONSIDER"

    else:

        return "PASS"


# ============================================================
# DISPLAY MARKET ANALYSIS
# ============================================================

def display_market_analysis(market):

    print("\n\n")
    print("=" * 80)
    print("3. MARKET ANALYSIS")
    print("=" * 80)

    print("\nMARKET:")
    print(market.get("description", "Not available"))

    # -------------------------
    # TAM
    # -------------------------

    tam = market.get("tam", {})

    print("\nTAM — TOTAL ADDRESSABLE MARKET")
    print("-" * 50)

    print(
        f"Value: {tam.get('value', 'Not available')}"
    )

    print(
        f"Methodology: {tam.get('methodology', 'Not available')}"
    )

    print(
        f"Assumptions: {tam.get('assumptions', 'Not available')}"
    )

    # -------------------------
    # SAM
    # -------------------------

    sam = market.get("sam", {})

    print("\nSAM — SERVICEABLE ADDRESSABLE MARKET")
    print("-" * 50)

    print(
        f"Value: {sam.get('value', 'Not available')}"
    )

    print(
        f"Methodology: {sam.get('methodology', 'Not available')}"
    )

    print(
        f"Assumptions: {sam.get('assumptions', 'Not available')}"
    )

    # -------------------------
    # SOM
    # -------------------------

    som = market.get("som", {})

    print("\nSOM — SERVICEABLE OBTAINABLE MARKET")
    print("-" * 50)

    print(
        f"Value: {som.get('value', 'Not available')}"
    )

    print(
        f"Methodology: {som.get('methodology', 'Not available')}"
    )

    print(
        f"Assumptions: {som.get('assumptions', 'Not available')}"
    )


# ============================================================
# DISPLAY COMPETITORS
# ============================================================

def display_competitors(competitors):

    print("\n\n")
    print("=" * 80)
    print("4. COMPETITIVE LANDSCAPE")
    print("=" * 80)

    if not competitors:

        print("No competitor information available.")

        return

    for i, competitor in enumerate(
        competitors,
        start=1
    ):

        print(
            f"\n{i}. {competitor.get('name', 'Unknown')}"
        )

        print(
            f"Description: "
            f"{competitor.get('description', 'Not available')}"
        )

        print(
            f"Strength: "
            f"{competitor.get('strength', 'Not available')}"
        )

        print(
            f"Weakness: "
            f"{competitor.get('weakness', 'Not available')}"
        )


# ============================================================
# DISPLAY INVESTMENT SCORE
# ============================================================

def display_scorecard(scores):

    weighted_score, weighted_components = calculate_score(
        scores
    )

    recommendation = determine_recommendation(
        weighted_score
    )

    print("\n\n")
    print("=" * 80)
    print("10. INVESTMENT SCORECARD")
    print("=" * 80)

    print(
        f"{'Factor':<22}"
        f"{'Score':<10}"
        f"{'Weight':<10}"
        f"{'Contribution':<15}"
    )

    print("-" * 80)

    labels = {

        "market": "Market",

        "traction": "Traction",

        "moat": "Moat",

        "business_model": "Business Model",

        "competition": "Competition",

        "team": "Team",

        "risk": "Risk"
    }

    for category, label in labels.items():

        component = weighted_components[
            category
        ]

        print(
            f"{label:<22}"
            f"{component['score']:<10.1f}"
            f"{component['weight'] * 100:<10.0f}%"
            f"{component['contribution']:<15.2f}"
        )

    print("-" * 80)

    print(
        f"\nWEIGHTED INVESTMENT SCORE: "
        f"{weighted_score}/10"
    )

    print(
        f"RECOMMENDATION: "
        f"{recommendation}"
    )

    print("=" * 80)

    return weighted_score, recommendation


# ============================================================
# DISPLAY SOURCES
# ============================================================

def display_sources(sources):

    print("\n\n")
    print("=" * 80)
    print("11. KEY SOURCES")
    print("=" * 80)

    if not sources:

        print("No sources found.")

        return

    for i, source in enumerate(
        sources,
        start=1
    ):

        print(
            f"\n[{i}] "
            f"{source.get('title', 'Untitled')}"
        )

        print(
            source.get("url", "")
        )


# ============================================================
# DISPLAY COMPLETE VC MEMO
# ============================================================

def display_memo(result, sources):

    company = result.get(
        "company",
        "Unknown"
    )

    print("\n\n")
    print("=" * 80)
    print(f"VC INVESTMENT MEMO — {company.upper()}")
    print("=" * 80)

    # --------------------------------------------------------
    # COMPANY OVERVIEW
    # --------------------------------------------------------

    print("\n1. COMPANY OVERVIEW")
    print("-" * 80)

    print(
        result.get(
            "company_overview",
            "Not available"
        )
    )

    # --------------------------------------------------------
    # CUSTOMERS
    # --------------------------------------------------------

    print("\n2. TARGET CUSTOMERS")
    print("-" * 80)

    print(
        result.get(
            "target_customers",
            "Not available"
        )
    )

    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    display_market_analysis(
        result.get(
            "market",
            {}
        )
    )

    # --------------------------------------------------------
    # BUSINESS MODEL
    # --------------------------------------------------------

    print("\n\n5. BUSINESS MODEL")
    print("-" * 80)

    print(
        result.get(
            "business_model",
            "Not available"
        )
    )

    # --------------------------------------------------------
    # MOAT
    # --------------------------------------------------------

    print("\n\n6. MOAT / COMPETITIVE ADVANTAGE")
    print("-" * 80)

    print(
        result.get(
            "moat",
            "Not available"
        )
    )

    # --------------------------------------------------------
    # TRACTION
    # --------------------------------------------------------

    print("\n\n7. TRACTION")
    print("-" * 80)

    print(
        result.get(
            "traction",
            "Not available"
        )
    )

    # --------------------------------------------------------
    # TEAM
    # --------------------------------------------------------

    print("\n\n8. TEAM")
    print("-" * 80)

    print(
        result.get(
            "team",
            "Not available"
        )
    )

    # --------------------------------------------------------
    # RISKS
    # --------------------------------------------------------

    print("\n\n9. KEY RISKS")
    print("-" * 80)

    risks = result.get(
        "risks",
        []
    )

    if risks:

        for i, risk in enumerate(
            risks,
            start=1
        ):

            print(
                f"{i}. {risk}"
            )

    else:

        print("No risks identified.")

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    scores = result.get(
        "investment_score_inputs",
        {}
    )

    weighted_score, recommendation = display_scorecard(
        scores
    )

    # --------------------------------------------------------
    # INVESTMENT THESIS
    # --------------------------------------------------------

    print("\n\n12. INVESTMENT THESIS")
    print("=" * 80)

    print(
        result.get(
            "investment_thesis",
            "Not available"
        )
    )

    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    display_sources(
        sources
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print("\n\n")
    print("=" * 80)
    print("END OF VC MEMO")
    print("=" * 80)

    return weighted_score, recommendation


# ============================================================
# SAVE REPORT
# ============================================================

def save_report(result, sources):

    company = result.get(
        "company",
        "company"
    )

    scores = result.get(
        "investment_score_inputs",
        {}
    )

    weighted_score, recommendation = calculate_score(
        scores
    )

    filename = (
        company.lower()
        .replace(" ", "_")
        .replace("/", "_")
        + "_investment_memo.txt"
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            f"VC INVESTMENT MEMO — {company}\n"
        )

        file.write("=" * 80 + "\n\n")

        file.write(
            "COMPANY OVERVIEW\n"
        )

        file.write(
            result.get(
                "company_overview",
                "Not available"
            )
            + "\n\n"
        )

        file.write(
            "TARGET CUSTOMERS\n"
        )

        file.write(
            result.get(
                "target_customers",
                "Not available"
            )
            + "\n\n"
        )

        file.write(
            "BUSINESS MODEL\n"
        )

        file.write(
            result.get(
                "business_model",
                "Not available"
            )
            + "\n\n"
        )

        file.write(
            "MARKET\n"
        )

        market = result.get(
            "market",
            {}
        )

        file.write(
            str(market)
            + "\n\n"
        )

        file.write(
            "COMPETITORS\n"
        )

        file.write(
            str(
                result.get(
                    "competitors",
                    []
                )
            )
            + "\n\n"
        )

        file.write(
            "MOAT\n"
        )

        file.write(
            result.get(
                "moat",
                "Not available"
            )
            + "\n\n"
        )

        file.write(
            "TRACTION\n"
        )

        file.write(
            result.get(
                "traction",
                "Not available"
            )
            + "\n\n"
        )

        file.write(
            "TEAM\n"
        )

        file.write(
            result.get(
                "team",
                "Not available"
            )
            + "\n\n"
        )

        file.write(
            "RISKS\n"
        )

        for risk in result.get(
            "risks",
            []
        ):

            file.write(
                f"- {risk}\n"
            )

        file.write("\n")

        file.write(
            "INVESTMENT THESIS\n"
        )

        file.write(
            result.get(
                "investment_thesis",
                "Not available"
            )
            + "\n\n"
        )

        file.write(
            "INVESTMENT SCORE\n"
        )

        file.write(
            f"{weighted_score}/10\n"
        )

        file.write(
            f"RECOMMENDATION: "
            f"{recommendation}\n\n"
        )

        file.write(
            "SOURCES\n"
        )

        for i, source in enumerate(
            sources,
            start=1
        ):

            file.write(
                f"{i}. "
                f"{source.get('title', '')}\n"
            )

            file.write(
                f"{source.get('url', '')}\n\n"
            )

    print(
        f"\nReport saved as: {filename}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 80)
    print("VC AI RESEARCH AGENT")
    print("=" * 80)

    company = input(
        "\nEnter company name: "
    ).strip()

    if not company:

        print(
            "Please enter a company name."
        )

        return

    # --------------------------------------------------------
    # STEP 1 — WEB RESEARCH
    # --------------------------------------------------------

    sources = research_company(
        company
    )

    print(
        f"\nCollected {len(sources)} unique sources."
    )

    if not sources:

        print(
            "\nNo web research was found."
        )

        return

    # --------------------------------------------------------
    # STEP 2 — CLAUDE ANALYSIS
    # --------------------------------------------------------

    result = analyze_company(
        company,
        sources
    )

    # --------------------------------------------------------
    # STEP 3 — DISPLAY MEMO
    # --------------------------------------------------------

    display_memo(
        result,
        sources
    )

    # --------------------------------------------------------
    # STEP 4 — SAVE REPORT
    # --------------------------------------------------------

    save_report(
        result,
        sources
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()