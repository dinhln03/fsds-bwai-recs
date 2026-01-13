from collections import defaultdict
from typing import Dict, List, Optional, Set

import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder

from ...base import BaseRecommendationEngine


class FPGrowthRecommendationEngine(BaseRecommendationEngine):
    def __init__(self, min_support: float = 0.01, min_confidence: float = 0.5):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.frequent_itemsets = None
        self.association_rules_df = None
        self.item_recommendations: Dict[str, List[tuple[str, float]]] = defaultdict(
            list
        )

    def fit(self, transactions: list[list[str]]):
        """
        Fit the FP-Growth model on transaction data using mlxtend.
        transactions: List of transactions, where each transaction is a list of items
        """
        if not transactions:
            return

        # Convert transactions to binary matrix format using TransactionEncoder
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df = pd.DataFrame(te_ary, columns=te.columns_)

        # Mine frequent itemsets using FP-Growth
        self.frequent_itemsets = fpgrowth(
            df, min_support=self.min_support, use_colnames=True
        )

        if self.frequent_itemsets.empty:
            return

        # Generate association rules
        self.association_rules_df = association_rules(
            self.frequent_itemsets,
            metric="confidence",
            min_threshold=self.min_confidence,
        )

        # Build item-to-item recommendations
        self._build_item_recommendations()

    def _build_item_recommendations(self):
        """Build item-to-item recommendations from association rules"""
        if self.association_rules_df is None or self.association_rules_df.empty:
            return

        self.item_recommendations.clear()

        for _, rule in self.association_rules_df.iterrows():
            antecedents = rule["antecedents"]
            consequents = rule["consequents"]
            confidence = rule["confidence"]

            # Create recommendations from antecedents to consequents
            for ant_item in antecedents:
                for cons_item in consequents:
                    self.item_recommendations[ant_item].append((cons_item, confidence))

        # Sort recommendations by confidence (descending)
        for item in self.item_recommendations:
            self.item_recommendations[item].sort(key=lambda x: x[1], reverse=True)

    def recommend(
        self, user_id: str, num_items: int, user_items: Optional[Set[str]] = None
    ) -> list[str]:
        """
        Generate recommendations for a user based on their interaction history
        """
        if user_items is None:
            user_items = set()

        if not user_items or not self.item_recommendations:
            return []

        # Score items based on association rules
        item_scores = defaultdict(float)

        for user_item in user_items:
            if user_item in self.item_recommendations:
                for recommended_item, confidence in self.item_recommendations[
                    user_item
                ]:
                    if (
                        recommended_item not in user_items
                    ):  # Don't recommend items user already has
                        item_scores[recommended_item] += confidence

        # Sort by score and return top N
        sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
        return [item for item, score in sorted_items[:num_items]]

    def get_frequent_itemsets(self) -> Optional[pd.DataFrame]:
        """Return the frequent itemsets DataFrame"""
        return self.frequent_itemsets

    def get_association_rules(self) -> Optional[pd.DataFrame]:
        """Return the association rules DataFrame"""
        return self.association_rules_df

    def get_item_recommendations_dict(self) -> Dict[str, List[tuple[str, float]]]:
        """Return the item-to-item recommendations dictionary"""
        return dict(self.item_recommendations)
