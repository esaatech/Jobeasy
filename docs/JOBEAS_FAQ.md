# JobEas — Comprehensive FAQ

Straight answers about how JobEas works, what you can do on the platform, and how your data is handled.

> **Note:** Features and pricing may vary by plan or region. If anything here differs from what you see after signing in at [jobeas.com](https://jobeas.com), trust your account and the live Pricing page.

---

## Getting Started

### What is JobEas?

JobEas is an online job-seeker platform that helps you create **resumes** and **cover letters**, prepare for **interviews**, track **job applications**, and use **AI** to tailor your materials to specific roles — all in one place. Paste a job posting and get a tailored resume, cover letter, and application workflow in minutes.

### Who is JobEas for?

JobEas is built primarily for **job seekers** — students, recent graduates, and professionals who want structured tools and AI-assisted writing to land interviews faster. Employers or partners should reach out through our official [Contact](https://jobeas.com/contact/) page.

### Do I need an account to use JobEas?

You can explore some features without signing in, but you'll need an **account** to save your work, sync across sessions, access paid features, and manage applications. If you start building a resume before creating an account, your progress can be saved after you register or log in.

### How do I create an account?

Go to **Register** (`/auth/register/`) and sign up with a username, email, and password. You'll be logged in automatically and can start using the dashboard right away. A welcome email is sent to confirm your account.

### How do I log in?

Use **Login** (`/auth/login/`) with your **username or email** (case-insensitive) and password. You can check "Remember me" to stay signed in on your device.

### I forgot my password. What do I do?

Use the **Forgot password** link on the login page (`/auth/password-reset/`). We'll email you a reset link. Follow it to set a new password, then log in as usual.

### Can I use JobEas on my phone or tablet?

Yes. JobEas is fully responsive and works on smartphones, tablets, and desktops through your web browser. No app download is required.

### Is JobEas available in other languages?

Parts of the site support **English, Spanish, and French** through client-side translations. FAQ and some content can also be served by language code (e.g. `?language=es` on the FAQ API).

---

## Plans & Pricing

### Is JobEas free?

Yes — JobEas offers a **Free** plan so you can get started at no cost. Paid plans (**Plus** and **Ultimate**) unlock advanced features like resume saving, upload, ATS optimization, cover letters, and the AI writing assistant. See the live **Pricing** page (`/subscriptions/pricing/`) for current options.

### What plans does JobEas offer?

| Plan | Price (USD, typical) | Highlights |
|------|----------------------|------------|
| **Free** | $0 | Basic resume creation, professional templates, interview preparation |
| **Plus** | $5/week or $15/month | Cover letters, resume saving & upload, ATS optimization, all templates, AI writing assistant |
| **Ultimate** | $10/week or $39.90/month | Everything in Plus + priority support, advanced analytics |

Exact prices and availability are shown on the Pricing page when you sign in.

### What's included in the Free plan?

- Basic resume creation with professional templates
- Interview preparation (practice questions and categories)
- Browse and explore the platform

### What's included in the Plus plan?

Everything in Free, plus:

- Cover letter generation
- Save and manage multiple resumes
- Upload existing resumes (PDF, DOC, DOCX)
- ATS optimization against job descriptions
- Access to all resume templates (including premium layouts)
- Enhanced AI cover letters
- AI Resume Writing Assistant (conversational chat)

### What's included in the Ultimate plan?

Everything in Plus, plus:

- Priority customer support
- Advanced analytics on your resume and application activity

### How do I upgrade my plan?

Visit **Pricing** (`/subscriptions/pricing/`), choose Plus or Ultimate, and complete checkout through **Stripe**. After payment, your account is upgraded immediately.

### How do I manage billing or cancel my subscription?

Go to **Settings → Billing** (`/settings/billing/`). From there you can view payment methods, invoices, toggle auto-renewal, and cancel your subscription. You can also cancel from `/subscriptions/cancel/`.

### Does JobEas store my payment card details?

No. Payments are processed securely by **Stripe**. JobEas does not store your full card number on our servers.

### Can I get a refund?

Refund policies depend on your purchase and region. Contact **support@jobeas.com** or use the Contact page with your account email and purchase details for help.

---

## Resumes

### How do I create a resume on JobEas?

1. Go to **Create Resume** (`/resume/create-resume/`)
2. Complete the wizard: Personal Info → Experience → Education → Skills → Additional sections → Summary
3. Choose a template from the gallery
4. Review, save, and download

You can also use the **AI Resume Assistant** (`/resume/ai-assistant/`) to build your resume through a conversational chat.

### What resume templates are available?

JobEas offers **13 professional templates**, grouped for different needs:

**Classic & contemporary:** Professional, Modern, Creative

**Leadership & portfolio:** Executive, Executive Portrait, Portfolio

**Creative studios:** ATS Plain, Creative Studio, Studio Folio, Creative Atelier

**Students & recent grads:** Campus ATS, Project Focus, Campus Profile

Browse all templates at `/resume/resume_templates/`.

### Which template should I choose?

- **Applying through online portals (ATS):** ATS Plain, Campus ATS, or Professional
- **Corporate or management roles:** Executive or Modern
- **Creative industries:** Creative, Creative Studio, or Creative Atelier
- **Students and new grads:** Campus ATS, Project Focus, or Campus Profile
- **Freelancers and designers:** Portfolio or Studio Folio

### Can I upload an existing resume instead of starting from scratch?

Yes — on the **Plus** plan or above. Go to **Upload Resume** (`/resume/upload-resume/`) and upload a **PDF, DOC, or DOCX** file. Our AI parses your document into structured fields you can edit in the wizard.

### Can I create multiple resumes for different jobs?

Yes. You can create, save, and manage multiple resumes tailored to different roles or industries from **My Resumes** (`/resume/my-resumes/`). Saving resumes requires a Plus plan or above.

### Can I add a profile photo to my resume?

Yes — on templates that support it (e.g. Executive Portrait, Creative Studio, Studio Folio, Creative Atelier). The wizard shows photo upload and extended contact fields only for compatible layouts.

### What export formats are supported?

You can download your resume as:

- **PDF** (primary format for applications)
- **HTML** (view or save in browser)
- **Word (.docx)**

Cover letters can be downloaded as **PDF**.

### Can I edit my resume after generating or saving it?

Yes. You can fully edit and customize every section — personal info, experience, education, skills, summary, and more — before downloading or applying.

### What is ATS optimization?

**ATS (Applicant Tracking System) optimization** analyzes your resume against a job description and suggests keyword improvements, formatting fixes, and an ATS compatibility score (0–100). This feature is available on Plus and Ultimate plans via the optimize flow (`/resume/optimize/`) and the dashboard job-application workflow.

---

## Cover Letters

### How do I create a cover letter?

Go to **Job Cover Letter** (`/coverletter/job-cover-letter/`), paste the job description, and optionally link your resume for context. JobEas generates a personalized cover letter you can edit before saving.

### Can I save and manage multiple cover letters?

Yes. All saved cover letters appear in **My Cover Letters** (`/coverletter/my-cover-letters/`). You can revisit, edit, and download any saved letter.

### Can I download my cover letter?

Yes. Download any saved cover letter as a **PDF** from the cover letter view page or via the download link (`/coverletter/download/<id>/`).

### Does the dashboard also generate cover letters?

Yes. When you run a **job application** from the dashboard (paste a job description + select a resume), JobEas generates both an optimized resume and a tailored cover letter in one workflow.

---

## AI Features

### How does JobEas use AI?

JobEas uses AI to **assist** you — not replace your judgment. AI can:

- Parse uploaded resumes into structured data
- Generate professional summaries
- Write and optimize cover letters
- Score resume–job fit before you apply
- Optimize resumes for ATS keyword matching
- Answer "Why should we hire you?" application questions
- Power the conversational **AI Resume Assistant**
- Coach you through interview practice

You should always **review and edit** AI output before submitting anything to an employer.

### Will AI write my entire resume for me?

AI can draft sections and suggest improvements, but **you decide what to keep**. Always verify accuracy — dates, employers, job titles, and skills must reflect your real experience. JobEas is not a law firm, career counselor, or human recruiter.

### What AI models does JobEas use?

JobEas uses a combination of **OpenAI (GPT)** and **Google Gemini**, depending on the task:

- **OpenAI:** Resume parsing, summary generation, cover letters, ATS optimization, AI chat assistant, interview coach
- **Gemini:** Resume–job fit evaluation, "Why should we hire you?" answers

Our admin **AI model catalog** also lists newer OpenAI (GPT-5.x) and **DeepSeek** models for future features; not every catalog entry is used in the live app yet. Models and prompts are configurable by our team and may be updated over time.

### What is the job fit score?

Before generating application materials, JobEas evaluates how well your resume matches a job description. You receive:

- An overall **fit score**
- A recommendation tier (Strong, Good, Moderate, Weak, or Poor Fit)
- Identified **gaps** and **strengths**
- Guidance on whether to proceed

If the fit is moderate or weak, the dashboard pauses for your review. You can still choose to **generate anyway**.

**Tip for accurate scores:** Job fit uses the **full text** from your uploaded resume file or parsed upload body when available, not only the shortened fields in the wizard. If you uploaded a PDF, keep that file on the resume record; re-upload after major edits so dates and titles match what employers see.

### What is the AI Resume Assistant?

The AI Resume Assistant is a **conversational chat** (`/resume/ai-assistant/`) that helps you build your resume step by step. Tell it about your experience in plain language and it saves structured data to your resume. Available on Plus and Ultimate plans.

### Can AI make mistakes?

Yes. AI output can contain errors, omissions, or biased language. Never paste passwords, government ID numbers, or highly sensitive personal data into AI chat or forms. Review everything before use.

### Is my data sent to AI providers?

When you use AI features, the content you provide (resume text, job descriptions, etc.) may be processed by our AI service providers to generate results. See our **Privacy Policy** (`/privacy/`) for details on data handling and third parties.

---

## Job Applications & Dashboard

### How does the dashboard job application flow work?

1. Go to **Dashboard** (`/dashboard/`)
2. Select a resume and paste the job description
3. JobEas evaluates your **fit** for the role
4. If fit is strong, it auto-generates an optimized resume + cover letter
5. If fit is moderate or weak, you review the evaluation first
6. Download documents or send your application via email

### Where do I track my applications?

View all applications at **Job Applications** (`/dashboard/job-applications/`). The list includes dashboard-generated applications and job-service requests in one unified view.

### What is "Why should we hire you?"

For some applications, employers ask a short answer to "Why should we hire you?" JobEas generates a tailored response (distinct from your cover letter) that you can review, edit, and download from the application detail page.

### Can I email my application directly from JobEas?

Yes. From a completed application, use **Compose Email** to send your resume and cover letter as attachments. You'll need to connect an email account first (Gmail, Yahoo, or custom SMTP).

### What is the automated job application service?

JobEas also offers a **job application service** (`/job-service/start/`) where you submit your preferences (job title, location, salary range, resume, contact details) and our team/system processes applications on your behalf. Track status at `/job-service/status/<uuid>/`.

### Can I browse job listings on JobEas?

Yes. Visit **Jobs** (`/job-service/jobs/`) to browse listings, view details, and apply.

### How do I set job search preferences?

Go to **Preferences** (`/job-service/preferences/`) to set remote work preference, notification frequency, and other job-search settings.

---

## Interview Preparation

### Does JobEas help with interview prep?

Yes. JobEas includes an **Interview Preparation** module with **89+ practice questions** across **53 categories** — including General, Leadership, Teamwork, Problem Solving, and more.

Access it at `/job-service/interview-prep/`.

### What types of interview questions are available?

- **Multiple choice**
- **True / false**
- **Essay / open-ended**

Multiple-choice questions are graded instantly in your browser. Sample answers are included for many questions.

### Is there an AI interview coach?

Yes. JobEas offers an **AI interview coach** API that provides guidance and feedback on interview responses. Access depends on your plan.

### Is interview prep free?

Interview preparation is included on the **Free** plan. Ultimate plan marketing also highlights interview prep alongside priority support and analytics.

---

## Email & Integrations

### Can I send job applications from my own email?

Yes. Connect your email account and compose applications directly from JobEas:

- **Gmail** — OAuth at `/email/auth/gmail/`
- **Yahoo** — OAuth at `/email/auth/yahoo/`
- **Custom SMTP** — configure at `/email/settings/`

### Where do I manage email settings?

Go to **Settings → Integrations** (`/settings/integrations/gmail/`) or **Email Settings** (`/email/settings/`). You can connect, disconnect, and manage sending accounts from there.

### Can I see my sent emails?

Yes. **Email History** (`/email/history/`) shows emails you've sent through JobEas.

### What transactional emails does JobEas send?

JobEas may send:

- Welcome email (on registration)
- Password reset
- Subscription confirmation, renewal reminders, and cancellation notices
- Account deletion confirmation

These are sent from **support@jobeas.com** (or the configured `FROM_EMAIL` address).

---

## Account & Settings

### How do I update my profile?

Go to **Settings → Profile** (`/settings/`) to update your name, email, and other account details.

### How do I change my password?

Go to **Settings → Security** to change your password while logged in. If you're locked out, use the password reset flow instead.

### How do I manage notification preferences?

Go to **Settings → Notifications** (`/settings/notifications/`) to toggle email notifications, desktop/browser alerts, and sound preferences.

### How do I delete my account?

Go to **Settings → Delete Account** (`/settings/delete-account/`). Account deletion is permanent and removes your stored data according to our retention policy. You'll receive a confirmation email.

---

## Privacy, Security & Data

### Is my data secure and private?

JobEas takes security seriously:

- Passwords are hashed using Django's authentication system
- Payment data is handled by Stripe (we never store full card numbers)
- Resume and account data are stored securely when you're logged in
- CSRF protection and session management are enforced

We do **not** sell your personal data. See our **Privacy Policy** (`/privacy/`) for full details.

### Do you store my resume?

If you save work while logged in, we store it so you can edit and download it later. You can delete resumes and your account at any time. Retention details are in the Privacy Policy.

### Do you share my data with third parties?

We use trusted service providers to operate JobEas — including **Stripe** (payments), **SendGrid** (email delivery), and **AI providers** (OpenAI, Google Gemini) for AI features. These providers process data on our behalf as described in the Privacy Policy. We do not sell your resume or personal information to employers or recruiters.

### What cookies does JobEas use?

JobEas uses cookies for session management, preferences, and analytics (e.g. Google Analytics). You can accept or decline non-essential cookies via the cookie banner. See the Privacy Policy for details.

### Can I request access to or deletion of my data?

Yes. Under applicable privacy laws, you may have rights to access, correct, delete, or export your data. Contact us at **support@jobeas.com** or through the Contact page with your request.

### What should I NOT paste into JobEas?

Do not paste **passwords**, **government ID numbers**, **Social Security numbers**, or other highly sensitive personal data into chat, forms, or AI features unless the product explicitly requires it.

---

## Support & Contact

### How do I get help?

- **Contact form:** [jobeas.com/contact](https://jobeas.com/contact/)
- **Email:** support@jobeas.com
- **AI Resume Assistant:** Available on Plus/Ultimate for resume-building help (not a substitute for human support)

Ultimate plan subscribers receive **priority support**.

### Is there live chat support?

JobEas has an **AI-powered resume chat assistant**, but there is no dedicated live human chat widget at this time. For human help, email support@jobeas.com or use the Contact form.

### Where can I learn about JobEas as a company?

Visit **About** (`/about/`) for company information and **Careers** (`/careers/`) for open positions.

### How do I subscribe to the newsletter?

Sign up via the newsletter form on the homepage or submit your email to the newsletter API. You can unsubscribe at any time.

---

## Blog & Resources

### Does JobEas have a blog?

Yes. Visit **Blog** (`/blog/`) for articles on job search, resume tips, interview advice, and career guidance. Posts are organized by category and include reading time estimates.

---

## Legal

### Where are the Terms and Privacy Policy?

- **Terms & Conditions:** `/terms/`
- **Privacy Policy:** `/privacy/`

These govern your legal relationship with JobEas. This FAQ is a general overview, not a contract.

### Can I use JobEas outputs anywhere?

Yes — your generated resumes and cover letters are yours to use. You are responsible for ensuring your final documents meet employer requirements and that you have rights to any content you submit (e.g. don't copy others' work).

### Is JobEas legal or career advice?

No. JobEas provides tools and AI-assisted suggestions. It is **not** a law firm, career counseling service, or recruiting agency. For high-stakes decisions, consider professional advice.

---

## Troubleshooting

### I started a resume before signing up. Is my work lost?

No. After you register or log in, JobEas can save your pending resume work via the post-auth flow (`/resume/create-after-auth/`).

### A feature is locked — how do I unlock it?

Some features require a **Plus** or **Ultimate** plan. When you try to access a gated feature, an upgrade dialog appears with a link to Pricing. Upgrade there to unlock immediately.

### My fit score is low. Should I still apply?

A low fit score means your current resume may not align well with the job requirements. Review the identified gaps, consider optimizing your resume, or choose "Generate anyway" if you still want to proceed. The score is guidance, not a guarantee.

### I'm having payment issues.

Ensure your card details are correct and try again. If problems persist, check **Settings → Billing** for invoice history or contact **support@jobeas.com** with your account email and a description of the issue.

### The site isn't loading properly on my device.

Try clearing your browser cache, using a modern browser (Chrome, Firefox, Safari, Edge), or switching devices. JobEas works on mobile browsers but some complex editor features are best on desktop.

---

*Last updated: May 2026. For the latest features and pricing, visit [jobeas.com](https://jobeas.com) after signing in.*
