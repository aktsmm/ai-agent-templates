"""Custom tools for the content marketing agent."""

from crewai.tools import tool


@tool("search_content_guide")
def search_content_guide(query: str) -> str:
    """Search the content marketing guide for best practices and strategies.

    Use this tool to find relevant content marketing articles, templates,
    and guidelines based on the user's request.

    Args:
        query: The search query based on the user's content marketing need.

    Returns:
        Matching content guide sections and best practices.
    """
    from pathlib import Path

    knowledge_dir = Path(__file__).parent.parent / "knowledge"
    results: list[str] = []

    for file in knowledge_dir.glob("*.md"):
        content = file.read_text(encoding="utf-8")
        sections = content.split("\n### ")
        for section in sections:
            if query.lower() in section.lower():
                results.append(section.strip()[:800])

    if results:
        return "\n\n---\n\n".join(results[:10])
    return f"No content guide articles found for: {query}"


@tool("lookup_campaign")
def lookup_campaign(campaign_id: str) -> str:
    """Look up an existing content marketing campaign by campaign ID.

    Use this tool to check the current status and performance metrics
    of a content marketing campaign.

    Args:
        campaign_id: The campaign ID to look up (e.g., CMP-001).

    Returns:
        Campaign status and performance details.
    """
    sample_campaigns = {
        "CMP-001": {
            "name": "Q1 Product Launch Blog Series",
            "status": "Active",
            "type": "blog_writing",
            "start_date": "2026-01-15",
            "end_date": "2026-03-31",
            "posts_published": 6,
            "posts_planned": 12,
            "total_views": 24500,
            "avg_time_on_page": "4:32",
            "conversion_rate": "3.2%",
            "top_post": "10 Ways AI Transforms Customer Service",
            "notes": "Strong engagement on AI-focused posts. Consider doubling down.",
        },
        "CMP-002": {
            "name": "LinkedIn Thought Leadership",
            "status": "Active",
            "type": "social_media",
            "start_date": "2026-01-01",
            "end_date": "2026-06-30",
            "posts_published": 18,
            "posts_planned": 48,
            "total_impressions": 156000,
            "avg_engagement_rate": "4.8%",
            "followers_gained": 2340,
            "top_post": "Why B2B Brands Need a Content-First Strategy",
            "notes": "Carousel posts outperforming text-only by 3x.",
        },
        "CMP-003": {
            "name": "SEO Content Refresh",
            "status": "In Progress",
            "type": "seo_analysis",
            "start_date": "2026-02-01",
            "end_date": "2026-04-30",
            "pages_audited": 45,
            "pages_optimized": 12,
            "keywords_improved": 28,
            "avg_position_change": "+8.5 positions",
            "organic_traffic_lift": "+22%",
            "top_improvement": "'content marketing guide' moved from #18 to #5",
            "notes": "Focus on updating meta descriptions and adding internal links.",
        },
        "CMP-004": {
            "name": "Instagram Brand Awareness",
            "status": "Planned",
            "type": "social_media",
            "start_date": "2026-03-01",
            "end_date": "2026-05-31",
            "posts_published": 0,
            "posts_planned": 36,
            "target_reach": 500000,
            "target_followers": 5000,
            "budget": "$3,000/month",
            "content_themes": "Behind-the-scenes, customer stories, product tips",
            "notes": "Awaiting brand asset kit from design team.",
        },
        "CMP-005": {
            "name": "Annual Content Strategy 2026",
            "status": "Completed",
            "type": "content_strategy",
            "start_date": "2025-11-01",
            "end_date": "2025-12-15",
            "deliverables": "Strategy doc, editorial calendar, persona profiles",
            "content_pillars": "AI Innovation, Customer Success, Industry Trends, How-To Guides",
            "channels": "Blog, LinkedIn, Twitter/X, Email newsletter",
            "quarterly_goals": "Q1: Launch series, Q2: SEO push, Q3: Video, Q4: Year-in-review",
            "notes": "Approved by CMO. Execution started Q1 2026.",
        },
    }

    campaign = sample_campaigns.get(campaign_id.upper())
    if campaign:
        lines = [
            f"**{k.replace('_', ' ').title()}**: {v}"
            for k, v in campaign.items()
        ]
        return "\n".join(lines)
    return (
        f"Campaign not found: {campaign_id}. "
        "Please check the campaign ID and try again."
    )


@tool("check_content_performance")
def check_content_performance(channel: str) -> str:
    """Check the current performance metrics for a content channel.

    Use this tool to see how a content channel is performing
    including traffic, engagement, and conversion metrics.

    Args:
        channel: The content channel to check
            (e.g., blog, linkedin, twitter, instagram, email, youtube).

    Returns:
        Current channel performance metrics.
    """
    channel_metrics = {
        "blog": {
            "channel": "Company Blog",
            "monthly_visitors": "45,200",
            "page_views": "128,500",
            "avg_session_duration": "3:45",
            "bounce_rate": "42%",
            "top_traffic_source": "Organic Search (62%)",
            "conversion_rate": "2.8%",
            "top_posts_this_month": (
                "1. '10 AI Trends for 2026' (8,200 views), "
                "2. 'Complete Guide to Content Marketing' (5,100 views), "
                "3. 'How to Build a Content Calendar' (3,800 views)"
            ),
            "trend": "↑ 15% MoM growth in organic traffic",
        },
        "linkedin": {
            "channel": "LinkedIn Company Page",
            "followers": "28,500",
            "monthly_impressions": "312,000",
            "engagement_rate": "4.2%",
            "clicks_per_post": "145 avg",
            "top_content_type": "Carousel posts (6.1% engagement)",
            "best_posting_time": "Tuesday & Thursday, 8-10 AM",
            "follower_growth": "+1,200/month",
            "trend": "↑ Carousel posts driving 3x engagement vs text-only",
        },
        "twitter": {
            "channel": "Twitter/X (@company)",
            "followers": "15,800",
            "monthly_impressions": "198,000",
            "engagement_rate": "2.1%",
            "retweets_per_post": "12 avg",
            "top_content_type": "Thread posts (3.5% engagement)",
            "best_posting_time": "Weekdays, 12-1 PM",
            "follower_growth": "+450/month",
            "trend": "→ Steady. Thread posts outperform single tweets 2:1",
        },
        "instagram": {
            "channel": "Instagram (@company)",
            "followers": "22,100",
            "monthly_reach": "245,000",
            "engagement_rate": "3.8%",
            "saves_per_post": "85 avg",
            "top_content_type": "Reels (5.2% engagement)",
            "best_posting_time": "Mon/Wed/Fri, 11 AM - 1 PM",
            "follower_growth": "+800/month",
            "trend": "↑ Reels driving 40% of new follows",
        },
        "email": {
            "channel": "Email Newsletter (Weekly Digest)",
            "subscribers": "18,400",
            "open_rate": "32.5%",
            "click_rate": "4.8%",
            "unsubscribe_rate": "0.3%",
            "avg_revenue_per_send": "$1,250",
            "best_send_time": "Tuesday 9 AM",
            "list_growth": "+600/month",
            "trend": "↑ Personalized subject lines boosted open rate by 18%",
        },
        "youtube": {
            "channel": "YouTube Channel",
            "subscribers": "8,200",
            "monthly_views": "42,000",
            "avg_view_duration": "6:12",
            "watch_time_hours": "4,340",
            "top_content_type": "How-to tutorials (8:30 avg duration)",
            "best_upload_day": "Wednesday",
            "subscriber_growth": "+350/month",
            "trend": "↑ Tutorial videos gaining traction. Shorts underperforming.",
        },
    }

    key = channel.strip().lower().replace(" ", "_").replace("/", "")
    # Handle aliases
    alias_map = {"x": "twitter", "twitterx": "twitter", "ig": "instagram"}
    key = alias_map.get(key, key)

    metrics = channel_metrics.get(key)
    if metrics:
        lines = [
            f"**{k.replace('_', ' ').title()}**: {v}"
            for k, v in metrics.items()
        ]
        return "\n".join(lines)

    available = ", ".join(sorted(channel_metrics.keys()))
    return (
        f"Channel '{channel}' not found. "
        f"Available channels: {available}"
    )
