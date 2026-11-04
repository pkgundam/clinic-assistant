Step-1
install langchain, langchain-openai, langchain-deepseek using uv
lets create a basic agent using langchain's create_agent function.
model = gpt-5.4

1. create a new folder called agents
   create a python file called clinic_agent.py that has the langchain create agent.
   create a method called ask() and invoke the LLM inside this ask method with user's question
2. create a folder called prompts
   inside it create a file called prompts.py and define the system_prompt in it
   keep the prompt very basic for now -- you are a friendly clinic appointment booking assistant. keep your responses brief.
3. create a file called chat.py
   This is the wrapper to the agent which we will expand in future tasks
   It will take in a user input and send it to clinic agent.
4. test the code by running chat.py and clinic_agent should answer a question.
