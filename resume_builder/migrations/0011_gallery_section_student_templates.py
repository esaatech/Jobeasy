from django.db import migrations, models


def seed_student_templates(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    ResumeTemplate.objects.exclude(
        template_id__in=("new_grad_ats", "new_grad_projects", "new_grad_profile")
    ).update(gallery_section="general")

    rows = [
        {
            "template_id": "new_grad_ats",
            "name": "Campus ATS",
            "description": (
                "Minimal single-column layout with education and projects up front—built for campus recruiting "
                "and applicant tracking systems when you are light on formal work history."
            ),
            "role_label": "Student / new grad · ATS",
            "short_label": "Education + keywords first",
            "features": [
                "Single column",
                "Education-forward",
                "Projects block",
                "Parser-friendly skills",
            ],
            "thumbnail_static": "img/resume_templates/new_grad_ats.svg",
            "selection_gradient": "from-slate-100 to-white",
            "selection_title_class": "text-slate-800",
            "gallery_section": "students",
            "featured": False,
            "featured_rank": 11,
            "is_active": True,
        },
        {
            "template_id": "new_grad_projects",
            "name": "Project Focus",
            "description": (
                "Highlights coursework and projects in the main column with a skills sidebar—ideal for CS, design, "
                "and builders who want proof before job titles."
            ),
            "role_label": "Student / new grad · Projects",
            "short_label": "Projects + skills rail",
            "features": [
                "Projects first",
                "Print-safe two column",
                "Sidebar skills",
                "Internships supported",
            ],
            "thumbnail_static": "img/resume_templates/new_grad_projects.svg",
            "selection_gradient": "from-indigo-100 to-indigo-50",
            "selection_title_class": "text-indigo-900",
            "gallery_section": "students",
            "featured": False,
            "featured_rank": 12,
            "is_active": True,
        },
        {
            "template_id": "new_grad_profile",
            "name": "Campus Profile",
            "description": (
                "Clear single-column flow: summary, education, then experience for internships, clubs, and "
                "volunteering—without looking like an executive layout."
            ),
            "role_label": "Student / new grad · Activities",
            "short_label": "Activities + education",
            "features": [
                "Single column",
                "Scannable sections",
                "Leadership-friendly",
                "PDF-safe layout",
            ],
            "thumbnail_static": "img/resume_templates/new_grad_profile.svg",
            "selection_gradient": "from-sky-100 to-slate-50",
            "selection_title_class": "text-sky-900",
            "gallery_section": "students",
            "featured": False,
            "featured_rank": 13,
            "is_active": True,
        },
    ]
    for row in rows:
        ResumeTemplate.objects.update_or_create(template_id=row["template_id"], defaults=row)


def unseed_student_templates(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    ResumeTemplate.objects.filter(
        template_id__in=("new_grad_ats", "new_grad_projects", "new_grad_profile")
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("resume_builder", "0010_executive_portrait_template_and_ranks"),
    ]

    operations = [
        migrations.AddField(
            model_name="resumetemplate",
            name="gallery_section",
            field=models.CharField(
                choices=[("general", "General"), ("students", "Students & recent grads")],
                db_index=True,
                default="general",
                max_length=32,
            ),
        ),
        migrations.RunPython(seed_student_templates, unseed_student_templates),
    ]
