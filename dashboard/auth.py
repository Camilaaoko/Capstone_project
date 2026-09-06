"""Authentication service and mock user repository for KEMSA Platform."""

from typing import Optional, Dict, Any

# Mock users database
MOCK_USERS = {
    "admin": {
        "username": "admin",
        "email": "admin@kemsa.go.ke",
        "passwords": ["admin", "admin123", "kemsa2026", "password"],
        "name": "System Administrator",
        "role": "Super Admin",
        "avatar": "🛡️",
        "title": "National System Administrator",
        "default_tab": "tab-executive"
    },
    "executive": {
        "username": "executive",
        "email": "executive@kemsa.go.ke",
        "passwords": ["executive", "kemsa2026", "password", "executive123"],
        "name": "Dr. Terry Ramadhani",
        "role": "KEMSA Executive",
        "avatar": "📊",
        "title": "Chief Executive Officer, KEMSA",
        "default_tab": "tab-executive"
    },
    "director": {
        "username": "director",
        "email": "county@health.go.ke",
        "passwords": ["director", "county2026", "password", "director123"],
        "name": "Dr. Beatrice Awiti",
        "role": "County Health Director",
        "avatar": "🗺️",
        "title": "Director of Health Services, Kisumu County",
        "default_tab": "tab-county"
    },
    "facility": {
        "username": "facility",
        "email": "facility@clinic.go.ke",
        "passwords": ["facility", "facility2026", "password", "facility123"],
        "name": "Pharm. Kevin Ochieng",
        "role": "Facility Pharmacist",
        "avatar": "🏥",
        "title": "Head of Pharmacy, Level 4 Hospital",
        "default_tab": "tab-facility"
    },
    "planner": {
        "username": "planner",
        "email": "planner@logistics.go.ke",
        "passwords": ["planner", "planner2026", "password", "planner123"],
        "name": "Eng. Sarah Mumbua",
        "role": "Logistics & Supply Planner",
        "avatar": "🔄",
        "title": "Logistics & Fleet Allocation Officer",
        "default_tab": "tab-redistribution"
    }
}


def authenticate_user(username_or_email: str, password: str = "") -> Optional[Dict[str, Any]]:
    """Validates user credentials against the mock user store.
    
    Accepts either username or email (case-insensitive for username/email).
    Supports multiple password variations.
    """
    if not username_or_email:
        return None
    
    query = username_or_email.strip().lower()
    pw = (password or "").strip()
    
    for user_key, user_data in MOCK_USERS.items():
        if (query == user_data["username"].lower() or query == user_data["email"].lower() or query == user_key):
            # If password is provided, match against accepted passwords; if empty password on direct demo action, allow
            if not pw or pw in user_data["passwords"] or pw == user_key:
                return {
                    "authenticated": True,
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "role": user_data["role"],
                    "avatar": user_data["avatar"],
                    "title": user_data["title"],
                    "default_tab": user_data["default_tab"]
                }
    return None


def get_mock_users() -> Dict[str, Dict[str, Any]]:
    """Returns the dictionary of mock users for demo displays."""
    return MOCK_USERS
