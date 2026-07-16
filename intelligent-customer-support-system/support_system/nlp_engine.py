"""
nlp_engine.py
A lightweight intent-classification engine for the support chatbot.

Approach:
- Load a knowledge base of intents, each with example patterns and a canned response.
- Vectorize all patterns with TF-IDF.
- For an incoming message, compute cosine similarity against every known pattern.
- Return the intent of the best match, its response, and a confidence score.
- If confidence is below a threshold, the caller should treat this as "unresolved"
  and escalate to a human agent (create a support ticket).
"""

import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

FAQ_PATH = Path(__file__).parent / "data" / "faqs.json"

# Below this similarity score, we consider the bot "not confident enough"
CONFIDENCE_THRESHOLD = 0.35


class SupportNLPEngine:
    def __init__(self, faq_path=FAQ_PATH):
        self.faq_path = faq_path
        self.intents = []          # list of dicts: {intent, patterns, response}
        self.pattern_texts = []    # flattened list of all example patterns
        self.pattern_intent_idx = []  # maps each pattern -> index into self.intents
        self.vectorizer = None
        self.pattern_vectors = None
        self._load_and_fit()

    def _load_and_fit(self):
        with open(self.faq_path, "r", encoding="utf-8") as f:
            self.intents = json.load(f)

        self.pattern_texts = []
        self.pattern_intent_idx = []
        for idx, intent in enumerate(self.intents):
            for pattern in intent["patterns"]:
                self.pattern_texts.append(pattern.lower())
                self.pattern_intent_idx.append(idx)

        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.pattern_vectors = self.vectorizer.fit_transform(self.pattern_texts)

    def reload(self):
        """Call this if faqs.json is edited at runtime."""
        self._load_and_fit()

    def classify(self, message: str):
        """
        Returns a dict:
        {
            "intent": str,
            "response": str,
            "confidence": float,
            "resolved": bool
        }
        """
        if not message or not message.strip():
            return {
                "intent": None,
                "response": "Could you tell me a bit more about what you need help with?",
                "confidence": 0.0,
                "resolved": False,
            }

        query_vec = self.vectorizer.transform([message.lower()])
        similarities = cosine_similarity(query_vec, self.pattern_vectors)[0]

        best_idx = similarities.argmax()
        best_score = float(similarities[best_idx])
        matched_intent_idx = self.pattern_intent_idx[best_idx]
        matched_intent = self.intents[matched_intent_idx]

        resolved = best_score >= CONFIDENCE_THRESHOLD

        if resolved:
            return {
                "intent": matched_intent["intent"],
                "response": matched_intent["response"],
                "confidence": round(best_score, 3),
                "resolved": True,
            }
        else:
            return {
                "intent": None,
                "response": (
                    "I'm not fully sure I understood that. I'm connecting you with a "
                    "human support agent who can help further."
                ),
                "confidence": round(best_score, 3),
                "resolved": False,
            }
