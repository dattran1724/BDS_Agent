from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_llm
from tests.test_agent_workflow import MockLLM

# Print override setup
print("Before override get_llm ID:", id(get_llm))
app.dependency_overrides[get_llm] = lambda: MockLLM(simulate_fail_once=False)
print("Overrides:", app.dependency_overrides)

client = TestClient(app)
res = client.post('/api/agent/start', json={'user_input': 'hello'})
print("Status code:", res.status_code)
print("Response JSON:", res.json())
