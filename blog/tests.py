from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import BlogCategory, BlogPost
from .utils import normalize_blog_body

User = get_user_model()


class BlogAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = BlogCategory.objects.create(
            name="Career Tips",
            slug="career-tips",
        )
        self.published = BlogPost.objects.create(
            title="Published Post",
            slug="published-post",
            excerpt="Summary",
            body="<p>Hello</p>",
            category=self.category,
            status=BlogPost.Status.PUBLISHED,
        )
        self.draft = BlogPost.objects.create(
            title="Draft Post",
            slug="draft-post",
            body="<p>Draft</p>",
            category=self.category,
            status=BlogPost.Status.DRAFT,
        )
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )

    def test_public_list_excludes_drafts(self):
        response = self.client.get("/api/blog/posts/")
        self.assertEqual(response.status_code, 200)
        slugs = [p["slug"] for p in response.json()]
        self.assertIn("published-post", slugs)
        self.assertNotIn("draft-post", slugs)

    def test_filter_by_category(self):
        response = self.client.get("/api/blog/posts/?category=career-tips")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_detail_includes_related_same_category(self):
        other = BlogPost.objects.create(
            title="Other Post",
            slug="other-post",
            body="<p>Other</p>",
            category=self.category,
            status=BlogPost.Status.PUBLISHED,
        )
        response = self.client.get("/api/blog/posts/published-post/")
        self.assertEqual(response.status_code, 200)
        related_slugs = [p["slug"] for p in response.json()["related_posts"]]
        self.assertIn(other.slug, related_slugs)

    def test_staff_create_post(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "title": "AI Draft",
            "excerpt": "Created via API",
            "body": "<p>Content</p>",
            "category_slug": "career-tips",
            "status": "draft",
            "tags": ["ai"],
        }
        response = self.client.post("/api/blog/posts/manage/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(BlogPost.objects.filter(slug="ai-draft").exists())

    def test_blog_index_page(self):
        response = self.client.get("/blog/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Post")
        self.assertNotContains(response, "Draft Post")

    def test_blog_detail_page(self):
        response = self.client.get("/blog/published-post/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Post")
        self.assertContains(response, "Hello")

    def test_blog_category_page(self):
        response = self.client.get("/blog/category/career-tips/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Career Tips")

    def test_draft_post_returns_404_on_frontend(self):
        response = self.client.get("/blog/draft-post/")
        self.assertEqual(response.status_code, 404)

    def test_normalize_blog_body_unescapes_ckeditor_paste(self):
        escaped = "<p>&lt;h2&gt;Title&lt;/h2&gt;&lt;p&gt;Text&lt;/p&gt;</p>"
        self.assertIn("<h2>Title</h2>", normalize_blog_body(escaped))

    def test_anonymous_cannot_create(self):
        response = self.client.post(
            "/api/blog/posts/manage/",
            {"title": "X", "body": "<p>x</p>", "category_slug": "career-tips"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
