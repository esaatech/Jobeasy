from django.shortcuts import render
from django.http import JsonResponse
from .models import Question, Category, QuestionType
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

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

def test_view(request):
    """Test view to render all question types"""
    questions = Question.objects.all().order_by('order')
    return render(request, 'question_answer/test.html', {'questions': questions})

@require_http_methods(["GET"])
def load_questions_by_category(request):
    """HTMX endpoint to load questions by category"""
    category_name = request.GET.get('category', 'General')
    
    try:
        # Get questions for the selected category
        questions = Question.objects.filter(
            category__name=category_name,
            type__name='Essay'  # Filter for essay questions (interview prep)
        ).order_by('order')
        
        if not questions.exists():
            return render(request, 'question_answer/partials/no_questions_found.html', {
                'category': category_name
            })
        
        return render(request, 'question_answer/partials/questions_list.html', {
            'questions': questions,
            'category': category_name
        })
        
    except Exception as e:
        return render(request, 'question_answer/partials/error.html', {
            'error': str(e)
        })

@csrf_exempt
def submit_answers(request):
    """Handle answer submission from the Q&A interface"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Process the submitted answers
            # This is a placeholder - implement actual answer processing
            return JsonResponse({'status': 'success', 'message': 'Answers submitted successfully'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
