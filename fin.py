import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from typing import List, Optional, Dict, Any
import json
from dotenv import load_dotenv


def get_llm():
    load_dotenv()
    google_api_key = os.getenv("GEMINI_API_KEY")
    if not google_api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set. Please set it to use the LLM."
        )

    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=google_api_key,
        temperature=0.7,
    )


def _extract_content_from_response(response_obj):
    """Extract clean content from LLM response object.
    Works with different response formats from various LLM providers."""
    if hasattr(response_obj, "content"):
        return response_obj.content
    elif isinstance(response_obj, dict) and "content" in response_obj:
        return response_obj["content"]
    elif isinstance(response_obj, str):
        return response_obj
    else:
        # Try to convert to string as fallback
        return str(response_obj)


class StoryVectorDatabase:
    def __init__(self, folder_path: str):
        """Initialize the story vector database for a specific folder.

        Args:
            folder_path: Path to the folder containing story files
        """
        # Create data directory if it doesn't exist
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)

        # Get folder name from path and use it for the db name
        self.folder_name = os.path.basename(os.path.normpath(folder_path))
        self.db_path = os.path.join(self.data_dir, self.folder_name)

        # Store the folder path for processing files
        self.folder_path = folder_path

        # Using HuggingFace's all-MiniLM-L6-v2 which is good for semantic search
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", ". ", " ", ""]
        )
        # Initialize or load the vector store
        self.vector_store = self._load_or_create_db()
        # Metadata storage for key information
        self.metadata_path = f"{self.db_path}/{self.folder_name}_metadata.json"
        self.metadata = self._load_or_create_metadata()
        # Conversation history
        self.conversation_history = []
        self.max_history_length = 5
        self.load_conversation_history()

    def _load_or_create_db(self):
        """Load existing vector database or create a new one."""
        try:
            # Add allow_dangerous_deserialization=True parameter
            vector_store = FAISS.load_local(
                self.db_path,
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            return vector_store
        except Exception as e:
            print(f"Error loading vector database for {self.folder_name}: {e}")
            # Return None if no existing database
        return None

    # to do
    def _load_or_create_metadata(self):
        """Load existing metadata or create a new dictionary."""
        try:
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        except:
            # Initialize with empty metadata structure
            return {
                "files_processed": [],
                "character_info": {},
                "timeline_events": [],
                "potential_contradictions": [],
            }

    def _save_metadata(self):
        """Save metadata to disk."""
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def process_file(self, file_name: str, file_id: Optional[str] = None):
        """Process a text file and add it to the vector database.

        Args:
            file_name: Name of the file (not full path)
            file_id: Optional identifier for the file (defaults to filename)
        """
        # Build full file path
        file_path = os.path.join(self.folder_path, file_name)

        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return

        if file_id is None:
            file_id = file_name

        # Check if file was already processed
        if file_id in self.metadata["files_processed"]:
            print(f"File {file_id} already processed. Use update_file to modify.")
            return

        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        print(f"Processing file: {file_id}")
        print(f"Raw text length: {len(raw_text)} characters")
        print(f"Raw text: {raw_text[:100]}...")  # Print first 100 characters

        # Split text into chunks
        docs = self.text_splitter.create_documents([raw_text])

        # Add file metadata to each chunk
        for i, doc in enumerate(docs):
            doc.metadata = {
                "file_id": file_id,
                "chunk_id": i,
                "total_chunks": len(docs),
            }

        # Create or add to vector store
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(docs, self.embeddings)
            self.vector_store.save_local(self.db_path)
        else:
            self.vector_store.add_documents(docs)
            self.vector_store.save_local(self.db_path)

        # Update metadata
        self.metadata["files_processed"].append(file_id)

        # Extract key information using LLM
        self._extract_story_info(raw_text, file_id)

        # Save updated metadata
        self._save_metadata()

        print(
            f"File {file_id} processed and added to vector database for folder {self.folder_name}."
        )

    def process_folder(self):
        """Process all text files in the folder."""
        if not os.path.exists(self.folder_path):
            print(f"Folder {self.folder_path} does not exist.")
            return

        print(f"Processing all files in folder: {self.folder_path}")

        # Process all text files in the folder
        for file_name in os.listdir(self.folder_path):
            if file_name.endswith(".txt"):
                self.process_file(file_name)

        # Reconcile story information after processing all files
        self._reconcile_story_information()

        print(f"All files in folder {self.folder_name} processed.")

    def update_file(self, file_name: str, file_id: Optional[str] = None):
        """Update an existing file in the database.

        Args:
            file_name: Name of the file (not full path)
            file_id: Optional identifier for the file (defaults to filename)
        """
        file_path = os.path.join(self.folder_path, file_name)

        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return

        if file_id is None:
            file_id = file_name

        # Remove existing entries for this file
        if file_id in self.metadata["files_processed"]:
            self._remove_file_entries(file_id)

        # Process the file as new
        self.process_file(file_name, file_id)

        # Reconcile new information with existing data
        self._reconcile_story_information()

        # Reset conversation history as story content has changed
        self.conversation_history = []

        print(
            f"File {file_id} updated in vector database for folder {self.folder_name}."
        )

    def _remove_file_entries(self, file_id: str):
        """Remove entries for a specific file from the vector database."""
        if self.vector_store is None:
            return

        # Get all documents
        all_docs = []
        for doc_id in range(len(self.vector_store.docstore._dict)):
            if doc_id in self.vector_store.docstore._dict:
                doc = self.vector_store.docstore._dict[doc_id]
                all_docs.append((doc_id, doc))

        # Filter out documents from the file to be removed
        docs_to_keep = [
            (doc_id, doc)
            for doc_id, doc in all_docs
            if doc.metadata.get("file_id") != file_id
        ]

        # Create new vector store with remaining documents
        if docs_to_keep:
            new_docs = [doc for _, doc in docs_to_keep]
            self.vector_store = FAISS.from_documents(new_docs, self.embeddings)
            self.vector_store.save_local(self.db_path)
        else:
            self.vector_store = None

        # Update metadata
        if file_id in self.metadata["files_processed"]:
            self.metadata["files_processed"].remove(file_id)

        if file_id in self.metadata["character_info"]:
            del self.metadata["character_info"][file_id]

        self.metadata["timeline_events"] = [
            event
            for event in self.metadata["timeline_events"]
            if event["file_id"] != file_id
        ]

        self.metadata["potential_contradictions"] = [
            contra
            for contra in self.metadata["potential_contradictions"]
            if contra["file_id"] != file_id
        ]

        self._save_metadata()

    # Rest of the class methods remain unchanged
    def _extract_story_info(self, text: str, file_id: str):
        """Extract key information from the story using LLM."""
        llm = get_llm()

        # Extract character information
        character_prompt = f"""
        Analyze the following story text and extract information about all characters mentioned.
        Include their names, descriptions, roles, and any key attributes.
        For unnamed characters, assign a descriptive identifier.
        
        TEXT:
        {text[:10000]}... (truncated)
        
        CHARACTERS:
        """

        character_response = llm.invoke(character_prompt)
        character_str = _extract_content_from_response(character_response)
        # Extract timeline events
        timeline_prompt = f"""
        Analyze the following story text and extract a chronological timeline of key events.
        Include the event and when it occurred in the story's timeline.
        
        TEXT:
        {text[:10000]}... (truncated)
        
        TIMELINE:
        """

        timeline_response = llm.invoke(timeline_prompt)
        timeline_str = _extract_content_from_response(timeline_response)
        # Look for potential contradictions
        contradiction_prompt = f"""
        Analyze the following story text and identify any potential contradictions or inconsistencies.
        Focus on character actions, timeline conflicts, or plot holes. and mention from where they are too. 
        
        TEXT:
        {text[:10000]}... (truncated)
        
        POTENTIAL CONTRADICTIONS:
        """

        contradiction_response = llm.invoke(contradiction_prompt)
        contradiction_str = _extract_content_from_response(contradiction_response)
        # Save to metadata
        self.metadata["character_info"][file_id] = character_str
        self.metadata["timeline_events"].append(
            {"file_id": file_id, "events": timeline_str}
        )
        self.metadata["potential_contradictions"].append(
            {"file_id": file_id, "contradictions": contradiction_str}
        )

    def _reconcile_story_information(self):
        """Reconcile information across all story files to update character identities and timeline."""
        if not self.metadata["files_processed"]:
            return

        llm = get_llm()

        # Prepare all character information
        all_character_info = "\n\n".join(
            [
                f"FILE {file_id}:\n{info}"
                for file_id, info in self.metadata["character_info"].items()
            ]
        )

        # Reconcile character identities
        character_reconcile_prompt = f"""
        Review the character information from multiple story files below.
        Identify any unnamed characters from earlier files that are named in later files.
        Create a master list of all characters with their most complete information.
        
        {all_character_info}
        
        RECONCILED CHARACTER LIST:
        """

        reconciled_characters = llm.invoke(character_reconcile_prompt)

        # Create combined reconciled character data
        self.metadata["reconciled_characters"] = _extract_content_from_response(
            reconciled_characters
        )

        # Prepare all timeline information
        all_timeline_info = "\n\n".join(
            [
                f"FILE {event['file_id']}:\n{event['events']}"
                for event in self.metadata["timeline_events"]
            ]
        )

        # Reconcile timeline
        timeline_reconcile_prompt = f"""
        Review the timeline information from multiple story files below.
        Create a unified chronological timeline that places all events in proper order.
        Resolve any timeline conflicts or contradictions.
        
        {all_timeline_info}
        
        UNIFIED TIMELINE:
        """

        unified_timeline = llm.invoke(timeline_reconcile_prompt)

        # Save reconciled timeline
        self.metadata["unified_timeline"] = _extract_content_from_response(
            unified_timeline
        )

        self._save_metadata()

    def query(
        self, question: str, k: int = 5, use_conversation_history: bool = True
    ) -> Dict[str, Any]:
        """Query the vector database with a question, maintaining conversation context."""
        if self.vector_store is None:
            return {"answer": "No documents have been processed yet.", "sources": []}

        # Print docstore size for debugging
        doc_count = (
            len(self.vector_store.docstore._dict)
            if hasattr(self.vector_store, "docstore")
            and hasattr(self.vector_store.docstore, "_dict")
            else "unknown"
        )
        print(f"Searching through {doc_count} documents")

        # Get relevant documents
        docs = self.vector_store.similarity_search(question, k=k)

        if not docs:
            return {
                "answer": "I couldn't find any relevant information in the story to answer your question.",
                "sources": [],
            }

        # Create context from relevant chunks
        context = "\n\n".join([doc.page_content for doc in docs])

        # Get metadata for source tracking
        sources = [
            {
                "file_id": doc.metadata.get("file_id", "unknown"),
                "chunk_id": doc.metadata.get("chunk_id", "unknown"),
            }
            for doc in docs
        ]

        llm = get_llm()

        # Check if we need to include metadata in the query
        if "character" in question.lower() or "who" in question.lower():
            # Include reconciled character information
            if "reconciled_characters" in self.metadata:
                context += f"\n\nCHARACTER INFORMATION:\n{self.metadata['reconciled_characters']}"

        if (
            "timeline" in question.lower()
            or "when" in question.lower()
            or "before" in question.lower()
            or "after" in question.lower()
        ):
            # Include unified timeline
            if "unified_timeline" in self.metadata:
                context += (
                    f"\n\nTIMELINE INFORMATION:\n{self.metadata['unified_timeline']}"
                )

        if "contradiction" in question.lower() or "inconsistent" in question.lower():
            # Include potential contradictions
            contradictions = "\n\n".join(
                [
                    f"FILE {c['file_id']}:\n{c['contradictions']}"
                    for c in self.metadata["potential_contradictions"]
                ]
            )
            context += f"\n\nPOTENTIAL CONTRADICTIONS:\n{contradictions}"

        # Build conversation history context
        conversation_context = ""
        if use_conversation_history and self.conversation_history:
            conversation_context = "PREVIOUS CONVERSATION:\n"
            for i, (q, a) in enumerate(self.conversation_history):
                conversation_context += (
                    f"Question {i + 1}: {q}\nAnswer {i + 1}: {a}\n\n"
                )

        # Create query with context and conversation history
        query_prompt = f"""
        Your are a writer's assistant.
        Answer the following question based on the provided context and previous conversation.
        Use the context and conversation history to provide a detailed answer.
        Help the writer identify if their question contradicts the story.
        also help them explore new ideas and directions for the story while maintaining continuity.
        If the answer is not clear, suggest possible interpretations or directions.
        if the user asks anything outside of the story, reply with "Sorry, that isn't part of the Universe"
        only reply with the answer and cite sources for whatever you say(eg: this was mentioned in book1 sentence: "", this contradicts x mentioned in book1 sentence: ""). 
        CONTEXT:
        {context}
        
        {conversation_context}
        
        CURRENT QUESTION WITH CITE: {question}
        
        DETAILED ANSWER:
        """

        answer = llm.invoke(query_prompt)
        answer_str = _extract_content_from_response(answer)

        # Update conversation history
        self.conversation_history.append((question, answer_str))
        # Keep only recent conversation history
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[
                -self.max_history_length :
            ]

        return {"answer": answer_str, "sources": sources}

    def get_story_summary(self) -> str:
        """Generate a summary of the entire story across all files."""
        if not self.metadata["files_processed"]:
            return "No story files have been processed yet."

        llm = get_llm()

        # Get full chunks from vector store - more direct approach
        full_text_samples = []
        if self.vector_store:
            # Get representative chunks from across the story
            search_queries = [
                "beginning of story",
                "middle of story",
                "end of story",
                "main character",
                "key events",
                "climax",
            ]

            for query in search_queries:
                docs = self.vector_store.similarity_search(query, k=2)
                chunks = [doc.page_content for doc in docs]
                full_text_samples.extend(chunks)

        # If we still don't have text, try to get all chunks
        if not full_text_samples and self.vector_store:
            # Get all document IDs
            all_docs = []
            for doc_id in range(len(self.vector_store.docstore._dict)):
                if doc_id in self.vector_store.docstore._dict:
                    doc = self.vector_store.docstore._dict[doc_id]
                    all_docs.append(doc)

            # Get text from all documents (up to a limit)
            max_chunks = 20  # Limit chunks to avoid token limits
            chunks = [doc.page_content for doc in all_docs[:max_chunks]]
            full_text_samples.extend(chunks)

        # Combine all text
        combined_text = "\n\n".join(full_text_samples)

        # Include character and timeline information if available
        char_info = self.metadata.get("reconciled_characters", "")
        timeline = self.metadata.get("unified_timeline", "")

        # Add explicit instructions to use what's available
        summary_prompt = f"""
        Generate a comprehensive summary of the story based on the following text samples from the story.
        Focus on what you can determine from these samples without asking for more information.
        If information seems incomplete, make reasonable inferences based on what is available.
        Include main characters, plot elements, key events, and themes you can identify.
        
        TEXT SAMPLES FROM STORY:
        {combined_text[:15000]}
        
        CHARACTER INFORMATION (if available):
        {char_info}
        
        TIMELINE (if available):
        {timeline}
        
        COMPREHENSIVE STORY SUMMARY:
        """

        summary = llm.invoke(summary_prompt)
        return _extract_content_from_response(summary)

    def save_conversation_history(self, file_path: str = None):
        """Save conversation history to a file."""
        if file_path is None:
            file_path = f"{self.db_path}_conversation.json"

        with open(file_path, "w") as f:
            json.dump(self.conversation_history, f, indent=2)

        print(f"Conversation history saved to {file_path}")

    def load_conversation_history(self, file_path: str = None):
        """Load conversation history from a file."""
        if file_path is None:
            file_path = f"{self.db_path}_conversation.json"
        try:
            with open(file_path, "r") as f:
                self.conversation_history = json.load(f)
            print(f"Conversation history loaded from {file_path}")
        except:
            print(f"No conversation history found at {file_path}")

    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        print("Conversation history cleared")


# Function to process a specific folder
def process_story_folder(folder_path: str):
    """Process all story text files in a folder and create embeddings.

    Args:
        folder_path: Path to the folder containing text files
    """
    # Initialize the vector database for this folder
    story_db = StoryVectorDatabase(folder_path)

    # Process all files in the folder
    story_db.process_folder()

    return story_db


# Updated interactive conversation function to work with folders
def have_conversation_with_story(folder_path: str):
    """Have an interactive conversation with the story database for a specific folder."""
    story_db = StoryVectorDatabase(folder_path)

    if not story_db.metadata["files_processed"]:
        print(
            f"No story files have been processed in folder {folder_path}. Please process files first."
        )
        return

    print(
        f"Welcome to the Story Conversation Interface for folder: {story_db.folder_name}!"
    )
    print("You can ask questions about the story, or type 'exit' to quit.")
    print("Type 'summary' to get a summary of the story.")
    print("Type 'clear' to clear conversation history.")

    while True:
        question = input("\nYour question: ")

        if question.lower() == "exit":
            break

        if question.lower() == "summary":
            print("\nGenerating story summary...")
            summary = story_db.get_story_summary()
            print("\nSTORY SUMMARY:")
            print(summary)
            continue

        if question.lower() == "clear":
            story_db.clear_conversation_history()
            continue

        print("\nThinking...")
        result = story_db.query(question)
        print("\nANSWER:")
        print(result["answer"])
        print("\nSOURCES:")
        for source in result["sources"]:
            print(f"- File: {source['file_id']}, Chunk: {source['chunk_id']}")


# Updated API functions
def file_deleted(folder_path: str, file_name: str):
    """Handle file deletion event."""
    story_db = StoryVectorDatabase(folder_path)
    story_db._remove_file_entries(file_name)
    print(
        f"File {file_name} deleted from vector database for folder {story_db.folder_name}."
    )
    return {
        "message": f"File {file_name} deleted from vector database for folder {story_db.folder_name}."
    }


import shutil


def folder_deleted(folder_path: str):
    """Handle folder deletion event."""
    full_path = os.path.join("data", folder_path)
    if os.path.exists(full_path):
        shutil.rmtree(full_path)
        print(f"Folder {full_path} deleted.")
    else:
        print(f"Folder {full_path} does not exist.")
    return {"message": f"Folder {full_path} deleted."}


def file_uploaded(folder_path: str, file_name: str):
    """Handle file upload event."""
    story_db = StoryVectorDatabase(folder_path)
    story_db.process_file(file_name)
    print(f"File {file_name} uploaded and processed for folder {story_db.folder_name}.")
    return {
        "message": f"File {file_name} uploaded and processed for folder {story_db.folder_name}."
    }


def chat_bot(folder_path: str, question: str):
    """Handle chat bot query and return answer."""
    story_db = StoryVectorDatabase(folder_path)
    result = story_db.query(question)
    return {"answer": result["answer"]}


def analysis(folder_path: str):
    """output the metadata formatted correctly, load directly from path data/folder_path with file name folder_name_metadata.json"""
    file_path = os.path.join("data", folder_path, f"{folder_path}_metadata.json")
    with open(file_path, "r") as f:
        metadata = json.load(f)
    formatted = {}
    for book in metadata["files_processed"]:
        formatted[book] = {}
        # remove anything before the first \n\n*
        formatted[book]["characters"] = metadata["character_info"][book].split("\n\n")[
            1
        ]
        for event in metadata["timeline_events"]:
            if event["file_id"] == book:
                formatted[book]["timeline"] = event["events"].split("\n\n")[1]
                break
        for contradiction in metadata["potential_contradictions"]:
            if contradiction["file_id"] == book:
                formatted[book]["contradictions"] = contradiction[
                    "contradictions"
                ].split("\n\n")[1]
                break
    formatted["timeline"] = metadata["unified_timeline"].split("\n\n")[1]
    return formatted


def main():
    """Main function to demonstrate usage."""
    # Example folder path - replace with your actual folder path
    folder_path = "stories/fantasy"

    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Process the folder
    story_db = process_story_folder(folder_path)

    # Start interactive conversation with the folder
    # have_conversation_with_story(folder_path)
    print(chat_bot(folder_path, "What is the main character's name?"))


if __name__ == "__main__":
    main()
