"""
Tests for the Mergington High School Activities API

Uses pytest with FastAPI TestClient and AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
import urllib.parse

from src.app import app

# Original activities data for resetting between tests
ORIGINAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and compete in basketball games",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
        "max_participants": 15,
        "participants": ["alex@mergington.edu"]
    },
    "Soccer Club": {
        "description": "Train and play soccer matches",
        "schedule": "Wednesdays and Saturdays, 3:00 PM - 5:00 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "ava@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore painting, drawing, and other visual arts",
        "schedule": "Mondays, 3:30 PM - 5:00 PM",
        "max_participants": 18,
        "participants": ["isabella@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act in plays and learn theater skills",
        "schedule": "Tuesdays, 4:00 PM - 6:00 PM",
        "max_participants": 20,
        "participants": ["mason@mergington.edu", "charlotte@mergington.edu"]
    },
    "Debate Club": {
        "description": "Develop argumentation and public speaking skills",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["ethan@mergington.edu"]
    },
    "Science Club": {
        "description": "Conduct experiments and learn about scientific concepts",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 25,
        "participants": ["harper@mergington.edu", "logan@mergington.edu"]
    }
}


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities data before each test to ensure isolation"""
    from src.app import activities
    activities.clear()
    activities.update(ORIGINAL_ACTIVITIES)

# Create a TestClient instance for testing
client = TestClient(app)


class TestActivitiesEndpoint:
    """Test cases for GET /activities"""

    def test_get_activities_success(self):
        """Test successful retrieval of all activities"""
        # Arrange - No special setup needed

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # All activities present

        # Check structure of first activity
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupEndpoint:
    """Test cases for POST /activities/{activity_name}/signup"""

    @pytest.mark.parametrize("activity,email", [
        ("Chess Club", "newstudent@mergington.edu"),
        ("Programming Class", "coder@mergington.edu"),
        ("Gym Class", "athlete@mergington.edu"),
    ])
    def test_signup_success(self, activity, email):
        """Test successful signup for an activity"""
        # Arrange - Ensure student not already signed up
        activity_encoded = urllib.parse.quote(activity)
        response_check = client.get("/activities")
        initial_participants = response_check.json()[activity]["participants"]
        assert email not in initial_participants

        # Act
        response = client.post(f"/activities/{activity_encoded}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]

        # Verify participant was added
        response_verify = client.get("/activities")
        updated_participants = response_verify.json()[activity]["participants"]
        assert email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1

    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        # Arrange
        invalid_activity = "NonExistent Club"
        invalid_encoded = urllib.parse.quote(invalid_activity)
        email = "student@mergington.edu"

        # Act
        response = client.post(f"/activities/{invalid_encoded}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_already_signed_up(self):
        """Test signup when student is already enrolled"""
        # Arrange
        activity = "Chess Club"
        activity_encoded = urllib.parse.quote(activity)
        email = "michael@mergington.edu"  # Already in participants

        # Act
        response = client.post(f"/activities/{activity_encoded}/signup?email={email}")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_activity_full(self):
        """Test signup when activity reaches max capacity"""
        # Arrange - Fill up an activity
        activity = "Chess Club"
        activity_encoded = urllib.parse.quote(activity)

        # Get current state
        response_check = client.get("/activities")
        initial_data = response_check.json()
        assert activity in initial_data
        current_len = len(initial_data[activity]["participants"])
        max_part = initial_data[activity]["max_participants"]
        to_add = max_part - current_len

        # Add participants until full
        for i in range(to_add):
            email = f"student{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity_encoded}/signup?email={email}"
            )
            assert response.status_code == 200

        # Now try to add one more
        extra_email = "extra@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_encoded}/signup?email={extra_email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"]


class TestUnregisterEndpoint:
    """Test cases for DELETE /activities/{activity_name}/signup"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        # Arrange
        activity = "Programming Class"
        activity_encoded = urllib.parse.quote(activity)
        email = "emma@mergington.edu"  # Already enrolled

        # Verify initially enrolled
        response_check = client.get("/activities")
        initial_participants = response_check.json()[activity]["participants"]
        assert email in initial_participants

        # Act
        response = client.delete(f"/activities/{activity_encoded}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]

        # Verify participant was removed
        response_verify = client.get("/activities")
        updated_participants = response_verify.json()[activity]["participants"]
        assert email not in updated_participants
        assert len(updated_participants) == len(initial_participants) - 1

    def test_unregister_activity_not_found(self):
        """Test unregister from non-existent activity"""
        # Arrange
        invalid_activity = "Fake Club"
        invalid_encoded = urllib.parse.quote(invalid_activity)
        email = "student@mergington.edu"

        # Act
        response = client.delete(f"/activities/{invalid_encoded}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_enrolled(self):
        """Test unregister when student is not enrolled"""
        # Arrange
        activity = "Gym Class"
        activity_encoded = urllib.parse.quote(activity)
        email = "notenrolled@mergington.edu"

        # Act
        response = client.delete(f"/activities/{activity_encoded}/signup?email={email}")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]


class TestRootEndpoint:
    """Test cases for GET / (root redirect)"""

    def test_root_redirect(self):
        """Test that root redirects to static index"""
        # Arrange - No setup needed

        # Act
        response = client.get("/", follow_redirects=False)  # Don't follow redirect

        # Assert
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"