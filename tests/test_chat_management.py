from uuid import uuid4

from fastapi.testclient import TestClient
from app.api.main import app
from app.storage.history import save


def test_manage_chat_without_removing_shared_turns(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELROI_ENABLE_LOCAL", "true")
    monkeypatch.setenv("MODELROI_HISTORY_DIR", str(tmp_path))
    client = TestClient(app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"})
    root, left, right, other = [str(uuid4()) for _ in range(4)]
    for turn, parent in [(root, None), (left, root), (right, root), (other, None)]:
        save(dict(run_id=turn, parent_id=parent, evidence_type="custom_prompt", prompt="Question",
                  started_at="2026-11-08", model_id="qwen3:4b"))
    path = "/studio/chats/" + left
    for action in ["rename", "pin", "unpin", "pin"]:
        assert client.post(path, json={"action": action, "title": "My chat"}).is_success
    entry = next(r for r in client.get("/studio/history").json() if r["run_id"] == left)
    assert entry["chat_name"] == "My chat" and entry["pinned"]
    assert client.post("/studio/chats/" + root, json={"action": "delete"}).status_code == 409
    assert client.post(path, json={"action": "delete"}).json()["removed"] == [left]
    assert client.post("/studio/chats/" + right, json={"action": "delete"}).json()["removed"] == [right, root]
    assert [r["run_id"] for r in client.get("/studio/history").json()] == [other]
