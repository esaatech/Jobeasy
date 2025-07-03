from django.shortcuts import render

# Create your views here.

def test_questions(request):
    questions = [
        {
            'id': 1,
            'type': 'multiple_choice',
            'text': 'What is the capital of France?',
            'options': ['Paris', 'London', 'Berlin', 'Madrid'],
            'correct_answer': 'Paris',
        },
        {
            'id': 2,
            'type': 'essay',
            'text': 'Describe your greatest achievement.',
            'correct_answer': 'A detailed description of a significant accomplishment that demonstrates skills and impact.'
        },
        {
            'id': 3,
            'type': 'true_false',
            'text': 'The sky is blue.',
            'correct_answer': 'True',
        },
    ]
    return render(request, 'question_answer/test.html', {
        'questions': questions,
        'total_questions': len(questions),
    })
