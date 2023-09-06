blog_prompt_template = """
### COMPLETION CONTEXT ###
This article concerns the {exam_full_name} administered by {admin}
### COMPLETION SOURCE MATERIAL ###
{source_material}
### COMPLETION TASK ###
Write a {word_count}-word article of the style {article_style} with the goal {goal}.
### COMPLETION INSTRUCTIONS ###
- Address the goal early in the article and answer it specifically (and numerically, if relevant)
- Refer to ### COMPLETION SOURCE MATERIAL ### extensvely (exclusively, if possible) to construct your completion. Provide several citations and quotations from ### COMPLETION SOURCE MATERIAL ###
- Use active voice. The tone of the article should be {tone}
- Use brief headings, short paragraphs, short sentences, and very simple words, use 1-2 lists to organize info
- The audience for the article is {audience}. Refer to the audience using third-person pronouns
- Add the following keywords to the article: {keywords}
- Format your completion using the MARKDOWN language. EXAMPLES ## Heading level 2, ### Heading level 3, **bold text**, *italicized text*, > a great block quote, link [Duck Duck Go](https://duckduckgo.com)
"""
