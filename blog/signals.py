"""Blog post media lifecycle: orphan cleanup on edit, full purge on delete."""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .media_cleanup import (
    cleanup_orphan_body_images,
    featured_image_storage_name,
    purge_blog_post_media,
)
from .models import BlogPost
from .storage import delete_blog_storage_name


@receiver(pre_save, sender=BlogPost)
def stash_previous_blog_media(sender, instance, **kwargs):
    """Remember prior body/featured image so post_save can delete replaced assets."""
    if not instance.pk:
        instance._blog_previous_body = None
        instance._blog_previous_featured = ""
        return
    try:
        previous = BlogPost.objects.only("body", "featured_image").get(pk=instance.pk)
    except BlogPost.DoesNotExist:
        instance._blog_previous_body = None
        instance._blog_previous_featured = ""
        return
    instance._blog_previous_body = previous.body
    instance._blog_previous_featured = featured_image_storage_name(previous.featured_image)


@receiver(post_save, sender=BlogPost)
def cleanup_blog_media_after_save(sender, instance, **kwargs):
    old_body = getattr(instance, "_blog_previous_body", None)
    if old_body is not None:
        cleanup_orphan_body_images(old_body, instance.body or "")

    old_featured = getattr(instance, "_blog_previous_featured", "") or ""
    new_featured = featured_image_storage_name(instance.featured_image)
    if old_featured and old_featured != new_featured:
        delete_blog_storage_name(old_featured)


@receiver(post_delete, sender=BlogPost)
def purge_blog_media_on_delete(sender, instance, **kwargs):
    purge_blog_post_media(instance)
