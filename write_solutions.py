import asyncio
import aiohttp
import pandas as pd
import time
import csv
import re
import os

from dotenv import load_dotenv

from prompt_utils.api_wrapper import (
    construct_body,
    execute_prompt
)

from prompt_utils.answer_prompt_templates import (
    role_prompt_template,
    answer_prompt_template,
    logical_match_prompt_template,
    incorrect_answer_template
)

from exam.utils import EXAMS

load_dotenv()

PARALLEL_SOLVE = 13
PHP_ITERATION_LIMIT = 6
PHP_CORRECT_COUNT = 2
GPT_TEMPERATURE = 0.3  # some variation seems good for PHP?
# GPT_MODEL = "gpt-3.5-turbo"
GPT_MODEL = "gpt-4"


def make_file_if_does_not_exist(exam_key):
    filename = f'./solutions/{exam_key}.Question.csv'
    if not os.path.isfile(filename):
        headers = ['questionId', 'subjectId', 'questionText', 'optA', 'expA', 'optB', 'expB', 'optC', 'expC', 'optD', 'expD', 'optE',
                   'expE', 'optF', 'expF', 'correctAns', 'correctAnsExp', 'gTime', 'model', 'input_tokens', 'output_tokens', 'internalQuestionId']
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)


async def solve_questions():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for exam_key in EXAMS.keys():
            make_file_if_does_not_exist(exam_key)
            long_exam_name = EXAMS[exam_key]
            role = role_prompt_template.format(exam_long_name=long_exam_name)

            exam_questions_all = pd.read_csv('questions_db.csv')
            questions_needing_solution = exam_questions_all[exam_questions_all['exam_key'] == exam_key]
            exam_solutions_all = pd.read_csv(get_exam_file_name(exam_key))

            for _, row in questions_needing_solution.iterrows():
                question_id = row['internalQuestionId']
                solved = question_already_solved(question_id, exam_solutions_all)
                if solved:
                    continue
                tasks.append(write_solution(session, role, exam_key, long_exam_name, row['question_text'], question_id))

        for i in range(0, len(tasks), PARALLEL_SOLVE):
            batch = tasks[i:i+PARALLEL_SOLVE]
            start_time = time.time()
            await asyncio.gather(*batch)
            end_time = time.time()
            elapsed_time = end_time - start_time
            if elapsed_time < 65:
                await asyncio.sleep(65-elapsed_time)
            print(f'Batch {i//PARALLEL_SOLVE + 1} execution time: {int(elapsed_time)} seconds')
            print("break")


def get_exam_file_name(exam_key):
    return f'./solutions/{exam_key}.Question.csv'


def write_row(exam_key, new_row):
    filename = get_exam_file_name(exam_key)
    with open(filename, 'a') as f:
        new_row.to_csv(f, header=False, index=False, quoting=csv.QUOTE_ALL, doublequote=True)


async def run_php_question_answer(session, role, exam_key, long_exam_name, question_text, question_id):
    print(f'{exam_key} - {question_id} - Running PHP on question')
    question_input_tokens = 0
    question_output_tokens = 0
    php_iteration_count = 0
    php_correct_response_count = 0
    php_hints = []
    php_correct_answer = {}
    while php_correct_response_count < PHP_CORRECT_COUNT and php_iteration_count < PHP_ITERATION_LIMIT:
        answer_prompt = answer_prompt_template.format(
            exam_long_name=long_exam_name,
            question=question_text,
            hints=php_hints)
        answer_body = construct_body(GPT_MODEL, role, answer_prompt, GPT_TEMPERATURE)
        answer_completion, usage = await execute_prompt(session, answer_body)
        if answer_completion is None or usage is None:
            print(f'{exam_key} - {question_id} - Missing answer completion')
            php_iteration_count = php_iteration_count + 1
            continue

        question_input_tokens = usage.get('prompt_tokens')
        question_output_tokens = usage.get('completion_tokens')

        answer_completion_pattern = r"\|e1\|(.*?)\|e2\|(.*?)\|e3\|(.*?)\|e4\|(.*?)\|e5\|(.*?)\|A\|(.*?)\|AE\|(.*?)(\|END\|)?$"
        answer_completion_matches = re.match(answer_completion_pattern, answer_completion)
        if answer_completion_matches is None:
            print(f'{exam_key} - {question_id} - Malformed answer completion: {answer_completion}')
            php_iteration_count = php_iteration_count + 1
            continue
        answer_completion = answer_completion_matches.group(6)
        answer_explanation_completion = answer_completion_matches.group(7)
        correct_answer_completion = {
            "completion": answer_completion,
            "explanation": answer_explanation_completion
        }

        if len(php_hints) > 0:
            latest_hint = php_hints[-1]
            match_prompt = logical_match_prompt_template.format(
                exam_long_name=long_exam_name,
                question=question_text,
                hint=latest_hint,
                answer=correct_answer_completion.get("completion")
            )
            match_body = construct_body(GPT_MODEL, role, match_prompt, GPT_TEMPERATURE)
            logical_match_completion, usage = await execute_prompt(session, match_body)
            if logical_match_completion is None or usage is None:
                print(f'{exam_key} - {question_id} - Missing logical match completion')
            else:
                question_input_tokens = question_input_tokens + usage.get('prompt_tokens')
                question_output_tokens = question_output_tokens + usage.get('completion_tokens')

                logical_match_completion_pattern = r"\|(T|True|true|t)\|$"
                logical_match_completion_match = re.match(
                    logical_match_completion_pattern, logical_match_completion.strip())
                if logical_match_completion_match:
                    php_correct_response_count = php_correct_response_count + 1
                else:
                    print(
                        f'{exam_key} - {question_id} - No match: {correct_answer_completion.get("completion")}, latest hint: {latest_hint}, all hints: {php_hints}')
                    php_correct_response_count = 0

            if php_correct_response_count == PHP_CORRECT_COUNT:
                php_correct_answer = correct_answer_completion
                break

        php_hints.append(correct_answer_completion.get("completion"))
        php_iteration_count = php_iteration_count + 1
    if php_correct_answer.get('completion'):
        print(f'{exam_key} - {question_id} - Found correct answer')
        return php_correct_answer, question_input_tokens, question_output_tokens
    else:
        return None, None, None


async def get_incorrect_answers(session, role, exam_key, long_exam_name, question_text, correct_answer, question_id):
    print(f'{exam_key} - {question_id} - Getting incorrect answers')
    incorrect_answer_prompt = incorrect_answer_template.format(
        exam_long_name=long_exam_name,
        answer=correct_answer.get("completion"),
        question=question_text
    )
    incorrect_answer_body = construct_body(GPT_MODEL, role, incorrect_answer_prompt, GPT_TEMPERATURE)
    incorrect_answers_completion, usage = await execute_prompt(session, incorrect_answer_body)
    if incorrect_answers_completion is None or usage is None:
        print(f'{exam_key} - {question_id} - Missing incorrect answer response')
        return None, None, None

    input_tokens = usage.get('prompt_tokens')
    output_tokens = usage.get('completion_tokens')

    incorrect_answer_completion_pattern = r"\|i1\|(.*?)\|i2\|(.*?)\|i3\|(.*?)\|i4\|(.*?)\|i5\|(.*?)\|i6\|(.*?)\|ie1\|(.*?)\|ie2\|(.*?)\|ie3\|(.*?)\|ie4\|(.*?)\|ie5\|(.*?)\|ie6\|(.*?)(\|END\|)?$"
    incorrect_answer_completion_match = re.match(
        incorrect_answer_completion_pattern, incorrect_answers_completion)
    if incorrect_answer_completion_match is None:
        print(f'{exam_key} - {question_id} - Missing incorrect answer completion: {incorrect_answers_completion}')
        return None, None, None
    incorrect_answers = []
    incorrect_answer_iterator = 1
    number_of_incorrect_answers = 6
    while incorrect_answer_iterator <= number_of_incorrect_answers:
        incorrect_answer = {
            "completion": incorrect_answer_completion_match.group(incorrect_answer_iterator),
            "explanation": incorrect_answer_completion_match.group(incorrect_answer_iterator+6),
        }
        incorrect_answers.append(incorrect_answer)
        incorrect_answer_iterator = incorrect_answer_iterator + 1
    if len(incorrect_answers) == number_of_incorrect_answers:
        return incorrect_answers, input_tokens, output_tokens
    else:
        return None, None, None


def question_already_solved(question_internal_id, exam_solutions_all):
    question_already_solved = exam_solutions_all[exam_solutions_all['internalQuestionId']
                                                 == question_internal_id]
    return len(question_already_solved) > 0


async def write_solution(session, role, exam_key, long_exam_name, question_text, question_id):
    correct_answer, correct_answer_input_tokens, correct_answer_output_tokens = \
        await run_php_question_answer(session, role, exam_key, long_exam_name, question_text, question_id)
    if correct_answer is None or correct_answer_input_tokens is None or correct_answer_output_tokens is None:
        print(f'{exam_key} - {question_id} - No solution found')
        return

    incorrect_answers, incorrect_answer_input_tokens, incorrect_answer_output_tokens = \
        await get_incorrect_answers(session, role, exam_key, long_exam_name, question_text, correct_answer, question_id)
    if incorrect_answers is None or incorrect_answer_input_tokens is None or incorrect_answer_output_tokens is None:
        print(f'{exam_key} - {question_id} - Error when generating incorrect answers')
        return

    data = pd.Series({
        'questionId': '',  # placeholder
        'subjectId': '',  # placeholder
        'questionText': question_text,
        'optA': incorrect_answers[0].get("completion"),
        'expA': incorrect_answers[0].get("explanation"),
        'optB': incorrect_answers[1].get("completion"),
        'expB': incorrect_answers[1].get("explanation"),
        'optC': incorrect_answers[2].get("completion"),
        'expC': incorrect_answers[2].get("explanation"),
        'optD': incorrect_answers[3].get("completion"),
        'expD': incorrect_answers[3].get("explanation"),
        'optE': incorrect_answers[4].get("completion"),
        'expE': incorrect_answers[4].get("explanation"),
        'optF': incorrect_answers[5].get("completion"),
        'expF': incorrect_answers[5].get("explanation"),
        'correctAns': correct_answer.get("completion"),
        'correctAnsExp': correct_answer.get("explanation"),
        'gTime': int(time.time()),
        'model': GPT_MODEL,
        'input_tokens': correct_answer_input_tokens + incorrect_answer_input_tokens,
        'output_tokens': correct_answer_output_tokens + incorrect_answer_output_tokens,
        'internalQuestionId': question_id
    })
    print(data.to_string(), '\n')

    new_row = data.to_frame().T
    write_row(exam_key, new_row)

asyncio.run(solve_questions())
