from flask import Flask, render_template, request, redirect, session, url_for
from model import predict
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management
DELAY = 3000  # Delay in milliseconds

base_path = "https://github.com/pranayarishi/adhd-predictive-analysis/blob/main/demo/static/"
suffix = ".JPG?raw=True"

# Trials data
quiz_questions = [
    {
        'question_image': base_path+'question1'+suffix,
        'options': [
            {'image': base_path+'option1_1'+suffix},
            {'image': base_path+'option1_2'+suffix},
            {'image': base_path+'option1_3'+suffix},
            {'image': base_path+'option1_4'+suffix}
        ],
        'correct_option_index': 1
    },
    {
        'question_image': base_path+'question2'+suffix,
        'options': [
            {'image': base_path+'option2_1'+suffix},
            {'image': base_path+'option2_2'+suffix},
            {'image': base_path+'option2_3'+suffix},
            {'image': base_path+'option2_4'+suffix}
        ],
        'correct_option_index': 2
    },
]

@app.route('/quiz', methods=['POST'])
def quiz():
    if request.method == 'POST':
        session['age'] = int(request.form['age'])  # Convert age to integer
        session['handedness'] = request.form['handedness']
        session['sex'] = request.form['sex']
        session['quiz_started'] = True
        session['question_index'] = 0
        session['start_time'] = time.time()
        session['chosen_options'] = {}  # Initialize chosen_options dictionary
        return redirect(url_for('index', page='question'))

@app.route('/question', methods=['POST'])
def question():
    if request.method == 'POST':
        question_index = session.get('question_index', 0)
        chosen_option = int(request.form['option'])  # Convert option to integer
        session['chosen_options'][question_index] = chosen_option
        session['chosen_options'] = {int(k): int(v) for k, v in session['chosen_options'].items()}
        session['question_index'] = int(session['question_index']) + 1  # Ensure question_index is an integer
        session[f'question_{question_index}_end_time'] = time.time()  # Store end time
        return redirect(url_for('index', page='question'))

@app.route('/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 'index')

    if page == 'question':
        if 'quiz_started' not in session or not session['quiz_started']:
            return redirect(url_for('index'))

        question_index = session.get('question_index', 0)
        if question_index >= len(quiz_questions):
            return redirect(url_for('index', page='result'))

        question = quiz_questions[question_index]
        session['current_question'] = question_index

        session[f'question_{question_index}_start_time'] = time.time()

        # Preprocess options with indices
        options_with_indices = [(index, option) for index, option in enumerate(question['options'])]

        return render_template('question.html', question=question, question_index=question_index, options_with_indices=options_with_indices, delay=DELAY)

    elif page == 'result':
        if 'quiz_started' not in session or not session['quiz_started']:
            return redirect(url_for('index'))

        session['quiz_started'] = False
        session['chosen_options'] = {int(k): int(v) for k, v in session['chosen_options'].items()}

        # Calculate total time taken
        end_time = time.time()
        total_time = round(end_time - session['start_time'], 2)

        # Calculate reaction times for each question
        reaction_times = []
        for i in range(len(quiz_questions)):
            start_time = session.get(f'question_{i}_start_time', session['start_time'])
            end_time = session.get(f'question_{i}_end_time', start_time)  # Use start_time as default end time
            reaction_time = end_time - start_time - 2 * DELAY / 1000  # Subtract 2 * DELAY to account for the delay in the question page

            chosen_option = session['chosen_options'].get(i, -1)
            correct_option_index = quiz_questions[i]['correct_option_index']
            reaction_times.append({'index': i + 1, 'time': round(reaction_time, 2), 'chosen_option': chosen_option, 'correct_option': correct_option_index, 'accurate': chosen_option == correct_option_index})

        return render_template('result.html', age=session['age'], handedness=session['handedness'].capitalize(), sex=session['sex'].capitalize(), reaction_times=reaction_times, total_time=total_time, adhd=predict(session['age'], session['handedness'], session['sex'], reaction_times))

    # Default to rendering the index page
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)