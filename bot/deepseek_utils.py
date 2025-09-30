from pydantic import BaseModel, Field
from typing import List, Optional
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from llm_wrappers.deepseek_wrapper import DeepSeekChat


class RecipeSelection(BaseModel):
    breakfast:List[str]=Field(..., description="2-3 options for breakfast")
    lunch: List[str]=Field(..., description="2-3 options for lunch/dinner")
    instructions: Optional[str]=Field(..., description="Concise cooking instructions for one of the lunch/dinner options if not from the retrieved recipes")
    cutom:Optional[bool]=Field(False, description="Whether any of the suggestions are custom (not from retrieved recipes)")
    
    
def select_recipes(recipes:str, preferences:str) -> RecipeSelection:
    recipe_prompt=ChatPromptTemplate.from_messages([
        (
            "system","""
            You are a helpful chef AI.
            Using the pantry items provided by the user, current store discounts, and these retrieved recipes,
            suggest a couple of meal ideas: 1-2 for breakfast, and 1-2 for lunch/dinner.
            
            - Keep recipes simple and concise
            - Use pantry + discounted items if possible
            - Don't go overboard with explanations
            - No giant lists or stocking advice, just a handful of ideas
            - If none of the provided recipes are suitable, just suggest simple ideas based on pantry + discounts
            - If suggesting a lunch/dinner option not from the retrieved recipes, provide concise cooking instructions

            """
        ),
        ("user", """
            
            Preferences:
            {preferences}

            Retrieved recipes:
            {recipes}
        """)
        ])
    ds=DeepSeekChat()
    recipe_selector=ds.with_structured_output(RecipeSelection)
    prompt=recipe_prompt.invoke({
        "pantry_items": pantry_items,
        "discounts": ", ".join(all_translated_names),
        "preferences": preferences,
        "recipes": recipes
    })
    print(f"Prompting deepseek)")
    result=recipe_selector.invoke(prompt)
    #print(f"Prompt to DeepSeek:\n{prompt}\n---")
    return result