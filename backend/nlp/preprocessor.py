import re
import html
import unicodedata
from typing import List, Dict, Any, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer

# Initialize NLTK resources safely
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except Exception:
    pass

# Custom domain stopwords while keeping negation or modal words that affect sentiment
STANDARD_STOPWORDS = set(stopwords.words('english')) if 'stopwords' in nltk.corpus.__dict__ else {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", 
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", 
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", 
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", 
    "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only", 
    "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she", 
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", 
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", 
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", 
    "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

# Preserve certain words that signal stance
PRESERVE_WORDS = {"not", "never", "no", "without", "against", "claims", "allegedly", "reportedly", "purported"}
FILTER_STOPWORDS = STANDARD_STOPWORDS - PRESERVE_WORDS

class TextPreprocessor:
    def __init__(self):
        try:
            self.lemmatizer = WordNetLemmatizer()
        except Exception:
            self.lemmatizer = None
        self.stemmer = PorterStemmer()

    def clean_text(self, text: str) -> str:
        """Removes HTML tags, normalizes whitespace, unescapes entities."""
        if not text:
            return ""
        # Unescape HTML entities (e.g., &amp; -> &)
        text = html.unescape(text)
        # Normalize unicode (NFKD)
        text = unicodedata.normalize('NFKD', text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Replace URLs
        text = re.sub(r'https?://\S+|www\.\S+', '[URL]', text)
        # Replace Emails
        text = re.sub(r'\S+@\S+', '[EMAIL]', text)
        # Normalize excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def tokenize(self, text: str) -> List[str]:
        """Simple, robust regex tokenization splitting words while preserving contractions."""
        clean = self.clean_text(text).lower()
        tokens = re.findall(r'\b[a-z0-9\'-]+\b', clean)
        return tokens

    def lemmatize_token(self, token: str) -> str:
        """Lemmatizes a token with fallback to stemming."""
        if self.lemmatizer:
            try:
                return self.lemmatizer.lemmatize(token)
            except Exception:
                pass
        return self.stemmer.stem(token)

    def preprocess(self, text: str, remove_stopwords: bool = True, lemmatize: bool = True) -> str:
        """Full NLP pipeline: clean -> tokenize -> filter stopwords -> lemmatize -> join."""
        tokens = self.tokenize(text)
        if remove_stopwords:
            tokens = [t for t in tokens if t not in FILTER_STOPWORDS]
        if lemmatize:
            tokens = [self.lemmatize_token(t) for t in tokens]
        return " ".join(tokens)

    def extract_stats(self, text: str) -> Dict[str, Any]:
        """Extracts descriptive and stylistic linguistic statistics from raw text."""
        raw_clean = self.clean_text(text)
        words = re.findall(r'\b\w+\b', raw_clean)
        sentences = [s.strip() for s in re.split(r'[.!?]+', raw_clean) if s.strip()]
        
        word_count = len(words)
        char_count = len(raw_clean)
        sentence_count = max(len(sentences), 1)
        
        # Upper case stats (exclude single letter acronyms)
        caps_words = [w for w in words if len(w) > 1 and w.isupper()]
        caps_ratio = len(caps_words) / max(word_count, 1)
        
        # Punctuation stats
        exclamation_count = raw_clean.count('!')
        question_count = raw_clean.count('?')
        quote_count = raw_clean.count('"') + raw_clean.count("'")
        
        # Calculate average word length & sentence length
        avg_word_length = sum(len(w) for w in words) / max(word_count, 1)
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        return {
            "word_count": word_count,
            "char_count": char_count,
            "sentence_count": sentence_count,
            "caps_words_count": len(caps_words),
            "caps_ratio": round(caps_ratio, 4),
            "exclamation_count": exclamation_count,
            "question_count": question_count,
            "quote_count": quote_count,
            "avg_word_length": round(avg_word_length, 2),
            "avg_sentence_length": round(avg_sentence_length, 2)
        }

preprocessor = TextPreprocessor()
