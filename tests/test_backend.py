import unittest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from app.main import app
from app.db import get_session
from app.models import Meeting, Platform

import os

# Use local temp SQLite database for testing
test_db_file = "./test_temp.db"
test_engine = create_engine(f"sqlite:///{test_db_file}", connect_args={"check_same_thread": False})


def override_get_session():
    with Session(test_engine) as session:
        yield session


class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Remove any leftover test DB
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass
        SQLModel.metadata.create_all(test_engine)
        app.dependency_overrides[get_session] = override_get_session
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        SQLModel.metadata.clear()
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass

    def setUp(self):
        # Clear tables before each test
        with Session(test_engine) as session:
            session.query(Meeting).delete()
            session.commit()

    def test_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"ok": True})

    def test_create_meeting(self):
        payload = {
            "title": "Project Kickoff",
            "platform": "google_meet",
            "meeting_url": "https://meet.google.com/abc-defg-hij",
            "recipient_email": "test@example.com"
        }
        res = self.client.post("/meetings", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["title"], "Project Kickoff")
        self.assertEqual(data["status"], "created")
        self.assertIsNotNone(data["id"])

    def test_add_transcript(self):
        # Create a meeting first
        payload = {
            "title": "Design Alignment",
            "platform": "zoom",
            "meeting_url": "https://zoom.us/j/123456789",
            "recipient_email": "test@example.com"
        }
        create_res = self.client.post("/meetings", json=payload)
        m_id = create_res.json()["id"]

        # Add transcript
        transcript_payload = {
            "transcript": "0.0-5.0: Speaker 0: Welcome to the design sync.\n5.0-10.0: Speaker 1: We will use blue.",
            "send_email": False
        }
        res = self.client.post(f"/meetings/{m_id}/transcript", json=transcript_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "mom_ready")
        self.assertIn("Welcome to the design sync", data["transcript"])
        self.assertTrue(len(data["mom"]) > 0)

    def test_rename_speaker(self):
        # Create meeting with transcript
        payload = {
            "title": "Weekly Update",
            "platform": "teams",
            "meeting_url": "https://teams.microsoft.com/l/meetup-join",
            "recipient_email": "test@example.com"
        }
        m_id = self.client.post("/meetings", json=payload).json()["id"]
        
        transcript_payload = {
            "transcript": "0.0-4.0: Speaker 0: Let's discuss metrics.\n4.0-9.0: Speaker 1: Speaker 0 is right.",
            "send_email": False
        }
        self.client.post(f"/meetings/{m_id}/transcript", json=transcript_payload)

        # Rename Speaker 0 to Alice
        rename_payload = {
            "old_name": "Speaker 0",
            "new_name": "Alice"
        }
        res = self.client.post(f"/meetings/{m_id}/rename-speaker", json=rename_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        # Verify renaming replaced the speaker tag but kept transcript content
        self.assertIn("0.0-4.0: Alice: Let's discuss metrics", data["transcript"])
        self.assertIn("Speaker 1: Speaker 0 is right", data["transcript"])  # Inner text should be unchanged

    def test_search_meetings(self):
        # Create two meetings
        m1 = self.client.post("/meetings", json={
            "title": "Sprint Planning",
            "platform": "google_meet",
            "meeting_url": "https://meet.google.com/aaa-bbbb-ccc",
            "recipient_email": "sprint@example.com"
        }).json()
        
        m2 = self.client.post("/meetings", json={
            "title": "Retro Sync",
            "platform": "google_meet",
            "meeting_url": "https://meet.google.com/ddd-eeee-fff",
            "recipient_email": "retro@example.com"
        }).json()

        # Add different transcripts
        self.client.post(f"/meetings/{m1['id']}/transcript", json={
            "transcript": "Today we will prioritize ticket A and ticket B.",
            "send_email": False
        })
        self.client.post(f"/meetings/{m2['id']}/transcript", json={
            "transcript": "We had issues with testing, let's fix that.",
            "send_email": False
        })

        # Search for "prioritize"
        res = self.client.get("/meetings/search?q=prioritize")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], m1["id"])
        self.assertIn("prioritize", data[0]["snippet"].lower())

        # Search for "issues"
        res = self.client.get("/meetings/search?q=issues")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], m2["id"])
        self.assertIn("issues", data[0]["snippet"].lower())

    def test_update_mom(self):
        payload = {
            "title": "Design Kickoff",
            "platform": "google_meet",
            "meeting_url": "https://meet.google.com/xyz-pdq-abc",
            "recipient_email": "test@example.com"
        }
        m_id = self.client.post("/meetings", json=payload).json()["id"]

        update_payload = {
            "mom": "# MOM\n- [ ] Task 1\n- [x] Task 2"
        }
        res = self.client.post(f"/meetings/{m_id}/mom", json=update_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["mom"], "# MOM\n- [ ] Task 1\n- [x] Task 2")


if __name__ == "__main__":
    unittest.main()

