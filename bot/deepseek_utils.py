from pydantic import BaseModel, Field
from typing import List
from langchain.prompts import ChatPromptTemplate


class RecipeSelection(BaseModel):
    breakfast:List[str]=Field(..., description="2-3 options for breakfast")
    lunch: List[str]=Field(..., description="2-3 options for lunch/dinner")
    
    
def select_recipes(pantry_items: str,all_translated_names:str, recipes:str, preferences:str) -> RecipeSelection:
    prompt = f"""
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
        {', '.join(all_translated_names)}

        Retrieved recipes:
        {recipes}
    """
    sentiment_prompt=ChatPromptTemplate.from_messages([
        (
            
        )