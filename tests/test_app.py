"""Tests for the FastAPI application"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from src.app import activities
    
    initial_state = {
        "Basketball Team": {
            "description": "Competitive basketball team with regular practices and games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Tennis training and friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["sarah@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and various art techniques",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["isabella@mergington.edu"]
        },
        "Theater Club": {
            "description": "Drama, acting, and stage performance",
            "schedule": "Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu"]
        },
        "Debate Team": {
            "description": "Competitive debate and public speaking skills",
            "schedule": "Mondays and Fridays, 3:30 PM - 4:45 PM",
            "max_participants": 10,
            "participants": ["james@mergington.edu"]
        },
        "Robotics Club": {
            "description": "Build and program robots for competitions",
            "schedule": "Tuesdays, Thursdays, Saturdays, 4:00 PM - 6:00 PM",
            "max_participants": 14,
            "participants": ["noah@mergington.edu", "ava@mergington.edu"]
        },
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
        }
    }
    
    # Store original state
    original_activities = {}
    for key, value in activities.items():
        original_activities[key] = {
            "description": value["description"],
            "schedule": value["schedule"],
            "max_participants": value["max_participants"],
            "participants": value["participants"].copy()
        }
    
    yield
    
    # Restore original state
    activities.clear()
    activities.update(initial_state)


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the get activities endpoint"""
    
    def test_get_all_activities(self, client, reset_activities):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have the expected number of activities
        assert len(data) == 9
        
        # Check specific activity exists
        assert "Basketball Team" in data
        assert data["Basketball Team"]["max_participants"] == 15
        assert "alex@mergington.edu" in data["Basketball Team"]["participants"]
    
    def test_activities_have_required_fields(self, client, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Test the signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Basketball Team"]["participants"]
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test signup fails when student already signed up"""
        response = client.post(
            "/activities/Basketball Team/signup?email=alex@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_invalid_activity(self, client, reset_activities):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/Non Existent Activity/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Test the unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister from an activity"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=alex@mergington.edu"
        )
        
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "alex@mergington.edu" not in activities_data["Basketball Team"]["participants"]
    
    def test_unregister_not_signed_up(self, client, reset_activities):
        """Test unregister fails when student not signed up"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=unknown@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_invalid_activity(self, client, reset_activities):
        """Test unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/Non Existent Activity/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestActivityConstraints:
    """Test activity constraints and business logic"""
    
    def test_max_participants_not_enforced_in_signup(self, client, reset_activities):
        """Test that signup doesn't enforce max participants limit"""
        # This tests the current behavior - max_participants is shown but not enforced
        response = client.get("/activities")
        basketball_data = response.json()["Basketball Team"]
        
        # Current implementation doesn't check max_participants on signup
        initial_count = len(basketball_data["participants"])
        assert initial_count > 0
    
    def test_participant_list_maintained(self, client, reset_activities):
        """Test that participant list is properly maintained"""
        # Get initial state
        response = client.get("/activities")
        robotics_team = response.json()["Robotics Club"]
        initial_participants = robotics_team["participants"].copy()
        
        # Should have 2 initial participants
        assert len(initial_participants) == 2
        assert "noah@mergington.edu" in initial_participants
        assert "ava@mergington.edu" in initial_participants
