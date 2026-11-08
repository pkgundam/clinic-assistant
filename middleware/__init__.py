from middleware.input_guardrails_middleware import input_guardrails
from middleware.output_guardrails_middleware import output_guardrails
from middleware.rolling_summary_middleware import summarize_old_messages
from middleware.user_profile_middleware import user_profile_middleware

# Every middleware we create is added to this list and given to the agent.
clinic_middlewares = [input_guardrails, user_profile_middleware, summarize_old_messages, output_guardrails]
