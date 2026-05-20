"""
Blog API serializers.

Public read serializers return stable, frontend-friendly shapes.
Write serializers accept flat fields so an AI agent can POST JSON without
nested category objects — use category_slug instead of category id.
"""

from rest_framework import serializers

from .models import BlogCategory, BlogPost


class BlogCategorySerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = BlogCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "post_count",
        ]

    def get_post_count(self, obj):
        return obj.posts.filter(status=BlogPost.Status.PUBLISHED).count()


class BlogCategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ["name", "slug", "description", "is_active"]


class BlogPostListSerializer(serializers.ModelSerializer):
    category = BlogCategorySerializer(read_only=True)
    author_name = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "featured_image",
            "category",
            "author_name",
            "tags",
            "reading_time_minutes",
            "published_at",
            "meta_title",
            "meta_description",
        ]

    def get_featured_image(self, obj):
        if not obj.featured_image:
            return None
        request = self.context.get("request")
        url = obj.featured_image.url
        return request.build_absolute_uri(url) if request else url

    def get_author_name(self, obj):
        if not obj.author:
            return None
        return obj.author.get_full_name() or obj.author.get_username()


class BlogPostDetailSerializer(BlogPostListSerializer):
    body = serializers.CharField()
    related_posts = serializers.SerializerMethodField()

    class Meta(BlogPostListSerializer.Meta):
        fields = BlogPostListSerializer.Meta.fields + [
            "body",
            "related_posts",
            "created_at",
            "updated_at",
        ]

    def get_related_posts(self, obj):
        related = obj.get_related_posts(limit=4)
        return BlogPostListSerializer(
            related, many=True, context=self.context
        ).data


class BlogPostWriteSerializer(serializers.ModelSerializer):
    """
    Create/update contract for staff and future AI blog generation.

    Required: title, body, category_slug
    Optional: slug (auto-generated), excerpt, status, tags, SEO fields,
              related_post_slugs, featured_image, reading_time_minutes
    """

    category_slug = serializers.SlugField(write_only=True)
    related_post_slugs = serializers.ListField(
        child=serializers.SlugField(),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text="Slugs of posts to show as related (manual override).",
    )

    class Meta:
        model = BlogPost
        fields = [
            "title",
            "slug",
            "excerpt",
            "body",
            "category_slug",
            "status",
            "tags",
            "meta_title",
            "meta_description",
            "reading_time_minutes",
            "related_post_slugs",
            "featured_image",
            "published_at",
        ]
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
            "excerpt": {"required": False, "allow_blank": True},
            "published_at": {"required": False},
        }

    def validate_category_slug(self, value):
        try:
            return BlogCategory.objects.get(slug=value, is_active=True)
        except BlogCategory.DoesNotExist as exc:
            raise serializers.ValidationError(
                f"No active category with slug '{value}'."
            ) from exc

    def validate_related_post_slugs(self, value):
        if not value:
            return []
        found = BlogPost.objects.filter(slug__in=value)
        found_slugs = set(found.values_list("slug", flat=True))
        missing = [s for s in value if s not in found_slugs]
        if missing:
            raise serializers.ValidationError(
                f"Unknown post slugs: {', '.join(missing)}"
            )
        return list(found)

    def create(self, validated_data):
        category = validated_data.pop("category_slug")
        related = validated_data.pop("related_post_slugs", [])
        validated_data["category"] = category
        post = super().create(validated_data)
        if related:
            post.related_posts.set(related)
        return post

    def update(self, instance, validated_data):
        if "category_slug" in validated_data:
            validated_data["category"] = validated_data.pop("category_slug")
        related = validated_data.pop("related_post_slugs", None)
        post = super().update(instance, validated_data)
        if related is not None:
            post.related_posts.set(related)
        return post
