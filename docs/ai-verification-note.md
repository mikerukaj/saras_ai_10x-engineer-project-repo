# **MISTAKE FOUND No.1**
+ See "FIFTH PROMPT" in docs/prompt-log.md
### Output of "FIFTH PROMPT" in docs/prompt-log.md
> def delete_collection(collection_id: str):
>     if not storage.get_collection(collection_id):
>         raise HTTPException(status_code=404, detail="Collection not found")
> 
>     for prompt in storage.get_prompts_by_collection(collection_id):
>         storage.update_prompt(prompt.id, Prompt(
>             id=prompt.id,
>             title=prompt.title,
>             content=prompt.content,
>             description=prompt.description,
>             collection_id=None,
>             created_at=prompt.created_at,
>             updated_at=get_current_time()
>         ))
> 
>     storage.delete_collection(collection_id)
>     return None

+ Though the output was correct and achieved the result I was looking for, the tests were failing.
+ This made me realize that all the tests were written for the buggy code, something I overlooked and didnt account for.
+ Realizing this I found another section of the test that was commented out that needed to be implemented after fixing one of the bugs.
+ Had I not realized this, I could have been pushing code that still has bugs.

### How I found the error
+ Luckily, the tests was failing even though the output of the test was what I was looking for. This caused me to look into the tests_api.py file more thouroughly.
+ Moving forward, I will be sure to provide more constraints/instruction in my prompts to make sure the tests are accounted for.

# **MISTAKE FOUND No.2**
+ When reviewing the output of the "SIXTH PROMPT" in docs/prompt-log.md, I noticed that well all teh code looked correct, Clauded added a class to models.py, but did add the class it created to the imports of api.py
