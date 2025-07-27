from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Category, QuestionType, Question, Answer
from ai_service.interview_coach_manager import InterviewCoachManager
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
    category_name = request.GET.get('category') or request.GET.get('categorySelect') or 'General'
    print(f"[DEBUG] Loading questions for category: {category_name}")
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

@login_required
@csrf_exempt
def interview_coach_api(request):
    """
    API endpoint for interview coaching
    
    Handles requests from the chat dialog to provide personalized
    interview coaching based on specific questions.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question_id = data.get('question_id')
            user_message = data.get('user_message')
            
            if not question_id or not user_message:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required parameters: question_id and user_message'
                }, status=400)
            
            # Get question from database
            try:
                question = Question.objects.get(id=question_id)
            except Question.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Question not found'
                }, status=404)
            
            # Build question context
            question_context = f"""
            Question: {question.text}
            Category: {question.category.name}
            Type: {question.type.name}
            Sample Answer: {question.options.get('sample_answer', 'Not available')}
            """
            
            # Get coaching response
            try:
                coach_manager = InterviewCoachManager()
                result = coach_manager.get_coaching_response(
                    user=request.user,
                    question_context=question_context,
                    user_message=user_message
                )
                
                if result and result.get('response'):
                    return JsonResponse({
                        'success': True,
                        'response': result['response']
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'No response received from AI'
                    }, status=500)
                    
            except Exception as e:
                print(f"Error getting coaching response: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to get coaching response. Please try again.'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            print(f"Unexpected error in interview_coach_api: {e}")
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)
