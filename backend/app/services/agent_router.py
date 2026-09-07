"""
LUMYD Agent Router Service
Evaluates incoming natural language queries against task prototypes using multilingual sentence embeddings.
Routes confident queries for automated execution or diverts ambiguous/OOD queries to the escalation queue.
"""

from typing import Any, Dict, List, Optional
import torch
from sqlalchemy.orm import Session

from app.models.agent import AgentTask, EscalationQueue

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_CONFIDENCE_THRESHOLD = 0.60


class AgentRouterService:
    _encoder = None  # Singleton encoder to avoid reloading on every request
    _task_cache: Dict[str, Dict[str, torch.Tensor]] = {}  # Class-level prototype & exemplar cache

    def __init__(self, db: Session, threshold: float = DEFAULT_CONFIDENCE_THRESHOLD):
        self.db = db
        self.threshold = threshold

    @classmethod
    def get_encoder(cls):
        """Lazy loads the SentenceTransformer encoder once."""
        if cls._encoder is None:
            from sentence_transformers import SentenceTransformer
            print(f"[*] Loading semantic encoder: {MODEL_NAME}...")
            cls._encoder = SentenceTransformer(MODEL_NAME)
            print("[+] Semantic encoder loaded successfully.")
        return cls._encoder

    def warm_cache(self, force: bool = True) -> None:
        """Loads active tasks from PostgreSQL and builds normalized prototype centroids and exemplar matrices."""
        if AgentRouterService._task_cache and not force:
            return

        encoder = self.get_encoder()
        tasks: List[AgentTask] = (
            self.db.query(AgentTask).filter(AgentTask.is_active == True).all()  # noqa: E712
        )
        new_cache: Dict[str, Dict[str, torch.Tensor]] = {}

        for task in tasks:
            if task.sample_queries and len(task.sample_queries) > 0:
                # Encode all sample phrases into normalized tensors
                embeddings = encoder.encode(
                    task.sample_queries,
                    convert_to_tensor=True,
                    normalize_embeddings=True
                )
                # Centroid is the mean vector, re-normalized
                centroid = torch.mean(embeddings, dim=0)
                centroid = centroid / torch.norm(centroid)
                new_cache[task.task_name] = {
                    "centroid": centroid,
                    "exemplars": embeddings,
                }

        AgentRouterService._task_cache = new_cache
        print(f"[+] Semantic router cache warmed with {len(new_cache)} task prototypes.")

    def route_query(self, dataset_id: str, query: str) -> Dict[str, Any]:
        """
        Routes an incoming query to an automated task handler or diverts to escalation queue.
        Calculates hybrid similarity: max(Sim(q, centroid), max_k(Sim(q, exemplar_k))).
        """
        if not AgentRouterService._task_cache:
            self.warm_cache()

        if not AgentRouterService._task_cache:
            raise ValueError("No active analytical tasks found in the database. Run seed_agent_tasks.py first.")

        encoder = self.get_encoder()
        query_vector = encoder.encode(
            query,
            convert_to_tensor=True,
            normalize_embeddings=True
        )

        from sentence_transformers import util

        best_task: Optional[str] = None
        best_score: float = -1.0
        scores_by_task: Dict[str, float] = {}

        for task_name, proto_data in AgentRouterService._task_cache.items():
            centroid_score = util.cos_sim(query_vector, proto_data["centroid"]).item()
            exemplar_scores = util.cos_sim(query_vector, proto_data["exemplars"])
            max_exemplar_score = torch.max(exemplar_scores).item()
            score = max(centroid_score, max_exemplar_score)
            scores_by_task[task_name] = round(score, 4)
            if score > best_score:
                best_score = score
                best_task = task_name

        confidence = round(best_score, 4)

        # In-Distribution (ID): High confidence match
        if best_score >= self.threshold:
            return {
                "route": "AUTOMATED_EXECUTION",
                "task": best_task,
                "confidence": confidence,
                "escalated": False,
                "scores": scores_by_task
            }

        # Out-of-Distribution (OOD): Escalate to queue for human or LLM triage
        escalation_record = EscalationQueue(
            dataset_id=dataset_id,
            raw_query=query,
            confidence_score=confidence,
            predicted_task=best_task,
            status="PENDING"
        )
        self.db.add(escalation_record)
        self.db.commit()
        self.db.refresh(escalation_record)

        return {
            "route": "HUMAN_ESCALATION",
            "task": best_task,
            "confidence": confidence,
            "escalated": True,
            "escalation_id": escalation_record.id,
            "scores": scores_by_task,
            "message": f"Query confidence ({confidence:.2f}) below threshold ({self.threshold:.2f}). Escalated to triage."
        }
