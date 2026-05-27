"""Shared admin helpers: upload a resume PDF and extract text like the dashboard."""

from __future__ import annotations

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseNotAllowed
from django.urls import path, reverse

from utils.pdf_text import PdfTextExtractionError, extract_text_from_pdf


def admin_extract_resume_pdf_url(model_admin) -> str:
    opts = model_admin.model._meta
    name = f"admin:{opts.app_label}_{opts.model_name}_extract_resume_pdf"
    return reverse(name)


def resolve_resume_text_from_admin_request(request) -> tuple[str, str | None]:
    """
    Resume text for admin AI playgrounds.

    **Precedence:** non-empty ``resume_text`` textarea wins (what you see in the form,
    including after "Load PDF into resume text"). Only if the textarea is empty do we
    extract an attached ``resume_pdf``. This avoids a stale file input overriding loaded text.
    """
    text_from_field = (request.POST.get("resume_text") or "").strip()
    if text_from_field:
        return text_from_field, None

    uploaded = request.FILES.get("resume_pdf")
    if uploaded:
        name = (getattr(uploaded, "name", None) or "").lower()
        if not name.endswith(".pdf"):
            return "", "Only PDF files are supported."
        try:
            if hasattr(uploaded, "seek"):
                uploaded.seek(0)
            return extract_text_from_pdf(uploaded).strip(), None
        except PdfTextExtractionError as exc:
            return "", str(exc)

    return "", None


def admin_extract_resume_pdf_response(request, *, permission_check) -> HttpResponse:
    """POST multipart with ``resume_pdf``; returns JSON ``{success, text?, error?}``."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST", "OPTIONS"])

    if not permission_check(request):
        payload = {"success": False, "error": "Permission denied"}
        return HttpResponse(
            json.dumps(payload),
            status=403,
            content_type="application/json",
        )

    uploaded = request.FILES.get("resume_pdf")
    if not uploaded:
        payload = {"success": False, "error": "Upload a PDF file (field resume_pdf)."}
        return HttpResponse(
            json.dumps(payload),
            status=400,
            content_type="application/json",
        )

    text, err = resolve_resume_text_from_admin_request(request)
    if err:
        payload = {"success": False, "error": err}
        return HttpResponse(
            json.dumps(payload),
            status=400,
            content_type="application/json",
        )

    payload = {"success": True, "text": text, "length": len(text)}
    return HttpResponse(
        json.dumps(payload, cls=DjangoJSONEncoder),
        content_type="application/json",
    )


class AdminResumePdfExtractMixin:
    """Add PDF upload field support and extract-resume-pdf admin endpoint."""

    def get_urls(self):
        urls = super().get_urls()
        opts = self.model._meta
        basename = f"{opts.app_label}_{opts.model_name}"
        extra = [
            path(
                "extract-resume-pdf/",
                self.admin_site.admin_view(self.extract_resume_pdf),
                name=f"{basename}_extract_resume_pdf",
            ),
        ]
        return extra + urls

    def extract_resume_pdf(self, request):
        opts = self.model._meta

        def permitted(req) -> bool:
            return req.user.has_perm(f"{opts.app_label}.add_{opts.model_name}") or req.user.has_perm(
                f"{opts.app_label}.change_{opts.model_name}"
            )

        return admin_extract_resume_pdf_response(request, permission_check=permitted)

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["extract_pdf_url"] = admin_extract_resume_pdf_url(self)
        return super().add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["extract_pdf_url"] = admin_extract_resume_pdf_url(self)
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
