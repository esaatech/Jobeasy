// question_render.js
// Grader class for instant and AI grading

class Grader {
    static gradeMCQ(userAnswer, correctAnswer) {
        return userAnswer === correctAnswer;
    }
    static gradeTrueFalse(userAnswer, correctAnswer) {
        return userAnswer === correctAnswer;
    }
    static async gradeEssay(userAnswer, correctAnswer) {
        // Placeholder: In production, send to backend/AI for grading
        const keywords = correctAnswer.split(' ');
        let found = 0;
        for (let word of keywords) {
            if (userAnswer.toLowerCase().includes(word.toLowerCase())) found++;
        }
        const isCorrect = found > 2; // crude check
        let feedback = isCorrect ? 'Good answer!' : 'Try to include more details from the expected answer.';
        return { isCorrect, feedback };
    }
}

function renderQuestion(question, index, total) {
    const container = document.getElementById('qa-question-container');
    let html = '';
    // Render the correct partial for the question type
    if (question.type === 'multiple_choice') {
        html += `<div class="mb-4"><div class="font-medium mb-2">${question.text}</div><div class="space-y-2">`;
        question.options.forEach((option, i) => {
            html += `<label class="flex items-center space-x-2"><input type="radio" name="question_${question.id}" value="${option}" class="form-radio text-blue-600"${i === 0 ? ` data-correct=\"${question.correct_answer}\"` : ''}><span>${option}</span></label>`;
        });
        html += `</div></div>`;
    } else if (question.type === 'essay') {
        html += `<div class="mb-4"><div class="font-medium mb-2">${question.text}</div><textarea name="question_${question.id}" rows="5" class="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Type your answer..." data-correct="${question.correct_answer}"></textarea></div>`;
    } else if (question.type === 'true_false') {
        html += `<div class="mb-4"><div class="font-medium mb-2">${question.text}</div><div class="flex space-x-4"><label class="flex items-center space-x-2"><input type="radio" name="question_${question.id}" value="True" class="form-radio text-blue-600" data-correct="${question.correct_answer}"><span>True</span></label><label class="flex items-center space-x-2"><input type="radio" name="question_${question.id}" value="False" class="form-radio text-blue-600"><span>False</span></label></div></div>`;
    }
    html += `<div class="text-sm text-gray-500 mt-2">Question ${index + 1} of ${total}</div>`;
    container.innerHTML = html;
}

function showNavButtons(index, total) {
    document.getElementById('qa-prev-btn').style.display = index === 0 ? 'none' : '';
    document.getElementById('qa-next-btn').style.display = (index < total - 1) ? '' : 'none';
    document.getElementById('qa-submit-btn').style.display = (index === total - 1) ? '' : 'none';
}

function collectAnswers(questions) {
    const answers = [];
    questions.forEach(q => {
        let val = '';
        if (q.type === 'essay') {
            const textarea = document.querySelector(`textarea[name="question_${q.id}"]`);
            val = textarea ? textarea.value : '';
        } else {
            const input = document.querySelector(`input[name="question_${q.id}"]:checked`);
            val = input ? input.value : '';
        }
        answers.push({ id: q.id, type: q.type, answer: val });
    });
    return answers;
}

document.addEventListener('DOMContentLoaded', function() {
    const questions = window.qaQuestions;
    const total = window.qaTotalQuestions;
    let current = 0;
    renderQuestion(questions[current], current, total);
    showNavButtons(current, total);

    document.getElementById('qa-next-btn').onclick = function() {
        if (current < total - 1) {
            current++;
            renderQuestion(questions[current], current, total);
            showNavButtons(current, total);
        }
    };
    document.getElementById('qa-prev-btn').onclick = function() {
        if (current > 0) {
            current--;
            renderQuestion(questions[current], current, total);
            showNavButtons(current, total);
        }
    };
    document.getElementById('qa-test-form').onsubmit = async function(e) {
        e.preventDefault();
        // Collect all answers
        const answers = collectAnswers(questions);
        // Grade all answers
        let results = [];
        for (let i = 0; i < questions.length; i++) {
            const q = questions[i];
            const a = answers[i].answer;
            let result = { id: q.id, type: q.type, correct: false, feedback: '' };
            if (q.type === 'multiple_choice') {
                result.correct = Grader.gradeMCQ(a, q.correct_answer);
            } else if (q.type === 'true_false') {
                result.correct = Grader.gradeTrueFalse(a, q.correct_answer);
            } else if (q.type === 'essay') {
                const r = await Grader.gradeEssay(a, q.correct_answer);
                result.correct = r.isCorrect;
                result.feedback = r.feedback;
            }
            results.push(result);
        }
        // Show results summary
        let summary = '<div class="mt-6 p-4 bg-gray-50 rounded"><h2 class="font-bold mb-2">Results</h2>';
        results.forEach((r, i) => {
            summary += `<div class="mb-2">Q${i + 1}: ${r.correct ? '<span class=\'text-green-600\'>Correct</span>' : '<span class=\'text-red-600\'>Incorrect</span>'}`;
            if (r.feedback) summary += ` <span class="text-gray-500">(${r.feedback})</span>`;
            summary += '</div>';
        });
        summary += '</div>';
        document.getElementById('qa-question-container').innerHTML = summary;
        document.querySelector('.flex.justify-between.mt-4').style.display = 'none';
        // Placeholder: send answers to backend endpoint
        fetch('/qa/submit/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value },
            body: JSON.stringify({ answers })
        });
    };
});
