from pydantic import BaseModel, Field
from typing import List, Optional
from langchain.prompts import ChatPromptTemplate
from llm_wrappers.deepseek_wrapper import DeepSeekChat
from langchain.chat_models import init_chat_model


class RecipeSelection(BaseModel):
    breakfast:List[str]=Field(..., description="2-3 options for breakfast")
    lunch: List[str]=Field(..., description="2-3 options for lunch/dinner")
    instructions: Optional[str]=Field(..., description="Concise cooking instructions for one of the lunch/dinner options if not from the retrieved recipes")
    custom:Optional[bool]=Field(False, description="Whether any of the suggestions are custom (not from retrieved recipes)")

class RecipeSelector:
    def __init__(self, model_name:str='gemini'):
        
        self.recipe_prompt=ChatPromptTemplate.from_messages([
        (
            "system","""
            You are a helpful chef AI.
            Using the retrieved recipes and user preferences,
            suggest a couple of meal ideas: 1-2 for breakfast, and 1-2 for lunch/dinner.
            
            - Keep recipes simple and concise
            - No explanations, just the suggestions.
            - No need to explain the reasoning
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
        if model_name=='gemini':
            self.ds=init_chat_model("gemini-2.5-flash", model_provider="google_genai")
        else:
            self.ds=DeepSeekChat()
        self.recipe_selector=self.ds.with_structured_output(RecipeSelection)
        
    
    def select_recipes(self,recipes:str, preferences:str) -> RecipeSelection:
        
        prompt=self.recipe_prompt.invoke({
            "preferences": preferences,
            "recipes": recipes
        })
        print("Prompting deepseek")
        result=self.recipe_selector.invoke(prompt)
        #print(f"Prompt to DeepSeek:\n{prompt}\n---")
        return result