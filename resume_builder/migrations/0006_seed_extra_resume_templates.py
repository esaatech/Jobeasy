from django.db import migrations


def seed_extra_templates(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    rows = [
        {
            "template_id": "executive",
            "name": "Executive",
            "description": (
                "For directors and senior leaders who want measurable impact upfront. Bold header, condensed "
                "roles, and a layout that favors outcomes over long task lists."
            ),
            "role_label": "Executive / leadership",
            "short_label": "Impact-focused header",
            "features": [
                "Executive header",
                "Outcome-oriented",
                "Condensed timeline",
                "Leadership-ready",
            ],
            "thumbnail_static": "img/resume_templates/executive.svg",
            "selection_gradient": "from-slate-700 to-slate-900",
            "selection_title_class": "text-slate-100",
            "featured": False,
            "featured_rank": 4,
            "is_active": True,
        },
        {
            "template_id": "portfolio",
            "name": "Portfolio",
            "description": (
                "Freelancers, consultants, and builders: foreground your projects and engagements, "
                "then back them up with experience and education. Skills live in a clear sidebar."
            ),
            "role_label": "Project / portfolio",
            "short_label": "Projects first",
            "features": [
                "Projects spotlight",
                "Sidebar skills",
                "Engagement-ready",
                "Flexible story",
            ],
            "thumbnail_static": "img/resume_templates/portfolio.svg",
            "selection_gradient": "from-teal-100 to-teal-50",
            "selection_title_class": "text-teal-900",
            "featured": False,
            "featured_rank": 5,
            "is_active": True,
        },
        {
            "template_id": "ats_plain",
            "name": "ATS Plain",
            "description": (
                "Simple single-column layout with standard headings and comma-separated skills. "
                "Optimizes readability for applicant tracking systems and quick recruiter scans."
            ),
            "role_label": "ATS plain",
            "short_label": "Parser-friendly",
            "features": [
                "Single column",
                "Standard headings",
                "Minimal styling",
                "High parse reliability",
            ],
            "thumbnail_static": "img/resume_templates/ats_plain.svg",
            "selection_gradient": "from-neutral-100 to-white",
            "selection_title_class": "text-neutral-900",
            "featured": False,
            "featured_rank": 6,
            "is_active": True,
        },
    ]
    for row in rows:
        ResumeTemplate.objects.update_or_create(template_id=row["template_id"], defaults=row)


def unseed_extra_templates(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    ResumeTemplate.objects.filter(template_id__in=["executive", "portfolio", "ats_plain"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("resume_builder", "0005_resumetemplate"),
    ]

    operations = [
        migrations.RunPython(seed_extra_templates, unseed_extra_templates),
    ]
