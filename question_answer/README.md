# Question & Answer App

This app provides a reusable system for rendering, grading, and managing questions and answers of various types (multiple choice, essay, true/false, etc.) for use in interview prep, quizzes, onboarding, and more.

## Features
- Supports multiple question types via template partials
- Instant grading for multiple choice and true/false in the browser
- Essay grading ready for AI backend integration
- Extensible: add new question types by creating a new template and updating the JS if needed
- **User-specific or global questions:** If a question's `user` is null, it is global (available to all). If set, it is private to that user.
- **Stepper navigation:** Only one question is shown at a time, with Next/Previous/Submit buttons. On the last question, Submit will grade and send answers to the backend endpoint.

## Models
- **QuestionType**: Defines the type of question and the template partial to use
- **Question**: Stores the question text, type, options, and order. Optionally linked to a user for private questions.
- **Answer**: Stores the user's answer, correctness, score, and submission time

## Templates
- Place question type partials in `question_answer/templates/question_answer/question_types/`
- Example partials: `multiple_choice.html`, `essay.html`, `true_false.html`
- Use `{% include 'question_answer/question_types/<type>.html' with question=question %}` to render

## JavaScript Grading & Navigation
- `static/question_answer/js/question_render.js` provides a `Grader` class for instant grading
- MCQ and True/False are graded instantly using the correct answer in a `data-correct` attribute
- Essay grading is a placeholder for now; connect to an AI backend for real feedback
- **Stepper navigation:** The JS renders one question at a time, with Next/Previous/Submit buttons. On submit, all answers are graded and sent to `/qa/submit/` (implement this endpoint as needed).

## Example Usage
See `test.html` and the `/qa/test/` URL for a demo of all question types, stepper navigation, and instant grading.

## Extending
- To add a new question type, create a new template partial and update the `QuestionType` model
- Add grading logic to the JS if needed

---

**Maintained by:** Your Team 