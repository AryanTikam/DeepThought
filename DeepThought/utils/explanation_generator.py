# utils/explanation_generator.py
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

def generate_explanation(contradiction, world_context=""):
    """Generate an in-universe explanation for a detected contradiction"""
    prompt = PromptTemplate.from_template("""
You are a lore master and narrative continuity expert for fictional universes. 
Given this contradiction in a fictional narrative:

{contradiction}

{world_context}

Please provide:
1. An immersive, in-universe explanation that could reconcile this contradiction using common narrative tropes like:
   - Time travel or temporal anomalies
   - Alternate timelines/universes
   - Clones, twins, or doppelgangers
   - Hidden identities or disguises
   - Magical/technological phenomena
   - Unreliable narrators or misunderstandings

2. A "behind the scenes" analysis of how significant this contradiction is and potential ways the author could address it with minimal disruption to established canon.

If it's genuinely impossible to reconcile within reasonable narrative conventions, explain why.
""")
    chain: Runnable = prompt | get_llm()
    
    return chain.invoke({
        "contradiction": contradiction["description"],
        "world_context": world_context
    })

def generate_speculative_boundaries(knowledge_graph):
    """Generate an analysis of what's firmly established vs. what's open to interpretation"""
    # Extract high-confidence and low-confidence facts
    firm_facts = []
    speculative_elements = []
    
    for entity_id, info in knowledge_graph.entity_info.items():
        if info["confidence"] > 0.8:
            firm_facts.append(f"{info['name']} ({info['type']})")
        elif info["confidence"] < 0.5:
            speculative_elements.append(f"{info['name']} ({info['type']})")
    
    prompt = PromptTemplate.from_template("""
As a narrative analyst for a fictional universe, examine these elements:

Firmly established facts:
{firm_facts}

Elements with unclear or ambiguous status:
{speculative_elements}

Please provide:
1. A brief analysis of what aspects of this fictional world are well-defined versus open to interpretation
2. Recommendations for areas where authors could expand the universe without contradicting established canon
3. Identification of potential narrative opportunities in the ambiguous areas
""")
    
    chain: Runnable = prompt | get_llm()
    
    return chain.invoke({
        "firm_facts": "\n".join(firm_facts),
        "speculative_elements": "\n".join(speculative_elements)
    })