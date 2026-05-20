from django.contrib import admin
from django.utils.html import format_html

from .models import BlogCategory, BlogPost


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "post_count", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)

    @admin.display(description="Posts")
    def post_count(self, obj):
        return obj.posts.count()


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "status",
        "author",
        "published_at",
        "updated_at",
    )
    list_filter = ("status", "category", "author")
    search_fields = ("title", "slug", "excerpt", "body", "tags")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "featured_image_preview")
    filter_horizontal = ("related_posts",)
    date_hierarchy = "published_at"
    ordering = ("-updated_at",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "excerpt",
                    "body",  # Type in the visual editor; do not paste raw HTML from Source mode
                    "category",
                    "author",
                    "status",
                    "published_at",
                )
            },
        ),
        (
            "Media & discovery",
            {
                "fields": (
                    "featured_image",
                    "featured_image_preview",
                    "tags",
                    "related_posts",
                    "reading_time_minutes",
                )
            },
        ),
        (
            "SEO",
            {
                "fields": ("meta_title", "meta_description"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Featured image preview")
    def featured_image_preview(self, obj):
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-height:120px;border-radius:4px;" />',
                obj.featured_image.url,
            )
        return "—"

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)
