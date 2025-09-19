from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Post, Season, Series, Lesson, PrayerRequest

class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(
            name="Test Category",
            description="Test description"
        )
        self.assertEqual(category.slug, "test-category")
        self.assertEqual(str(category), "Test Category")

class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name="Test Category")
    
    def test_post_creation(self):
        post = Post.objects.create(
            title="Test Post",
            content="Test content",
            category=self.category,
            author=self.user,
            status='published'
        )
        self.assertEqual(post.slug, "test-post")
        self.assertEqual(str(post), "Test Post")

class PrayerRequestAPITest(APITestCase):
    def test_submit_prayer_request(self):
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'category': 'personal',
            'request': 'Please pray for my family',
            'is_anonymous': False,
            'is_urgent': False
        }
        response = self.client.post('/api/prayer-requests/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)

class PostAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name="Test Category")
        self.post = Post.objects.create(
            title="Test Post",
            content="Test content",
            category=self.category,
            author=self.user,
            status='published'
        )
    
    def test_get_posts(self):
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_post_detail(self):
        response = self.client.get(f'/api/posts/{self.post.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Post')