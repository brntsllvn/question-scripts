role_prompt_template = "You are an expert in |{exam_long_name}|."

answer_prompt_template = """
### COMPLETION CONTEXT ###
Concerning |{exam_long_name}|
### COMPLETION TASK ###
Answer question |{question}| with these hints |{hints}| and the instructions:
- Show your step-by-step reasoning, in 5 separate steps.
- Use only characters from a standard American keyboard.
- Summarize very concisely why the answer is correct in while keeping math formulas as applicable.
- Summarize your answer in 4 words or less.
### COMPLETION FORMAT ###
|e1|[explanation step #1]|e2|[explanation step #2]|e3|[explanation step #3]|e4|[explanation step #4]|e5|[explanation step #5]|A|[answer]|AE|[concise answer summary explanation]|END|
### COMPLETION EXAMPLES ###
### EXAMPLE ###
|e1|Start with an initial guess: x = 1|e2|Use the iteration formula: x = (x + 2.3/x) / 2|e3|Perform the first iteration: x = (1 + 2.3/1) / 2 = 1.65|e4|Perform the second iteration: x = (1.65 + 2.3/1.65) / 2 = 1.521969|e5|Perform the third iteration: x = (1.521969 + 2.3/1.521969) / 2 = 1.517578|A|1.52|AE|Start with an initial guess, x = 1. Apply the iteration formula: x = (x + 2.3/x) / 2. Perform the first iteration, resulting in x = 1.65. Perform the second iteration, resulting in x = 1.521969. Perform the third iteration, resulting in x = 1.517578.|END|
### EXAMPLE ###
|e1|The document most likely associated with revenue is the income statement|e2|The income statement is also associated with expenses|e3|The income statement is not typically associated with cash flows|e4|Answer reached, no additional steps|e5|Answer reached, no additional steps|A|Income statement|AE|Income statement is linked to revenue and expenses, but not typically associated with cash flows.|END|
### EXAMPLE ###
|e1|The first phase is expansion|e2|The second phase is peak|e3|The third phase is contraction|e4|The fourth phase is trough|e5|Answer reached, no additional steps|A|Expansion, peak, contraction, trough|AE|The four phases of a business cycle are expansion, peak, contraction, and trough.|END|
### END COMPLETION EXAMPLES ###
"""

logical_match_prompt_template = """
### COMPLETION CONTEXT ###
Concerning exam |{exam_long_name}| and question |{question}|
### COMPLETION TASK ###
In the context of the exam and question, compare the hint |{hint}| and the answer |{answer}|, return |T| if logically equivalent (within two decimal places for numbers), or |F| if not.
### COMPLETION FORMAT ###
|T| or |F|
### COMPLETION EXAMPLES ###
### EXAMPLE ###
Hint: Income statement, Answer: Incm Stmt
|T|
### EXAMPLE ###
Hint: 3.03, Answer: 3.03111
|T|
### EXAMPLE ###
Hint: mean, Answer: average
|T|
### EXAMPLE ###
Hint: Income statement, Answer: Statement of cash flows
|F|
### EXAMPLE ###
Hint: 3.03, Answer: 3
|F|
### EXAMPLE ###
Hint: 'Yes', Answer: 'Yes, investors can lose more than their initial investment when trading on margin.'
|T|
### EXAMPLE ###
Hint: 'Risk management tool', Answer: 'Risk assessment tool'
|T|
### END COMPLETION EXAMPLES ###
"""

incorrect_answer_template = """
### COMPLETION CONTEXT ###
Concerning |{exam_long_name}|
### COMPLETION TASK ###
Generate 6 unique plausible and incorrect answers for the question |{question}| with about the same length as correct answer |{answer}|. Very concisely explain why each incorrect answer is incorrect.
### COMPLETION FORMAT ###
|i1|[incorrect answer #1]|i2|[incorrect answer #2]|i3|[incorrect answer #3]|i4|[incorrect answer #4]|i5|[incorrect answer #5]|i6|[incorrect answer #6]|ie1|[incorrect answer #1 explanation]|ie2|[incorrect answer #2 explanation]|ie3|[incorrect answer #3 explanation]|ie4|[incorrect answer #4 explanation]|ie5|[incorrect answer #5 explanation]|ie6|[incorrect answer #6 explanation]|END|
### COMPLETION EXAMPLES ###
### EXAMPLE ###
|i1|2.35%|i2|3.23%|i3|4.32%|i4|5.87%|i5|1.22%|i6|-1.4%|ie1|Yield-to-Maturity is 2.45%|ie2|This is not the correct yield to maturity|ie3|Yield-to-Maturity is 2.45%|ie4|yield to maturity is calculated differently|ie5|this answer is not correct because blah blah blah|ie6|This answer is incorrect because it divided when it should have multiplied|END|
### EXAMPLE ###
|i1|Management Discussion & Analysis|i2|Annual Report|i3|Unfunded Pension Liability|i4|some answer choice|i5|another bad choice|i6|some further incorrect answer|ie1|Management Discussion & Analysis is commentary provided by management, not a precise accounting of profit & loss|ie2|The annual report is delivered to shareholders to provide a general overview of the business, not a precise accounting of profit & loss|ie3|Unfunded pension liability is related but generally has little to do with profit & loss|ie4|the reason this answer is wrong|ie5|another explanation for incorrectness|ie6|the final reason this particular selection is wrong|END|
### END COMPLETION EXAMPLES ###
"""
