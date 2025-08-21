

def discounts_to_string(all_items, max_items=20):
    """
    Convert scraped discounts into a simple bullet-point list string.

    Args:
        all_items (List[Dict[str, Any]]): List of discounts from scrape_aanbiedingen.
        max_items (int, optional): Max number of items to include. Defaults to 20.

    Returns:
        str: Bullet-point formatted string summarizing the discounts.
    """
    if not all_items:
        return "- No discounts available today."

    lines = []
    for item in all_items[:max_items]:
        name = item.get("name") or "Unknown"
        promo = item.get("promotion") or "No promo"
        discounted = item.get("discounted_price") or "N/A"
        original = item.get("original_price") or "N/A"
        extra = item.get("extra_info") or ""

        line = f"- {name}{f' ({extra})' if extra else ''} | {promo} | {discounted} (was {original})"
        lines.append(line)

    if len(all_items) > max_items:
        lines.append(f"- ... {len(all_items) - max_items} more items not shown")

    return "\n".join(lines)