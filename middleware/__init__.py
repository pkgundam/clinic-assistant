from middleware.rolling_summary_middleware import summarize_old_messages
from middleware.user_profile_middleware import user_profile_middleware

# Every middleware we create is added to this list and given to the agent.
clinic_middlewares = [user_profile_middleware, summarize_old_messages]
