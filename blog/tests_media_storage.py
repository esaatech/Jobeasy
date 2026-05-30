from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from blog.media_cleanup import (
    cleanup_orphan_body_images,
    extract_blog_media_names_from_html,
    purge_blog_post_media,
)
from blog.models import BlogCategory, BlogPost
from blog.storage import (
    gcs_object_name_for_upload,
    storage_name_from_public_url,
)


class BlogMediaPathTestCase(TestCase):
    @override_settings(
        ENABLE_GCS_BLOG_MEDIA=True,
        GS_BUCKET_NAME="my-bucket",
        DJANGO_ENV="production",
    )
    def test_gcs_object_name_adds_env_prefix(self):
        name = gcs_object_name_for_upload("blog/featured/hero.jpg")
        self.assertEqual(name, "production/blog/featured/hero.jpg")

    @override_settings(
        ENABLE_GCS_BLOG_MEDIA=True,
        GS_BUCKET_NAME="my-bucket",
        DJANGO_ENV="production",
    )
    def test_gcs_object_name_routes_bare_filename_to_ckeditor(self):
        name = gcs_object_name_for_upload("photo.png")
        self.assertTrue(name.startswith("production/blog/ckeditor/"))
        self.assertTrue(name.endswith(".png"))

    @override_settings(
        ENABLE_GCS_BLOG_MEDIA=False,
        MEDIA_URL="/media/",
    )
    def test_extract_media_url_from_html(self):
        html = '<p><img src="/media/blog/ckeditor/a.png" alt=""></p>'
        names = extract_blog_media_names_from_html(html)
        self.assertEqual(names, {"blog/ckeditor/a.png"})

    @override_settings(
        ENABLE_GCS_BLOG_MEDIA=True,
        GS_BUCKET_NAME="my-bucket",
        GCS_BLOG_MEDIA_BASE_URL="",
    )
    def test_extract_gcs_public_url_from_html(self):
        html = (
            '<img src="https://storage.googleapis.com/my-bucket/production/'
            'blog/ckeditor/b.jpg">'
        )
        names = extract_blog_media_names_from_html(html)
        self.assertEqual(names, {"production/blog/ckeditor/b.jpg"})

    def test_storage_name_from_public_url_media_path(self):
        with override_settings(MEDIA_URL="/media/"):
            name = storage_name_from_public_url("/media/blog/featured/x.jpg")
        self.assertEqual(name, "blog/featured/x.jpg")


class BlogMediaCleanupTestCase(TestCase):
    def setUp(self):
        self.category = BlogCategory.objects.create(name="Tips", slug="tips")

    @patch("blog.media_cleanup.delete_blog_storage_name")
    def test_cleanup_orphan_body_images(self, mock_delete):
        old = '<img src="/media/blog/ckeditor/old.png">'
        new = '<img src="/media/blog/ckeditor/keep.png">'
        cleanup_orphan_body_images(old, new)
        mock_delete.assert_called_once_with("blog/ckeditor/old.png")

    @patch("blog.media_cleanup.delete_blog_media_names")
    def test_purge_blog_post_media_on_delete(self, mock_delete_names):
        post = BlogPost.objects.create(
            title="Post",
            slug="post",
            body='<img src="/media/blog/ckeditor/inline.png">',
            category=self.category,
            status=BlogPost.Status.PUBLISHED,
        )
        post.featured_image.name = "blog/featured/hero.jpg"
        purge_blog_post_media(post)
        mock_delete_names.assert_called_once()
        deleted = mock_delete_names.call_args[0][0]
        self.assertIn("blog/featured/hero.jpg", deleted)
        self.assertIn("blog/ckeditor/inline.png", deleted)

    @patch("blog.media_cleanup.delete_blog_storage_name")
    def test_post_delete_signal_purges_media(self, mock_delete):
        post = BlogPost.objects.create(
            title="Gone",
            slug="gone",
            body='<img src="/media/blog/ckeditor/z.png">',
            category=self.category,
            status=BlogPost.Status.PUBLISHED,
        )
        post_id = post.pk
        post.delete()
        self.assertFalse(BlogPost.objects.filter(pk=post_id).exists())
        self.assertTrue(mock_delete.called)

    @patch("blog.media_cleanup.delete_blog_storage_name")
    def test_body_update_removes_orphan_inline_image(self, mock_delete):
        post = BlogPost.objects.create(
            title="Edit",
            slug="edit",
            body='<img src="/media/blog/ckeditor/remove-me.png">',
            category=self.category,
            status=BlogPost.Status.PUBLISHED,
        )
        post.body = "<p>No images now</p>"
        post.save()
        mock_delete.assert_called_with("blog/ckeditor/remove-me.png")

    @patch("blog.signals.delete_blog_storage_name")
    def test_featured_image_replace_deletes_previous(self, mock_delete):
        post = BlogPost.objects.create(
            title="Hero",
            slug="hero",
            body="<p>Hi</p>",
            category=self.category,
            status=BlogPost.Status.PUBLISHED,
        )
        post.featured_image.name = "blog/featured/old.jpg"
        post.save(update_fields=["featured_image"])

        post.featured_image.name = "blog/featured/new.jpg"
        post.save(update_fields=["featured_image"])

        mock_delete.assert_called_with("blog/featured/old.jpg")
