from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .models import BlogCategory, BlogPost


def _published_posts():
    return BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).select_related(
        "category", "author"
    )


def _filter_posts(request, queryset=None):
    qs = queryset if queryset is not None else _published_posts()
    category_slug = request.GET.get("category", "").strip()
    if category_slug:
        qs = qs.filter(category__slug=category_slug, category__is_active=True)

    tag = request.GET.get("tag", "").strip()
    if tag:
        qs = qs.filter(tags__contains=[tag])

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(body__icontains=q)
        )
    return qs


@require_GET
def post_list(request):
    categories = (
        BlogCategory.objects.filter(is_active=True)
        .annotate(
            post_count=Count(
                "posts",
                filter=Q(posts__status=BlogPost.Status.PUBLISHED),
            )
        )
        .order_by("name")
    )
    active_category_slug = request.GET.get("category", "").strip()
    active_category = None
    if active_category_slug:
        active_category = categories.filter(slug=active_category_slug).first()

    posts = _filter_posts(request)
    active_tag = request.GET.get("tag", "").strip()
    search_query = request.GET.get("q", "").strip()

    return render(
        request,
        "blog/post_list.html",
        {
            "page_title": "Blog - Jobeas",
            "meta_description": "Career tips, resume advice, and job search insights from Jobeas.",
            "posts": posts,
            "categories": categories,
            "active_category": active_category,
            "active_category_slug": active_category_slug,
            "active_tag": active_tag,
            "search_query": search_query,
        },
    )


@require_GET
def category_posts(request, slug):
    category = get_object_or_404(BlogCategory, slug=slug, is_active=True)
    posts = _filter_posts(request, _published_posts().filter(category=category))
    categories = (
        BlogCategory.objects.filter(is_active=True)
        .annotate(
            post_count=Count(
                "posts",
                filter=Q(posts__status=BlogPost.Status.PUBLISHED),
            )
        )
        .order_by("name")
    )

    return render(
        request,
        "blog/post_list.html",
        {
            "page_title": f"{category.name} - Blog - Jobeas",
            "meta_description": category.description or f"Articles in {category.name}.",
            "posts": posts,
            "categories": categories,
            "active_category": category,
            "active_category_slug": category.slug,
            "active_tag": request.GET.get("tag", "").strip(),
            "search_query": request.GET.get("q", "").strip(),
        },
    )


@require_GET
def post_detail(request, slug):
    post = get_object_or_404(
        _published_posts(),
        slug=slug,
    )
    related_posts = post.get_related_posts(limit=4)

    meta_title = post.meta_title or post.title
    meta_description = post.meta_description or post.excerpt

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "related_posts": related_posts,
            "page_title": f"{meta_title} - Jobeas Blog",
            "meta_description": meta_description,
        },
    )
