import streamlit as st
from agent import (
    research_company,
    analyze_company,
    calculate_score,
    determine_recommendation,
)

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------

st.set_page_config(
    page_title="VC AI Research Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# CUSTOM CSS
# ------------------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        .hero {
            padding: 1.5rem 0 1rem 0;
        }

        .hero h1 {
            font-size: 2.4rem;
            margin-bottom: 0.25rem;
        }

        .hero p {
            font-size: 1.05rem;
            opacity: 0.75;
        }

        .score-card {
            padding: 1.25rem;
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 14px;
            text-align: center;
            min-height: 145px;
        }

        .score-number {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0.25rem 0;
        }

        .score-label {
            font-size: 0.85rem;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .recommendation {
            font-size: 1.35rem;
            font-weight: 700;
            margin-top: 0.4rem;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 700;
            margin-top: 1.25rem;
            margin-bottom: 0.75rem;
        }

        .metric-box {
            padding: 1rem;
            border: 1px solid rgba(128,128,128,0.22);
            border-radius: 12px;
            min-height: 125px;
        }

        .metric-name {
            font-size: 0.8rem;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-value {
            font-size: 1.45rem;
            font-weight: 700;
            margin: 0.35rem 0;
        }

        .small-note {
            font-size: 0.82rem;
            opacity: 0.7;
        }

        div[data-testid="stExpander"] {
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def safe_text(value):
    if value is None or value == "":
        return "Not available"
    return str(value)


def render_market_metric(label, market_data):
    value = safe_text(market_data.get("value", "Not available"))
    methodology = safe_text(market_data.get("methodology", "Not available"))
    assumptions = safe_text(market_data.get("assumptions", "Not available"))

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-name">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"{label} methodology & assumptions"):
        st.write("**Methodology:**", methodology)
        st.write("**Assumptions:**", assumptions)


def build_download_text(result, sources, score, recommendation):
    company = safe_text(result.get("company", "Company"))
    market = result.get("market", {}) or {}
    scores = result.get("investment_score_inputs", {}) or {}

    lines = [
        f"VC INVESTMENT MEMO — {company}",
        "=" * 70,
        "",
        "COMPANY OVERVIEW",
        safe_text(result.get("company_overview")),
        "",
        "TARGET CUSTOMERS",
        safe_text(result.get("target_customers")),
        "",
        "MARKET",
        safe_text(market.get("description")),
        "",
        f"TAM: {safe_text((market.get('tam') or {}).get('value'))}",
        f"SAM: {safe_text((market.get('sam') or {}).get('value'))}",
        f"SOM: {safe_text((market.get('som') or {}).get('value'))}",
        "",
        "BUSINESS MODEL",
        safe_text(result.get("business_model")),
        "",
        "COMPETITORS",
    ]

    for i, competitor in enumerate(result.get("competitors", []) or [], 1):
        lines.extend([
            f"{i}. {safe_text(competitor.get('name'))}",
            f"   Description: {safe_text(competitor.get('description'))}",
            f"   Strength: {safe_text(competitor.get('strength'))}",
            f"   Weakness: {safe_text(competitor.get('weakness'))}",
            "",
        ])

    lines.extend([
        "MOAT / COMPETITIVE ADVANTAGE",
        safe_text(result.get("moat")),
        "",
        "TRACTION",
        safe_text(result.get("traction")),
        "",
        "TEAM",
        safe_text(result.get("team")),
        "",
        "KEY RISKS",
    ])

    for risk in result.get("risks", []) or []:
        lines.append(f"- {safe_text(risk)}")

    lines.extend([
        "",
        "INVESTMENT THESIS",
        safe_text(result.get("investment_thesis")),
        "",
        "INVESTMENT SCORECARD",
    ])

    weights = {
        "market": 0.20,
        "traction": 0.20,
        "moat": 0.15,
        "business_model": 0.10,
        "competition": 0.10,
        "team": 0.10,
        "risk": 0.15,
    }

    for category, weight in weights.items():
        value = float(scores.get(category, 0))
        lines.append(f"{category.replace('_', ' ').title()}: {value:.1f}/10 ({weight:.0%})")

    lines.extend([
        "",
        f"WEIGHTED INVESTMENT SCORE: {score}/10",
        f"RECOMMENDATION: {recommendation}",
        "",
        "SOURCES",
    ])

    for i, source in enumerate(sources, 1):
        lines.extend([
            f"[{i}] {safe_text(source.get('title'))}",
            safe_text(source.get("url")),
            "",
        ])

    return "\n".join(lines)


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------

with st.sidebar:
    st.markdown("## 📊 VC AI Research Agent")
    st.caption("AI-powered company research and investment analysis")

    st.divider()

    st.markdown("### What it analyzes")
    st.markdown(
        """
        - Company overview
        - Target customers
        - Business model
        - TAM / SAM / SOM
        - Competitors
        - Competitive moat
        - Traction
        - Team
        - Key risks
        - Investment thesis
        - Weighted investment score
        """
    )

    st.divider()

    st.markdown("### Pipeline")
    st.caption("Tavily → Research → Claude → VC Analysis")

    st.info(
        "The web research is performed with Tavily and the final investment "
        "analysis is generated by Claude."
    )

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>VC AI RESEARCH AGENT</h1>
        <p>Research a company and generate an AI-powered venture capital investment memo.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# COMPANY INPUT
# ------------------------------------------------------------

company = st.text_input(
    "Company",
    placeholder="Enter a company name — e.g. Figma, Stripe, Databricks",
)

analyze_clicked = st.button(
    "🔍 Analyze Company",
    type="primary",
    use_container_width=True,
)

# ------------------------------------------------------------
# ANALYSIS
# ------------------------------------------------------------

if analyze_clicked:
    if not company.strip():
        st.warning("Please enter a company name.")
        st.stop()

    company = company.strip()

    try:
        with st.status("Researching company...", expanded=True) as status:
            st.write("Searching company overview, products and customers...")
            sources = research_company(company)

            if not sources:
                status.update(
                    label="No research results found",
                    state="error",
                )
                st.error("No web research was found for this company.")
                st.stop()

            st.write(f"Collected {len(sources)} unique sources.")
            st.write("Sending research to Claude for investment analysis...")

            result = analyze_company(company, sources)

            status.update(
                label="Analysis complete",
                state="complete",
            )

        # Calculate deterministic score in Python using the scores
        # returned by Claude.
        score_inputs = result.get("investment_score_inputs", {}) or {}
        weighted_score, weighted_components = calculate_score(score_inputs)
        recommendation = determine_recommendation(weighted_score)

        # Store everything in session state so it remains visible
        # across Streamlit reruns.
        st.session_state["analysis"] = result
        st.session_state["sources"] = sources
        st.session_state["score"] = weighted_score
        st.session_state["recommendation"] = recommendation
        st.session_state["components"] = weighted_components

    except Exception as e:
        st.error("The analysis failed.")
        st.exception(e)

# ------------------------------------------------------------
# DISPLAY STORED RESULT
# ------------------------------------------------------------

if "analysis" in st.session_state:
    result = st.session_state["analysis"]
    sources = st.session_state["sources"]
    score = st.session_state["score"]
    recommendation = st.session_state["recommendation"]
    components = st.session_state["components"]

    company_name = safe_text(result.get("company", company))

    st.divider()

    st.markdown(f"## {company_name}")

    # --------------------------------------------------------
    # TOP SCORE CARDS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="score-card">
                <div class="score-label">Investment Score</div>
                <div class="score-number">{score}/10</div>
                <div class="small-note">Weighted VC score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="score-card">
                <div class="score-label">Recommendation</div>
                <div class="recommendation">{recommendation}</div>
                <div class="small-note">Based on weighted score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="score-card">
                <div class="score-label">Sources</div>
                <div class="score-number">{len(sources)}</div>
                <div class="small-note">Unique research sources</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # --------------------------------------------------------
    # MARKET SIZE
    # --------------------------------------------------------

    st.markdown('<div class="section-title">Market Size</div>', unsafe_allow_html=True)

    market = result.get("market", {}) or {}

    st.write(safe_text(market.get("description")))

    tam_col, sam_col, som_col = st.columns(3)

    with tam_col:
        render_market_metric("TAM", market.get("tam", {}) or {})

    with sam_col:
        render_market_metric("SAM", market.get("sam", {}) or {})

    with som_col:
        render_market_metric("SOM", market.get("som", {}) or {})

    # --------------------------------------------------------
    # COMPANY OVERVIEW + CUSTOMERS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            '<div class="section-title">Company Overview</div>',
            unsafe_allow_html=True,
        )
        st.write(safe_text(result.get("company_overview")))

    with col2:
        st.markdown(
            '<div class="section-title">Target Customers</div>',
            unsafe_allow_html=True,
        )
        st.write(safe_text(result.get("target_customers")))

    # --------------------------------------------------------
    # BUSINESS MODEL + MOAT
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            '<div class="section-title">Business Model</div>',
            unsafe_allow_html=True,
        )
        st.write(safe_text(result.get("business_model")))

    with col2:
        st.markdown(
            '<div class="section-title">Moat / Competitive Advantage</div>',
            unsafe_allow_html=True,
        )
        st.write(safe_text(result.get("moat")))

    # --------------------------------------------------------
    # COMPETITORS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Competitive Landscape</div>',
        unsafe_allow_html=True,
    )

    competitors = result.get("competitors", []) or []

    if competitors:
        for competitor in competitors:
            with st.expander(safe_text(competitor.get("name", "Competitor"))):
                c1, c2 = st.columns(2)

                with c1:
                    st.write("**Description**")
                    st.write(safe_text(competitor.get("description")))

                    st.write("**Strength**")
                    st.write(safe_text(competitor.get("strength")))

                with c2:
                    st.write("**Weakness**")
                    st.write(safe_text(competitor.get("weakness")))
    else:
        st.info("No competitor information available.")

    # --------------------------------------------------------
    # TRACTION + TEAM
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            '<div class="section-title">Traction</div>',
            unsafe_allow_html=True,
        )
        st.write(safe_text(result.get("traction")))

    with col2:
        st.markdown(
            '<div class="section-title">Team</div>',
            unsafe_allow_html=True,
        )
        st.write(safe_text(result.get("team")))

    # --------------------------------------------------------
    # RISKS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Key Risks</div>',
        unsafe_allow_html=True,
    )

    risks = result.get("risks", []) or []

    if risks:
        for risk in risks:
            st.warning(safe_text(risk))
    else:
        st.info("No major risks identified in the available research.")

    # --------------------------------------------------------
    # SCORECARD
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Investment Scorecard</div>',
        unsafe_allow_html=True,
    )

    score_labels = {
        "market": "Market",
        "traction": "Traction",
        "moat": "Moat",
        "business_model": "Business Model",
        "competition": "Competition",
        "team": "Team",
        "risk": "Risk",
    }

    for category, label in score_labels.items():
        component = components.get(category, {})
        category_score = component.get("score", 0)
        weight = component.get("weight", 0)
        contribution = component.get("contribution", 0)

        col1, col2, col3 = st.columns([2.5, 4, 1.5])

        with col1:
            st.write(f"**{label}**")

        with col2:
            st.progress(float(category_score) / 10)

        with col3:
            st.write(f"**{category_score:.1f}/10**")
            st.caption(f"{weight:.0%} weight")

    # --------------------------------------------------------
    # INVESTMENT THESIS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Investment Thesis</div>',
        unsafe_allow_html=True,
    )

    st.info(safe_text(result.get("investment_thesis")))

    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Research Sources</div>',
        unsafe_allow_html=True,
    )

    for i, source in enumerate(sources, 1):
        title = safe_text(source.get("title", "Untitled source"))
        url = safe_text(source.get("url", ""))

        st.markdown(f"**[{i}] {title}**")
        if url != "Not available":
            st.markdown(f"[Open source]({url})")

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    report_text = build_download_text(
        result,
        sources,
        score,
        recommendation,
    )

    st.divider()

    st.download_button(
        label="⬇️ Download Investment Memo",
        data=report_text,
        file_name=f"{company_name.lower().replace(' ', '_')}_investment_memo.txt",
        mime="text/plain",
        use_container_width=True,
    )

else:
    # Landing page when no analysis has been run yet.
    st.divider()

    st.markdown("### How it works")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 1️⃣ Research")
        st.write(
            "Tavily performs targeted web research across company, market, "
            "competition, traction, team and risk topics."
        )

    with c2:
        st.markdown("### 2️⃣ Analyze")
        st.write(
            "Claude synthesizes the research into a structured VC investment "
            "analysis with TAM/SAM/SOM and scoring inputs."
        )

    with c3:
        st.markdown("### 3️⃣ Decide")
        st.write(
            "A deterministic Python scoring engine calculates the weighted "
            "investment score and recommendation."
        )

    st.info("Enter a company above to start your first investment analysis.")
