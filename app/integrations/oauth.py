def oauth_state_for_user(user_id: int) -> str:
    return f"ga4:{user_id}"
