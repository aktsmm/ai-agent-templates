"""Custom tools for the e-commerce assistant agent."""

from crewai.tools import tool


@tool("search_product_catalog")
def search_product_catalog(query: str) -> str:
    """Search the product catalog for matching products.

    Use this tool to find products based on customer queries such as
    product names, categories, features, or price ranges.

    Args:
        query: The search query based on the customer's request.

    Returns:
        Matching product information from the catalog.
    """
    # In production, replace with a database/API call (e.g., Elasticsearch, Algolia)
    # This is a simple keyword-based fallback for the template
    from pathlib import Path

    knowledge_dir = Path(__file__).parent.parent / "knowledge"
    results: list[str] = []

    for file in knowledge_dir.glob("*.md"):
        content = file.read_text(encoding="utf-8")
        # Section-based search
        sections = content.split("\n### ")
        for section in sections:
            if query.lower() in section.lower():
                results.append(section.strip()[:500])

    if results:
        return "\n\n---\n\n".join(results[:5])
    return f"No products found matching: {query}"


@tool("lookup_order")
def lookup_order(order_id: str) -> str:
    """Look up order status by order ID.

    Use this tool to check the current status and shipping information
    for a customer's order.

    Args:
        order_id: The order ID to look up (e.g., ORD-12345).

    Returns:
        Order status information.
    """
    # In production, replace with actual order management system API
    # This returns sample data for the template
    sample_orders = {
        "ORD-12345": {
            "status": "In Transit",
            "items": "SoundMax Pro Headphones x1",
            "shipped_date": "2026-02-12",
            "carrier": "FedEx",
            "tracking": "FX-9876543210",
            "estimated_delivery": "2026-02-16",
            "current_location": "Chicago, IL Distribution Center",
        },
        "ORD-67890": {
            "status": "Processing",
            "items": "CleanBot X1 Robot Vacuum x1",
            "shipped_date": None,
            "carrier": None,
            "tracking": None,
            "estimated_delivery": "2026-02-20",
            "current_location": "Warehouse - Preparing for shipment",
        },
        "ORD-11111": {
            "status": "Delivered",
            "items": "SpeedStride Pro Running Shoes x1",
            "shipped_date": "2026-02-08",
            "carrier": "UPS",
            "tracking": "UP-1234567890",
            "estimated_delivery": "2026-02-11",
            "current_location": "Delivered to front door",
        },
    }

    order = sample_orders.get(order_id.upper())
    if order:
        lines = [f"**{k.replace('_', ' ').title()}**: {v}" for k, v in order.items()]
        return "\n".join(lines)
    return f"Order not found: {order_id}. Please check the order ID and try again."
