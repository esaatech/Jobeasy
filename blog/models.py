from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from django_ckeditor_5.fields import CKEditor5Field

from .storage import get_blog_file_storage
from .utils import normalize_blog_body


class BlogCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive categories are hidden from public API lists.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "blog categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140]
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    excerpt = models.TextField(
        blank=True,
        help_text="Plain-text summary for listings, SEO, and AI generation.",
    )
    body = CKEditor5Field(
        config_name="blog",
        help_text=(
            "Write in the visual editor (headings, bold, lists). "
            "Do not paste raw HTML—use formatting buttons instead."
        ),
    )
    featured_image = models.ImageField(
        upload_to="blog/featured/",
        storage=get_blog_file_storage,
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.PROTECT,
        related_name="posts",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text='List of tag strings, e.g. ["resume", "interview"].',
    )
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    reading_time_minutes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Optional; leave blank to omit from API responses.",
    )
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    related_posts = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="related_from",
        help_text="Optional manual related posts shown below the article.",
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["category", "status"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("blog:post-detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:250] or "post"
            slug = base
            counter = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix = f"-{counter}"
                slug = f"{base[: 280 - len(suffix)]}{suffix}"
                counter += 1
            self.slug = slug

        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        if self.status != self.Status.PUBLISHED:
            self.published_at = None

        if self.body:
            self.body = normalize_blog_body(self.body)

        super().save(*args, **kwargs)

    def get_related_posts(self, limit=4):
        """Manual related posts first; otherwise same-category published posts."""
        manual = list(
            self.related_posts.filter(status=self.Status.PUBLISHED).order_by(
                "-published_at"
            )[:limit]
        )
        if manual:
            return manual[:limit]

        return list(
            BlogPost.objects.filter(
                status=self.Status.PUBLISHED,
                category=self.category,
            )
            .exclude(pk=self.pk)
            .order_by("-published_at")[:limit]
        )
