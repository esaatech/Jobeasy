from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BlogCategory, BlogPost
from .serializers import (
    BlogCategorySerializer,
    BlogCategoryWriteSerializer,
    BlogPostDetailSerializer,
    BlogPostListSerializer,
    BlogPostWriteSerializer,
)


class BlogCategoryListAPIView(generics.ListAPIView):
    """GET /api/blog/categories/ — active categories with published post counts."""

    serializer_class = BlogCategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return BlogCategory.objects.filter(is_active=True)


class BlogCategoryDetailAPIView(generics.RetrieveAPIView):
    """GET /api/blog/categories/<slug>/"""

    serializer_class = BlogCategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return BlogCategory.objects.filter(is_active=True)


class BlogPostListAPIView(generics.ListAPIView):
    """
    GET /api/blog/posts/

    Query params:
      - category: category slug
      - tag: filter posts containing this tag (case-insensitive)
      - q: search title, excerpt, body
    """

    serializer_class = BlogPostListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).select_related(
            "category", "author"
        )
        category_slug = self.request.query_params.get("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug, category__is_active=True)

        tag = self.request.query_params.get("tag", "").strip()
        if tag:
            qs = qs.filter(tags__contains=[tag])

        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(excerpt__icontains=q)
                | Q(body__icontains=q)
            )
        return qs


class BlogPostDetailAPIView(generics.RetrieveAPIView):
    """GET /api/blog/posts/<slug>/ — full post with related_posts."""

    serializer_class = BlogPostDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).select_related(
            "category", "author"
        )


class BlogPostCreateAPIView(generics.CreateAPIView):
    """
    POST /api/blog/posts/manage/

    Staff-only. Accepts BlogPostWriteSerializer (AI-friendly flat JSON).
    """

    serializer_class = BlogPostWriteSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        author = self.request.user if self.request.user.is_authenticated else None
        serializer.save(author=author)


class BlogPostUpdateAPIView(generics.UpdateAPIView):
    """PATCH/PUT /api/blog/posts/manage/<slug>/ — staff-only partial updates."""

    serializer_class = BlogPostWriteSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "slug"
    queryset = BlogPost.objects.all()
    http_method_names = ["put", "patch"]


class BlogPostPublishAPIView(APIView):
    """POST /api/blog/posts/manage/<slug>/publish/ — set status to published."""

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, slug):
        try:
            post = BlogPost.objects.get(slug=slug)
        except BlogPost.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        post.status = BlogPost.Status.PUBLISHED
        post.save()
        return Response(BlogPostDetailSerializer(post, context={"request": request}).data)


class BlogCategoryManageListCreateAPIView(generics.ListCreateAPIView):
    """GET/POST /api/blog/categories/manage/ — staff category CRUD (list + create)."""

    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BlogCategoryWriteSerializer
        return BlogCategorySerializer

    def get_queryset(self):
        return BlogCategory.objects.all()
