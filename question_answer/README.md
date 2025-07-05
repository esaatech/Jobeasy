# Question & Answer App

This app provides a reusable system for rendering, grading, and managing questions and answers of various types (multiple choice, essay, true/false, etc.) for use in interview prep, quizzes, onboarding, and more.

## Features
- Supports multiple question types via template partials
- Instant grading for multiple choice and true/false in the browser
- Essay grading ready for AI backend integration
- **HTMX Integration:** Dynamic loading of questions by category with no page refresh
- **Interview Prep System:** Pre-loaded with 89 interview questions across 53 categories
- Extensible: add new question types by creating a new template and updating the JS if needed
- **User-specific or global questions:** If a question's `user` is null, it is global (available to all). If set, it is private to that user.
- **Category support:** Questions are grouped by category (e.g., "General", "Leadership", "Teamwork"). If no category is provided, a default category named **"General"** is automatically assigned.
- **Stepper navigation:** Only one question is shown at a time, with Next/Previous/Submit buttons. On the last question, Submit will grade and send answers to the backend endpoint.

## Models
- **Category**: Groups questions by subject, topic, or domain. If not specified, questions are assigned to a default "General" category.
- **QuestionType**: Defines the type of question and the template partial to use
- **Question**: Stores the question text, type, options, and order. Optionally linked to a user for private questions, and always linked to a category.
- **Answer**: Stores the user's answer, correctness, score, and submission time

## Templates
- Place question type partials in `question_answer/templates/question_answer/question_types/`
- Example partials: `multiple_choice.html`, `essay.html`, `true_false.html`
- Use `{% include 'question_answer/question_types/<type>.html' with question=question %}` to render
- **HTMX Partials:** Located in `question_answer/templates/question_answer/partials/` for dynamic content loading

## HTMX Integration
- **Dynamic Loading:** Questions load via HTMX without page refresh
- **Category Filtering:** Users can switch between categories using a dropdown
- **Default Loading:** "General" questions load automatically on page load
- **Error Handling:** Graceful error handling with user-friendly messages
- **Loading States:** Spinner indicators during content loading

### HTMX Endpoints
- `GET /qa/load-questions/?category=<category_name>` - Load questions by category
- `POST /qa/submit/` - Submit answers for grading (placeholder)

## JavaScript Grading & Navigation
- `static/question_answer/js/question_render.js` provides a `Grader` class for instant grading
- MCQ and True/False are graded instantly using the correct answer in a `data-correct` attribute
- Essay grading is a placeholder for now; connect to an AI backend for real feedback
- **Stepper navigation:** The JS renders one question at a time, with Next/Previous/Submit buttons. On submit, all answers are graded and sent to `/qa/submit/` (implement this endpoint as needed).

## Interview Prep Integration
- **Pre-loaded Data:** 89 interview questions imported from JSON
- **Categories:** 53 categories including General, Leadership, Teamwork, Problem Solving, etc.
- **Sample Answers:** Each question includes a sample answer for reference
- **Integration:** Accessible via `/job-service/interview-prep/` in the job_service app

## Example Usage
- **Test Page:** See `test.html` and the `/qa/test/` URL for a demo of all question types, stepper navigation, and instant grading
- **Interview Prep:** Visit `/job-service/interview-prep/` for the interview preparation interface
- **HTMX Demo:** The interview prep page demonstrates HTMX integration with category filtering

## Management Commands
- `python manage.py import_interview_prep` - Import interview questions from JSON file
- `python manage.py import_interview_prep --clear` - Clear existing questions before importing

## Extending
- To add a new question type, create a new template partial and update the `QuestionType` model
- Add grading logic to the JS if needed
- Add new categories as needed for your use case
- Extend HTMX functionality by adding new endpoints and partials

## Dependencies
- **HTMX:** Required for dynamic content loading (included in base.html)
- **Django:** Core framework
- **JSON:** For importing question data

---

**Maintained by:** Your Team 