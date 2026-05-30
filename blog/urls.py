from django.urls import path

from . import page_views, views

app_name = "blog"

urlpatterns = [
    # Public pages
    path("blog/", page_views.post_list, name="index"),
    path("blog/category/<slug:slug>/", page_views.category_posts, name="category"),
    path("blog/<slug:slug>/", page_views.post_detail, name="post-detail"),
    # Staff / AI write API (must be before <slug> routes)
    path(
        "api/blog/posts/manage/",
        views.BlogPostCreateAPIView.as_view(),
        name="post-create",
    ),
    path(
        "api/blog/posts/manage/<slug:slug>/publish/",
        views.BlogPostPublishAPIView.as_view(),
        name="post-publish",
    ),
    path(
        "api/blog/posts/manage/<slug:slug>/",
        views.BlogPostUpdateAPIView.as_view(),
        name="post-update",
    ),
    path(
        "api/blog/categories/manage/",
        views.BlogCategoryManageListCreateAPIView.as_view(),
        name="category-manage",
    ),
    # Public read API
    path("api/blog/categories/", views.BlogCategoryListAPIView.as_view(), name="category-list"),
    path(
        "api/blog/categories/<slug:slug>/",
        views.BlogCategoryDetailAPIView.as_view(),
        name="category-detail",
    ),
    path("api/blog/posts/", views.BlogPostListAPIView.as_view(), name="post-list"),
    path(
        "api/blog/posts/<slug:slug>/",
        views.BlogPostDetailAPIView.as_view(),
        name="post-api-detail",
    ),
]
