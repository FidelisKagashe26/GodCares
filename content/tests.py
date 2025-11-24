from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import (
    Category,
    Post,
    PrayerRequest,
    DiscipleshipJourney,
    MissionReport,
    BibleStudyGroup,
    GlobalSoulsCounter,
    Profile,
)


class CategoryAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )
        self.category = Category.objects.create(
            name="Test Category",
            description="Test description",
        )

    def test_get_categories(self):
        response = self.client.get("/api/v1/content/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_category_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {"name": "New Category", "description": "New category description"}
        response = self.client.post("/api/v1/content/categories/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_category_as_regular_user(self):
        self.client.force_authenticate(user=self.user)
        data = {"name": "New Category", "description": "New category description"}
        response = self.client.post("/api/v1/content/categories/", data)
        # anapaswa kukataliwa
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PostAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.category = Category.objects.create(name="Test Category")
        self.post = Post.objects.create(
            title="Test Post",
            content="Test content",
            category=self.category,
            author=self.user,
            status="published",
        )

    def test_get_posts(self):
        response = self.client.get("/api/v1/content/posts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # tunatarajia pagination yenye key 'results'
        self.assertGreaterEqual(len(response.data.get("results", [])), 1)

    def test_get_post_detail(self):
        response = self.client.get(f"/api/v1/content/posts/{self.post.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Post")


class PrayerRequestAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_submit_prayer_request(self):
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "category": "personal",
            "request": "Please pray for my family",
            "is_anonymous": False,
            "is_urgent": False,
        }
        response = self.client.post("/api/v1/content/prayer-requests/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_submit_anonymous_prayer_request(self):
        data = {
            "category": "personal",
            "request": "Please pray for me",
            "is_anonymous": True,
            "is_urgent": False,
        }
        response = self.client.post("/api/v1/content/prayer-requests/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "")
        self.assertEqual(response.data["email"], "")


class DiscipleshipJourneyAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        # Signals tayari zimesha-create DiscipleshipJourney kwa huyu user
        self.journey = DiscipleshipJourney.objects.get(user=self.user)

    def test_get_user_journey(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/v1/content/discipleship-journeys/{self.journey.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_stage"], "seeker")

    def test_advance_journey_stage(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f"/api/v1/content/discipleship-journeys/{self.journey.id}/advance_stage/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["new_stage"], "scholar")


class MissionReportAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="missionary",
            email="missionary@example.com",
            password="testpass123",
        )
        self.mission_report = MissionReport.objects.create(
            missionary=self.user,
            title="Test Mission",
            location="Test Location",
            souls_reached=10,
        )

    def test_create_mission_report(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "New Mission Report",
            "location": "New Location",
            "souls_reached": 5,
            "testimonies": "Great results!",
            "gps_coordinates": {"lat": -6.123, "lng": 39.123},
        }
        # MUHIMU: tumia format='json' kwa sababu ya gps_coordinates (dict)
        response = self.client.post(
            "/api/v1/content/mission-reports/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_mission_stats(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/content/mission-reports/stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_souls_reached", response.data)


class BibleStudyGroupAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.leader = User.objects.create_user(
            username="leader",
            email="leader@example.com",
            password="testpass123",
        )
        self.member = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="testpass123",
        )
        self.group = BibleStudyGroup.objects.create(
            leader=self.leader,
            group_name="Test Group",
            meeting_frequency="weekly",
        )

    def test_create_bible_study_group(self):
        self.client.force_authenticate(user=self.leader)
        data = {
            "group_name": "New Study Group",
            "description": "Weekly Bible study",
            "meeting_frequency": "weekly",
            "location": "Church Hall",
            "max_members": 15,
            # Ongeza leader ili serializer asilalamike kama anahitaji field hii
            "leader": self.leader.id,
        }
        response = self.client.post("/api/v1/content/bible-study-groups/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_join_bible_study_group(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f"/api/v1/content/bible-study-groups/{self.group.id}/join/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GlobalSoulsCounterTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        GlobalSoulsCounter.objects.create(pk=1)

    def test_get_global_stats(self):
        response = self.client.get(
            "/api/v1/content/global-souls-counter/dashboard_stats/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_souls_reached", response.data)


class UserDashboardTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        # Profile & Journey zinatengenezwa na signals
        self.profile = Profile.objects.get(user=self.user)
        self.journey = DiscipleshipJourney.objects.get(user=self.user)

    def test_user_dashboard(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/content/user/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("journey", response.data)
        self.assertIn("recent_activity", response.data)
