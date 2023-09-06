import asyncio
import aiohttp
import csv
import pandas as pd
import random
import string
import time

from prompt_utils.api_wrapper import (
    construct_body,
    execute_prompt
)

from prompt_utils.answer_prompt_templates import (
    role_prompt_template
)

from exam.utils import EXAMS

# GPT_MODEL = "gpt-3.5-turbo"
GPT_MODEL = "gpt-4"
GPT_TEMPERATURE = 1.0
# aiming for 150 questions since some fraction will not be solvable
ITERATIONS = 6
MAX_QUESTIONS_PER_COMPLETION = 10


"""
Edge cases...

TRUE/FALSE QUESTION -> "True or False: The Efficient Market Hypothesis (EMH) suggests that it is possible to consistently outperform the market."

Does the question reference the exam? 
- "How does the detection and prevention of money laundering relate to requirements outlined in the USA PATRIOT Act as it pertains to the FINRA Series 16 examination?"
- WRONG "Series 99 rules" <-- wtf. Example: "What are the requirements for customer verification under the provisions of Anti-Money Laundering (AML) regulations according to FINRA Series 99 rules?"

Does the question reference unprovided answers?
- "Which of the following..."

"""
question_prompt_template = """
### COMPLETION CONTEXT ###
Concerning {exam_long_name} and existing practice questions {existing_questions}
### COMPLETION TASK ###
Write {number_of_questions} new and unique, challenging, very concise 1-sentence practice questions from random sections in the {exam_long_name}. 
- Each question should be on a single line.
- Seperate each question with the following delimiter: |$|
Each question should have the following characteristics:
- conducive to a multiple-choice exam
- closed-ended
- ask for 1 thing
- have 1 answer
- not test number memorization
- not reference any answer choices
- use only characters from a standard American keyboard
- not refer to the test itself
### COMPLETION FORMAT ###
[question]|$|[question]|$|...|$|[question]
### COMPLETION EXAMPLES ###
### EXAMPLE ###
How does John's Gospel differ from the synoptic Gospels in its depiction of Jesus' dialogue with Pilate?|$|What does the yield curve depict in relation to bond interest rates and maturity periods?|$|How does the use of margin in futures trading affect the potential return and risk of an investment?|$|If a batter unintentionally bunts the ball into foul territory during a third strike, what is the ruling according to the MLB umpire rulebook?|$|What action must be taken by a character to stabilize another character that has reached 0 hit points?
### END COMPLETION EXAMPLES ###
"""

"""
question edge cases...

- "
"""


async def write_questions():
    input_tokens = 0
    output_tokens = 0
    questions_all_accumulated = []
    for exam_key in EXAMS.keys():
        questions_exam_accumulated = []
        questions_exam_raw_accumulated = []
        long_exam_name = EXAMS[exam_key]
        role = role_prompt_template.format(exam_long_name=long_exam_name)
        count = 0
        while count < ITERATIONS:
            questions_exam_raw_accumulated.extend([q.get('qText') for q in questions_exam_accumulated])
            question_prompt = question_prompt_template.format(
                exam_long_name=long_exam_name,
                existing_questions=questions_exam_raw_accumulated,
                number_of_questions=MAX_QUESTIONS_PER_COMPLETION
            )
            question_body = construct_body(GPT_MODEL, role, question_prompt, GPT_TEMPERATURE)
            question_response = None
            usage = None
            async with aiohttp.ClientSession() as session:
                question_response, usage = await execute_prompt(session, question_body)
                if question_response is None or usage is None:
                    break

            input_tokens = input_tokens + usage.get('prompt_tokens')
            output_tokens = output_tokens + usage.get('completion_tokens')
            print(f'{long_exam_name} - IN PROGRESS Input tokes - {input_tokens}')
            print(f'{long_exam_name} - IN PROGRESS Output tokens - {output_tokens}')

            questions_local_raw = question_response.split('|$|')
            questions_local = [s.replace("\n", " ").strip() for s in questions_local_raw]
            for question in questions_local:
                # edge case: trailing |$| creates lagging empty
                if len(question) > 0:
                    question_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                    question_data = pd.Series({
                        'exam_key': exam_key,
                        'question_id': question_id,
                        'question_text': question,
                        'question_generated': int(time.time()),
                        'question_solution_count': 0,

                    })
                    questions_exam_accumulated.append(question_data)
                    questions_all_accumulated.append(question_data)

            count = count + 1

        with open('questions_db.csv', 'a') as f:
            for question in questions_exam_accumulated:
                new_row = question.to_frame().T
                new_row.to_csv(f,
                               header=False,
                               index=False,
                               quoting=csv.QUOTE_ALL,
                               doublequote=True
                               )

    print(f'TOTAL Input tokes: {input_tokens}')
    print(f'TOTAL Output tokens: {output_tokens}')


asyncio.run(write_questions())
