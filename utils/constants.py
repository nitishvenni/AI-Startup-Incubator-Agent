"""
utils/constants.py - Shared dropdown constants used across routes.

Import from here instead of repeating the lists in every route file.
"""

INDUSTRIES = [
    "Technology", "Healthcare", "Finance", "Education", "E-commerce",
    "Real Estate", "Food & Beverage", "Transportation", "Entertainment",
    "Agriculture", "Energy", "Fashion", "Travel", "Sports", "Other",
]

BUDGETS = [
    "Under $10,000", "$10,000 – $50,000", "$50,000 – $100,000",
    "$100,000 – $500,000", "$500,000 – $1M", "Over $1M",
]

COUNTRIES = [
    "United States", "United Kingdom", "Canada", "Australia", "Germany",
    "France", "India", "China", "Japan", "Brazil", "South Africa",
    "Nigeria", "Kenya", "Singapore", "UAE", "Netherlands", "Sweden",
    "Israel", "South Korea", "Mexico", "Other",
]

ALLOWED_STATUSES = {"pending", "analyzed", "in_progress", "launched", "archived"}
