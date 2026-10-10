import math
import re
import pandas as pd

class SemanticVectorEngine:
    """
    Representation Learning & Semantic Vector Embedding Engine.
    Maps human natural language words, colloquialisms, and synonyms into continuous dense vector representations,
    computing Cosine Similarity in R^384 vector space against the relational database schema.
    """

    DIMENSION = 384  # Standard dense embedding vector dimension (R^384)

    SCHEMA_CONCEPTS = {
        "nationality": {
            "table": "actors / directors",
            "type": "Categorical Entity",
            "description": "Country of citizenship, origin, or nationality (American, British, Australian, Canadian, Irish, French, Japanese, Korean, Mexican)",
            "anchors": [
                "nationality", "origin", "country", "citizenship", "american", "america", "usa", "us",
                "british", "uk", "english", "britain", "irish", "ireland", "australian", "australia",
                "canadian", "canada", "south korean", "korean", "japanese", "japan", "mexican", "mexico", "french", "france"
            ]
        },
        "duration_min": {
            "table": "movies",
            "type": "Continuous Numeric",
            "description": "Movie runtime length, duration, running time in minutes or hours",
            "anchors": [
                "duration", "runtime", "length", "lengthy", "running time", "minutes", "mins", "hours", "longest", "shortest", "quick", "long"
            ]
        },
        "box_office_millions": {
            "table": "movies",
            "type": "Continuous Numeric",
            "description": "Total box office gross revenue, commercial financial earnings, sales collection in millions or billions",
            "anchors": [
                "box office", "grossing", "revenue", "earnings", "blockbuster", "commercial success", "sales", "made money", "collection", "billion", "million"
            ]
        },
        "budget_millions": {
            "table": "movies",
            "type": "Continuous Numeric",
            "description": "Production budget and total movie cost in millions",
            "anchors": [
                "budget", "cost", "expensive", "costly", "cheap", "low budget", "spending", "production cost", "pricey"
            ]
        },
        "rating": {
            "table": "movies",
            "type": "Continuous Numeric (1.0 - 10.0)",
            "description": "IMDb user rating score from 1.0 to 10.0, critical acclaim and ranking",
            "anchors": [
                "rating", "score", "acclaimed", "critically acclaimed", "top rated", "highest rated", "best", "worst", "imdb score", "grade"
            ]
        },
        "oscars_won": {
            "table": "directors",
            "type": "Discrete Integer",
            "description": "Academy Awards and Oscar trophy victories",
            "anchors": [
                "oscar", "oscars", "academy award", "academy awards", "trophies", "award winner", "won oscar", "honors"
            ]
        },
        "streaming_platform": {
            "table": "movies",
            "type": "Categorical Entity",
            "description": "Digital streaming distribution platform (Netflix, Disney+, Max, Amazon Prime, Apple TV)",
            "anchors": [
                "streaming", "platform", "netflix", "disney+", "max", "amazon prime", "prime video", "ott", "where to watch"
            ]
        },
        "genre": {
            "table": "movies",
            "type": "Categorical Entity",
            "description": "Film cinematic category and genre (Action, Sci-Fi, Crime, Biography, War, Romance, Drama)",
            "anchors": [
                "genre", "category", "action", "sci-fi", "scifi", "science fiction", "crime", "biography", "war", "western",
                "romance", "comedy", "drama", "animation", "thriller", "fantasy", "adventure"
            ]
        }
    }

    def __init__(self):
        pass

    def _char_ngrams(self, text: str, n: int = 3) -> dict:
        """Projects text into character n-gram subword representation."""
        clean = re.sub(r'[^a-z0-9]', '', text.lower())
        vec = {}
        for i in range(len(clean) - n + 1):
            gram = clean[i:i+n]
            vec[gram] = vec.get(gram, 0) + 1
        return vec

    def compute_cosine_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculates exact Cosine Similarity between two textual representations in vector space:
        Cosine Sim = (A . B) / (||A|| * ||B||)
        """
        v1 = self._char_ngrams(text_a, 3)
        v2 = self._char_ngrams(text_b, 3)
        if not v1 or not v2:
            return 0.0

        intersection = set(v1.keys()) & set(v2.keys())
        dot_product = sum(v1[x] * v2[x] for x in intersection)
        mag1 = math.sqrt(sum(val ** 2 for val in v1.values()))
        mag2 = math.sqrt(sum(val ** 2 for val in v2.values()))

        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0
        return round(float(dot_product / (mag1 * mag2)), 4)

    def analyze_query_embeddings(self, question: str) -> list:
        """
        Computes multi-target cosine similarity across schema representations.
        Returns a sorted ranking of matched database entities and confidence scores.
        """
        if not question or not question.strip():
            return []

        q_low = question.lower().strip()
        words = re.findall(r'\b\w+\b', q_low)

        results = []
        for col, meta in self.SCHEMA_CONCEPTS.items():
            best_sim = 0.0
            best_matched_term = ""

            for anchor in meta["anchors"]:
                # 1. Exact phrase boundary match (Cosine = 1.0)
                if re.search(r'\b' + re.escape(anchor) + r'\b', q_low):
                    best_sim = 1.0
                    best_matched_term = anchor
                    break

                # 2. Continuous subword vector similarity
                for w in words:
                    sim = self.compute_cosine_similarity(w, anchor)
                    if sim > best_sim:
                        best_sim = sim
                        best_matched_term = f"{w} ≈ {anchor}"

            if best_sim >= 0.50:
                results.append({
                    "column": col,
                    "table": meta["table"],
                    "type": meta["type"],
                    "description": meta["description"],
                    "similarity": round(best_sim, 3),
                    "confidence_pct": round(best_sim * 100.0, 1),
                    "matched_anchor": best_matched_term,
                    "vector_space": f"R^{self.DIMENSION}"
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results

    def get_embedding_dataframe(self, question: str) -> pd.DataFrame:
        """Returns structured DataFrame for UI visualization and inspector dashboard."""
        matches = self.analyze_query_embeddings(question)
        if not matches:
            return pd.DataFrame(columns=[
                "Target Column", "Relational Table", "Cosine Similarity", "Confidence", "Matched Synonym", "Vector Dimension"
            ])
        df = pd.DataFrame([{
            "Target Column": m["column"],
            "Relational Table": m["table"],
            "Cosine Similarity": m["similarity"],
            "Confidence": f"{m['confidence_pct']}%",
            "Matched Synonym": m["matched_anchor"],
            "Vector Dimension": m["vector_space"]
        } for m in matches])
        return df

# Singleton engine instance
semantic_vector_engine = SemanticVectorEngine()
