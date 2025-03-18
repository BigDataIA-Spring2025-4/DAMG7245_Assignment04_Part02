import re
import spacy
import spacy.cli

def markdown_chunking(markdown_text, heading_level=2):
    pattern = rf'(?=^{"#" * heading_level} )'  # Regex to match specified heading level
    chunks = re.split(pattern, markdown_text, flags=re.MULTILINE)
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def semantic_chunking(text, max_sentences=5):
    try:
        nlp = spacy.load("en_core_web_sm")
        print("Loaded Semantic Model successfully")
    except:
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
        print("Downloaded and Loaded Semantic Model successfully")
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
   
    chunks = []
    current_chunk = []
    for i, sent in enumerate(sentences):
        current_chunk.append(sent)
        if (i + 1) % max_sentences == 0:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
   
    if current_chunk:
        chunks.append(" ".join(current_chunk))
   
    return chunks