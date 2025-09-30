from pydantic import BaseModel, Field
from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from llm_wrappers.deepseek_wrapper import DeepSeekChat


class RecipeSelection(BaseModel):
    breakfast:List[str]=Field(..., description="2-3 options for breakfast")
    lunch: List[str]=Field(..., description="2-3 options for lunch/dinner")
    
    
def select_recipes(pantry_items: str,all_translated_names:str, recipes:str, preferences:str) -> RecipeSelection:
    recipe_prompt=ChatPromptTemplate.from_messages([
        (
            "system","""
            You are a helpful chef AI.
            Using the pantry items below, current store discounts, and these retrieved recipes,
            suggest a couple of meal ideas: 1-2 for breakfast, and 1-2 for lunch/dinner.
            
            - Keep recipes simple and concise
            - Use pantry + discounted items if possible
            - Don't go overboard with explanations
            - No giant lists or stocking advice, just a handful of ideas

            """
        ),
        ("user", """
            You are a helpful chef AI.
            Using the pantry items below, current store discounts, and these retrieved recipes,
            suggest a couple of meal ideas: 1-2 for breakfast, and 1-2 for lunch/dinner.
            
            - Keep recipes simple and concise
            - Use pantry + discounted items if possible
            - Don't go overboard with explanations
            - No giant lists or stocking advice, just a handful of ideas

            Pantry items:
            {pantry_items}

            Current discounts:
            {discounts}
            
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
    print(f"Prompt to DeepSeek:\n{prompt}\n---")
    return 0