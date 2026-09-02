"""
Recommendation Engine Adapters
"""
from abc import ABC, abstractmethod
from typing import Any

from ....application.ports.external_services import RecommendationEnginePort


@dataclass
class RecommendationResult:
    """Recommendation result"""
    item_id: str
    score: float
    metadata: dict[str, Any]


class BaseRecommendationAdapter(RecommendationEnginePort, ABC):
    """Base recommendation adapter"""

    @abstractmethod
    async def _train_request(
        self,
        interactions: list[dict[str, Any]],
        item_features: dict[str, Any] | None,
        user_features: dict[str, Any] | None,
    ) -> None:
        """Train model request"""
        pass

    @abstractmethod
    async def _recommend_request(
        self,
        user_id: str,
        n_recommendations: int,
        filter_items: list[str] | None,
    ) -> list[RecommendationResult]:
        """Get recommendations request"""
        pass

    @abstractmethod
    async def _similar_items_request(
        self,
        item_id: str,
        n_similar: int,
    ) -> list[RecommendationResult]:
        """Get similar items request"""
        pass

    @abstractmethod
    async def _update_user_request(
        self,
        user_id: str,
        interactions: list[dict[str, Any]],
    ) -> None:
        """Update user model request"""
        pass

    async def train(
        self,
        interactions: list[dict[str, Any]],
        item_features: dict[str, Any] | None = None,
        user_features: dict[str, Any] | None = None,
    ) -> None:
        """Train recommendation model"""
        await self._train_request(interactions, item_features, user_features)

    async def recommend(
        self,
        user_id: str,
        n_recommendations: int = 10,
        filter_items: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get recommendations for user"""
        results = await self._recommend_request(user_id, n_recommendations, filter_items)
        return [
            {
                "item_id": r.item_id,
                "score": r.score,
                "metadata": r.metadata,
            }
            for r in results
        ]

    async def similar_items(
        self,
        item_id: str,
        n_similar: int = 10,
    ) -> list[dict[str, Any]]:
        """Get similar items"""
        results = await self._similar_items_request(item_id, n_similar)
        return [
            {
                "item_id": r.item_id,
                "score": r.score,
                "metadata": r.metadata,
            }
            for r in results
        ]

    async def update_user(
        self,
        user_id: str,
        interactions: list[dict[str, Any]],
    ) -> None:
        """Update user model with new interactions"""
        await self._update_user_request(user_id, interactions)


class LightFMAdapter(BaseRecommendationAdapter):
    """LightFM recommendation adapter (local)"""

    def __init__(self, no_components: int = 32, learning_rate: float = 0.05, loss: str = "warp"):
        self.no_components = no_components
        self.learning_rate = learning_rate
        self.loss = loss
        self._model = None
        self._user_id_map = {}
        self._item_id_map = {}
        self._reverse_user_map = {}
        self._reverse_item_map = {}

    async def _load_model(self):
        if self._model is None:
            from lightfm import LightFM
            self._model = LightFM(
                no_components=self.no_components,
                learning_rate=self.learning_rate,
                loss=self.loss,
            )

    def _get_user_index(self, user_id: str) -> int:
        if user_id not in self._user_id_map:
            idx = len(self._user_id_map)
            self._user_id_map[user_id] = idx
            self._reverse_user_map[idx] = user_id
        return self._user_id_map[user_id]

    def _get_item_index(self, item_id: str) -> int:
        if item_id not in self._item_id_map:
            idx = len(self._item_id_map)
            self._item_id_map[item_id] = idx
            self._reverse_item_map[idx] = item_id
        return self._item_id_map[item_id]

    async def _train_request(
        self,
        interactions: list[dict[str, Any]],
        item_features: dict[str, Any] | None,
        user_features: dict[str, Any] | None,
    ) -> None:
        await self._load_model()
        from scipy.sparse import coo_matrix

        # Build interaction matrix
        rows = []
        cols = []
        data = []

        for interaction in interactions:
            user_idx = self._get_user_index(interaction["user_id"])
            item_idx = self._get_item_index(interaction["item_id"])
            weight = interaction.get("weight", 1.0)

            rows.append(user_idx)
            cols.append(item_idx)
            data.append(weight)

        n_users = len(self._user_id_map)
        n_items = len(self._item_id_map)

        interaction_matrix = coo_matrix(
            (data, (rows, cols)),
            shape=(n_users, n_items),
        ).tocsr()

        # Build feature matrices if provided
        item_feature_matrix = None
        user_feature_matrix = None

        if item_features:
            # Build item feature matrix
            pass

        if user_features:
            # Build user feature matrix
            pass

        self._model.fit(
            interaction_matrix,
            item_features=item_feature_matrix,
            user_features=user_feature_matrix,
            epochs=10,
            num_threads=4,
        )

    async def _recommend_request(
        self,
        user_id: str,
        n_recommendations: int,
        filter_items: list[str] | None,
    ) -> list[RecommendationResult]:
        await self._load_model()
        import numpy as np

        if user_id not in self._user_id_map:
            return []

        user_idx = self._user_id_map[user_id]
        n_items = len(self._item_id_map)

        # Get scores for all items
        scores = self._model.predict(user_idx, np.arange(n_items))

        # Filter out already interacted items
        if filter_items:
            for item_id in filter_items:
                if item_id in self._item_id_map:
                    scores[self._item_id_map[item_id]] = -np.inf

        # Get top N
        top_indices = np.argsort(-scores)[:n_recommendations]

        results = []
        for idx in top_indices:
            if idx in self._reverse_item_map:
                results.append(RecommendationResult(
                    item_id=self._reverse_item_map[idx],
                    score=float(scores[idx]),
                    metadata={},
                ))

        return results

    async def _similar_items_request(
        self,
        item_id: str,
        n_similar: int,
    ) -> list[RecommendationResult]:
        await self._load_model()
        import numpy as np

        if item_id not in self._item_id_map:
            return []

        item_idx = self._item_id_map[item_id]
        item_embedding = self._model.item_embeddings[item_idx]

        # Compute similarities with all items
        similarities = np.dot(self._model.item_embeddings, item_embedding)
        similarities[item_idx] = -1  # Exclude self

        top_indices = np.argsort(-similarities)[:n_similar]

        results = []
        for idx in top_indices:
            if idx in self._reverse_item_map:
                results.append(RecommendationResult(
                    item_id=self._reverse_item_map[idx],
                    score=float(similarities[idx]),
                    metadata={},
                ))

        return results

    async def _update_user_request(
        self,
        user_id: str,
        interactions: list[dict[str, Any]],
    ) -> None:
        # LightFM supports partial_fit for incremental updates
        await self._load_model()
        from scipy.sparse import coo_matrix

        if user_id not in self._user_id_map:
            self._get_user_index(user_id)

        user_idx = self._user_id_map[user_id]
        n_items = len(self._item_id_map)

        rows = []
        cols = []
        data = []

        for interaction in interactions:
            item_id = interaction["item_id"]
            if item_id not in self._item_id_map:
                self._get_item_index(item_id)

            item_idx = self._item_id_map[item_id]
            weight = interaction.get("weight", 1.0)

            rows.append(user_idx)
            cols.append(item_idx)
            data.append(weight)

        interaction_matrix = coo_matrix(
            (data, (rows, cols)),
            shape=(len(self._user_id_map), n_items),
        ).tocsr()

        self._model.fit_partial(interaction_matrix, epochs=1)


class ImplicitAdapter(BaseRecommendationAdapter):
    """Implicit recommendation adapter (local)"""

    def __init__(self, factors: int = 64, regularization: float = 0.01, iterations: int = 15):
        self.factors = factors
        self.regularization = regularization
        self.iterations = iterations
        self._model = None
        self._user_id_map = {}
        self._item_id_map = {}
        self._reverse_user_map = {}
        self._reverse_item_map = {}

    async def _load_model(self):
        if self._model is None:
            from implicit.als import AlternatingLeastSquares
            self._model = AlternatingLeastSquares(
                factors=self.factors,
                regularization=self.regularization,
                iterations=self.iterations,
            )

    def _get_user_index(self, user_id: str) -> int:
        if user_id not in self._user_id_map:
            idx = len(self._user_id_map)
            self._user_id_map[user_id] = idx
            self._reverse_user_map[idx] = user_id
        return self._user_id_map[user_id]

    def _get_item_index(self, item_id: str) -> int:
        if item_id not in self._item_id_map:
            idx = len(self._item_id_map)
            self._item_id_map[item_id] = idx
            self._reverse_item_map[idx] = item_id
        return self._item_id_map[item_id]

    async def _train_request(
        self,
        interactions: list[dict[str, Any]],
        item_features: dict[str, Any] | None,
        user_features: dict[str, Any] | None,
    ) -> None:
        await self._load_model()
        from scipy.sparse import coo_matrix

        rows = []
        cols = []
        data = []

        for interaction in interactions:
            user_idx = self._get_user_index(interaction["user_id"])
            item_idx = self._get_item_index(interaction["item_id"])
            weight = interaction.get("weight", 1.0)

            rows.append(user_idx)
            cols.append(item_idx)
            data.append(weight)

        n_users = len(self._user_id_map)
        n_items = len(self._item_id_map)

        interaction_matrix = coo_matrix(
            (data, (rows, cols)),
            shape=(n_users, n_items),
        ).tocsr()

        self._model.fit(interaction_matrix)

    async def _recommend_request(
        self,
        user_id: str,
        n_recommendations: int,
        filter_items: list[str] | None,
    ) -> list[RecommendationResult]:
        await self._load_model()

        if user_id not in self._user_id_map:
            return []

        user_idx = self._user_id_map[user_id]

        # Get items to filter
        filter_indices = []
        if filter_items:
            for item_id in filter_items:
                if item_id in self._item_id_map:
                    filter_indices.append(self._item_id_map[item_id])

        # Get recommendations
        item_indices, scores = self._model.recommend(
            user_idx,
            self._model.item_factors,
            N=n_recommendations,
            filter_already_liked_items=True,
            filter_items=filter_indices,
        )

        results = []
        for idx, score in zip(item_indices, scores, strict=False):
            if idx in self._reverse_item_map:
                results.append(RecommendationResult(
                    item_id=self._reverse_item_map[idx],
                    score=float(score),
                    metadata={},
                ))

        return results

    async def _similar_items_request(
        self,
        item_id: str,
        n_similar: int,
    ) -> list[RecommendationResult]:
        await self._load_model()

        if item_id not in self._item_id_map:
            return []

        item_idx = self._item_id_map[item_id]

        similar_indices, scores = self._model.similar_items(item_idx, N=n_similar + 1)

        results = []
        for idx, score in zip(similar_indices[1:], scores[1:], strict=False):  # Skip first (self)
            if idx in self._reverse_item_map:
                results.append(RecommendationResult(
                    item_id=self._reverse_item_map[idx],
                    score=float(score),
                    metadata={},
                ))

        return results

    async def _update_user_request(
        self,
        user_id: str,
        interactions: list[dict[str, Any]],
    ) -> None:
        # Implicit doesn't have easy incremental update
        # Would need to retrain or use a different approach
        pass


class SurpriseAdapter(BaseRecommendationAdapter):
    """Surprise recommendation adapter (local)"""

    def __init__(self, algorithm: str = "SVD", n_factors: int = 100):
        self.algorithm = algorithm
        self.n_factors = n_factors
        self._model = None
        self._trainset = None

    async def _load_model(self):
        if self._model is None:
            from surprise import NMF, SVD, KNNBasic

            if self.algorithm == "SVD":
                self._model = SVD(n_factors=self.n_factors)
            elif self.algorithm == "KNN":
                self._model = KNNBasic()
            elif self.algorithm == "NMF":
                self._model = NMF(n_factors=self.n_factors)

    async def _train_request(
        self,
        interactions: list[dict[str, Any]],
        item_features: dict[str, Any] | None,
        user_features: dict[str, Any] | None,
    ) -> None:
        await self._load_model()
        from surprise import Dataset, Reader

        # Build dataset
        data = []
        for interaction in interactions:
            data.append((
                interaction["user_id"],
                interaction["item_id"],
                interaction.get("rating", interaction.get("weight", 1.0)),
            ))

        reader = Reader(rating_scale=(0, 5))
        dataset = Dataset.load_from_df(
            pd.DataFrame(data, columns=["user", "item", "rating"]),
            reader,
        )

        self._trainset = dataset.build_full_trainset()
        self._model.fit(self._trainset)

    async def _recommend_request(
        self,
        user_id: str,
        n_recommendations: int,
        filter_items: list[str] | None,
    ) -> list[RecommendationResult]:
        await self._load_model()

        try:
            inner_uid = self._trainset.to_inner_uid(user_id)
        except ValueError:
            return []

        # Get all items
        all_items = [self._trainset.to_raw_iid(i) for i in range(self._trainset.n_items)]

        # Filter out already rated items
        rated_items = set()
        for item_inner, _ in self._trainset.ur[inner_uid]:
            rated_items.add(self._trainset.to_raw_iid(item_inner))

        if filter_items:
            rated_items.update(filter_items)

        # Predict for unrated items
        predictions = []
        for item_id in all_items:
            if item_id not in rated_items:
                pred = self._model.predict(user_id, item_id)
                predictions.append((item_id, pred.est))

        # Sort by predicted rating
        predictions.sort(key=lambda x: x[1], reverse=True)

        results = []
        for item_id, score in predictions[:n_recommendations]:
            results.append(RecommendationResult(
                item_id=item_id,
                score=float(score),
                metadata={},
            ))

        return results

    async def _similar_items_request(
        self,
        item_id: str,
        n_similar: int,
    ) -> list[RecommendationResult]:
        # Surprise doesn't have built-in similar items
        return []

    async def _update_user_request(
        self,
        user_id: str,
        interactions: list[dict[str, Any]],
    ) -> None:
        # Surprise doesn't have easy incremental update
        pass
