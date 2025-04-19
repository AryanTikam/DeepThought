import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable


def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.7,
    )


def generate_explanation(contradiction):
    prompt = PromptTemplate.from_template("""
You are a lore master of a fantasy/sci-fi universe. Given this contradiction:

{contradiction}

Create an immersive, in-universe explanation that aligns with common narrative tropes like time travel, alternate timelines, clones, or hidden motives.
or if its impossible to reconcile them, say so
""")
    chain: Runnable = prompt | get_llm()
    return chain.invoke({"contradiction": contradiction["description"]})
