from django.test import RequestFactory, TestCase, override_settings

from resume_builder.profile_photo_media import (
    has_stored_profile_photo,
    resolve_profile_photo_display_url,
    sanitize_personal_info_for_db,
)
from resume_builder.resume_display import augment_resume_dict_for_rendering


class ProfilePhotoMediaTests(TestCase):
    def test_sanitize_strips_embedded_display_url(self):
        raw = {
            "full_name": "Ada",
            "profile_photo_display_url": "data:image/jpeg;base64,abc",
            "profile_image_gcs_bucket": "my-bucket",
            "profile_image_blob": "prod/profile-photos/user-1/resume-2.jpg",
            "profile_image_local_path": "profile_photos/1/resume_2.jpg",
        }
        cleaned = sanitize_personal_info_for_db(raw)
        self.assertNotIn("profile_photo_display_url", cleaned)
        self.assertEqual(cleaned["profile_image_gcs_bucket"], "my-bucket")

    @override_settings(ENABLE_GCS_PROFILE_UPLOAD=True, GS_BUCKET_NAME="my-bucket")
    def test_sanitize_drops_local_path_when_gcs_canonical(self):
        raw = {
            "profile_image_gcs_bucket": "my-bucket",
            "profile_image_blob": "prod/profile-photos/user-1/resume-2.jpg",
            "profile_image_local_path": "profile_photos/1/resume_2.jpg",
        }
        cleaned = sanitize_personal_info_for_db(raw)
        self.assertNotIn("profile_image_local_path", cleaned)

    @override_settings(ENABLE_GCS_PROFILE_UPLOAD=False, GS_BUCKET_NAME="")
    def test_resolve_gcs_without_upload_flag_uses_proxy(self):
        factory = RequestFactory()
        request = factory.get("/resume/edit/")
        request.META["HTTP_HOST"] = "example.com"
        request.META["SERVER_PORT"] = "443"
        request.META["wsgi.url_scheme"] = "https"

        pi = {
            "profile_image_gcs_bucket": "my-bucket",
            "profile_image_blob": "prod/profile-photos/user-1/resume-2.jpg",
            "profile_photo_display_url": "data:image/jpeg;base64,OLD",
        }
        url = resolve_profile_photo_display_url(
            pi, request=request, resume_id=2, cache_version="99"
        )
        self.assertIn("/resume/profile-photo-proxy/2/", url)
        self.assertIn("v=99", url)
        self.assertFalse(url.startswith("data:"))

    def test_augment_ignores_stale_data_url_when_storage_exists(self):
        factory = RequestFactory()
        request = factory.get("/resume/edit/")
        request.META["HTTP_HOST"] = "example.com"
        request.META["SERVER_PORT"] = "443"
        request.META["wsgi.url_scheme"] = "https"

        data = {
            "personal_info": {
                "profile_photo_display_url": "data:image/jpeg;base64,OLD",
                "profile_image_gcs_bucket": "my-bucket",
                "profile_image_blob": "prod/profile-photos/user-1/resume-2.jpg",
            }
        }
        out = augment_resume_dict_for_rendering(
            data, request=request, resume_id=2, cache_version="1"
        )
        display = out["personal_info"]["profile_photo_display_url"]
        self.assertIn("/resume/profile-photo-proxy/2/", display)
        self.assertFalse(display.startswith("data:"))

    def test_augment_keeps_transient_data_url_without_storage(self):
        data = {
            "personal_info": {
                "profile_photo_display_url": "data:image/jpeg;base64,DRAFT",
            }
        }
        out = augment_resume_dict_for_rendering(data)
        self.assertEqual(
            out["personal_info"]["profile_photo_display_url"],
            "data:image/jpeg;base64,DRAFT",
        )
        self.assertFalse(has_stored_profile_photo(data["personal_info"]))
