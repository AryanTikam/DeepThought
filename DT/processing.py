# processing.py
import os
import json
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.docstore.document import Document
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")

MODEL_NAME = "gemini-1.5-flash-latest" # Using the latest available Flash model
CHUNK_SIZE = 2000 # Adjust based on typical document structure and context window needs
CHUNK_OVERLAP = 200
SIMILARITY_K = 5 # Number of relevant chunks to retrieve for context

# --- Initialize Langchain Components ---
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY) # Standard embedding model
llm = ChatGoogleGenerativeAI(model=MODEL_NAME, google_api_key=API_KEY, temperature=0.3) # Lower temp for more factual extraction

# --- Prompt Templates ---

# 1. Knowledge Graph Extraction
KG_PROMPT_TEMPLATE = """
Based *only* on the provided text context, extract entities and their relationships to build a knowledge graph.
Identify entities like characters, locations, organizations, key objects, rules, cultural elements, and significant events.
Specify the relationships between them (e.g., 'located_in', 'member_of', 'interacted_with', 'rule_applies_to', 'created_by').

Format the output strictly as a JSON object with two keys: "nodes" and "edges".
- "nodes": A list of objects, each with 'id' (unique name), 'type' (e.g., 'Character', 'Location', 'Rule'), and 'description' (brief description from text).
- "edges": A list of objects, each with 'source' (id of source node), 'target' (id of target node), and 'relationship' (label of the relationship).

For *each* node and edge, add a 'confidence' score (a float between 0.0 and 1.0) indicating your certainty based *solely* on the provided text. A higher score means higher confidence. If unsure, assign a lower score. Do not invent information.

Example Node: {{ "id": "Gandalf", "type": "Character", "description": "A wizard who guides the fellowship.", "confidence": 0.95 }}
Example Edge: {{ "source": "Frodo Baggins", "target": "The Shire", "relationship": "lives_in", "confidence": 0.98 }}

Strictly adhere to the JSON format. Do not include any explanations outside the JSON structure.

Context:
{context}

JSON Output:
"""
KG_PROMPT = PromptTemplate(template=KG_PROMPT_TEMPLATE, input_variables=["context"])
kg_chain = LLMChain(llm=llm, prompt=KG_PROMPT)

# 2. Contradiction Detection
CONTRADICTION_PROMPT_TEMPLATE = """
Analyze the provided text context for internal inconsistencies or contradictions related to character actions, timelines, established rules, object properties, or location descriptions.

List any potential contradictions you find. For each contradiction:
1. Briefly describe the contradiction.
2. Quote or reference the conflicting statements/parts from the text.
3. Provide a 'confidence' score (float 0.0 to 1.0) indicating how likely this is a *genuine* contradiction based *only* on the text, rather than ambiguity or lack of detail. Higher score = more certain contradiction.

Format the output strictly as a JSON list of objects. Each object should have 'description', 'conflicting_statements' (a list of strings), and 'confidence'.

Example:
[
  {{
    "description": "Character A is stated to be in Location X and Location Y at the same time.",
    "conflicting_statements": ["'Character A arrived at Location X on Tuesday.'", "'On Tuesday morning, Character A was overseeing work at Location Y.'"],
    "confidence": 0.85
  }}
]

If no contradictions are found, return an empty list: [].
Strictly adhere to the JSON format. Do not include any explanations outside the JSON structure.

Context:
{context}

JSON Contradiction List:
"""
CONTRADICTION_PROMPT = PromptTemplate(template=CONTRADICTION_PROMPT_TEMPLATE, input_variables=["context"])
contradiction_chain = LLMChain(llm=llm, prompt=CONTRADICTION_PROMPT)

# 3. Speculation Boundary Identification
SPECULATION_PROMPT_TEMPLATE = """
Analyze the provided text context to differentiate between firmly established facts and elements that are undefined, ambiguous, speculative, or open to interpretation.

List key statements or elements from the text and categorize them.
For each item:
1. State the 'element' (the fact, rule, event, description, etc.).
2. Categorize it as 'Fact' (explicitly stated, unambiguous) or 'Speculation/Ambiguity' (implied, vague, potentially contradictory later, requires interpretation).
3. Provide a 'confidence' score (float 0.0 to 1.0) for your categorization based *only* on the provided text. Higher score = more certain about the categorization.

Format the output strictly as a JSON list of objects. Each object should have 'element', 'category' ('Fact' or 'Speculation/Ambiguity'), and 'confidence'.

Example:
[
  {{ "element": "The capital city is named 'Metropolis'.", "category": "Fact", "confidence": 1.0 }},
  {{ "element": "Character B's motives for helping Character C.", "category": "Speculation/Ambiguity", "confidence": 0.9 }},
  {{ "element": "The exact power level of the ancient artifact.", "category": "Speculation/Ambiguity", "confidence": 0.95 }}
]

Strictly adhere to the JSON format. Do not include any explanations outside the JSON structure.

Context:
{context}

JSON Speculation List:
"""
SPECULATION_PROMPT = PromptTemplate(template=SPECULATION_PROMPT_TEMPLATE, input_variables=["context"])
speculation_chain = LLMChain(llm=llm, prompt=SPECULATION_PROMPT)

# --- Core Processing Function ---

def analyze_text(text: str) -> dict:
    """
    Analyzes the input text to extract knowledge graph, contradictions, and speculation boundaries.

    Args:
        text: The fictional text content.

    Returns:
        A dictionary containing the analysis results.
    """
    if not text:
        return {"error": "Input text is empty."}

    try:
        # 1. Split text into manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        docs = [Document(page_content=chunk) for chunk in text_splitter.split_text(text)]
        if not docs:
             return {"error": "Text could not be split into documents."}

        print(f"Split text into {len(docs)} documents.")

        # 2. Create Vector Store for context retrieval
        print("Creating vector store...")
        vector_store = FAISS.from_documents(docs, embeddings)
        print("Vector store created.")

        # For simplicity in this example, we'll use the *entire* text as context
        # for the main analysis. For very large texts, you might retrieve relevant
        # chunks using vector_store.similarity_search() before each LLM call,
        # but aggregating results across chunks adds complexity.
        # Using full context ensures Gemini sees the whole picture for consistency checks.
        # Note: This might hit token limits for extremely large single files.
        # A more robust solution would chunk the analysis itself or use map-reduce chains.
        full_context = text # Consider token limits

        # --- Run Analysis Chains ---
        results = {}

        print("Extracting Knowledge Graph...")
        try:
            kg_result_raw = kg_chain.run(context=full_context)
            results["knowledge_graph"] = json.loads(kg_result_raw)
        except json.JSONDecodeError:
            print("Error decoding KG JSON:", kg_result_raw)
            results["knowledge_graph"] = {"error": "Failed to parse Knowledge Graph JSON from LLM.", "raw_output": kg_result_raw}
        except Exception as e:
             print(f"Error in KG chain: {e}")
             results["knowledge_graph"] = {"error": str(e)}


        print("Detecting Contradictions...")
        try:
            contradiction_result_raw = contradiction_chain.run(context=full_context)
            results["contradictions"] = json.loads(contradiction_result_raw)
        except json.JSONDecodeError:
            print("Error decoding Contradictions JSON:", contradiction_result_raw)
            results["contradictions"] = {"error": "Failed to parse Contradictions JSON from LLM.", "raw_output": contradiction_result_raw}
        except Exception as e:
             print(f"Error in Contradiction chain: {e}")
             results["contradictions"] = {"error": str(e)}


        print("Identifying Speculation Boundaries...")
        try:
            speculation_result_raw = speculation_chain.run(context=full_context)
            results["speculation_boundaries"] = json.loads(speculation_result_raw)
        except json.JSONDecodeError:
            print("Error decoding Speculation JSON:", speculation_result_raw)
            results["speculation_boundaries"] = {"error": "Failed to parse Speculation Boundaries JSON from LLM.", "raw_output": speculation_result_raw}
        except Exception as e:
             print(f"Error in Speculation chain: {e}")
             results["speculation_boundaries"] = {"error": str(e)}

        print("Analysis complete.")
        return results

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        # In a production scenario, log the full traceback
        import traceback
        traceback.print_exc()
        return {"error": f"An unexpected error occurred: {str(e)}"}