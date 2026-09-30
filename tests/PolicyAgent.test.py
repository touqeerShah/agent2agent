from IPython.display import Markdown, display
from agents.PolicyAgent import PolicyAgent

print("Running Health Insurance Policy Agent")
agent = PolicyAgent()
prompt = "How much would I pay for mental health therapy?"

response = agent.answer_query(prompt)
display(Markdown(response))