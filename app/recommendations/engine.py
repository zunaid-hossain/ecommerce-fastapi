import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.user import User
from app.models.interaction import UserInteraction
from app.config import settings
import requests


class HybridRecommendationEngine:
    """
    Lightweight Context-Aware Hybrid Recommendation System with Cold-Start Handling
    
    Approach:
    1. Collaborative Filtering: User-Product interaction matrix
    2. Content-Based: Product similarity based on features
    3. Context-Aware: Time, popularity, trends
    4. Cold-Start: Trending products, category-based recommendations
    """

    def __init__(self, db: Session):
        self.db = db
        self.min_similarity = settings.MIN_SIMILARITY_THRESHOLD
        self.top_n = settings.TOP_N_RECOMMENDATIONS

    def get_personalized_recommendations(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get personalized recommendations for a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return self._get_trending_products(limit)

        # Check if user is cold-start (new user)
        user_interactions = self.db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id
        ).count()

        if user_interactions == 0:
            # Cold-start: Return trending products
            return self._get_trending_products(limit)

        # Get user's interaction history
        user_history = self.db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id
        ).all()

        # Weighted scoring based on interaction type
        interaction_weights = {
            "purchase": 3.0,
            "review": 2.5,
            "add_to_cart": 1.5,
            "view": 1.0
        }

        # Calculate user preference vector
        user_prefs = {}
        for interaction in user_history:
            weight = interaction_weights.get(interaction.interaction_type, 1.0)
            if interaction.product_id not in user_prefs:
                user_prefs[interaction.product_id] = 0
            user_prefs[interaction.product_id] += weight

        # Hybrid scoring
        recommendations = {}
        all_products = self.db.query(Product).all()

        for product in all_products:
            if product.id in user_prefs:
                continue  # Skip already interacted products

            score = 0

            # 1. Collaborative signal (similar users who bought this)
            collab_score = self._collaborative_score(user_id, product.id, user_history)
            score += collab_score * 0.4

            # 2. Content-based signal (product features similarity)
            content_score = self._content_based_score(user_history, product)
            score += content_score * 0.3

            # 3. Context-aware signal (popularity, ratings, recency)
            context_score = self._context_aware_score(product)
            score += context_score * 0.3

            if score > 0:
                recommendations[product.id] = {
                    "product": product,
                    "score": score,
                    "confidence": min(score, 1.0)
                }

        # Sort by score and return top-n
        sorted_recs = sorted(recommendations.items(), key=lambda x: x[1]["score"], reverse=True)
        return [
            {
                "id": rec[0],
                "name": rec[1]["product"].name,
                "price": rec[1]["product"].price,
                "image_url": rec[1]["product"].image_url,
                "rating": rec[1]["product"].rating,
                "confidence": rec[1]["confidence"],
                "reason": "Personalized for you"
            }
            for rec in sorted_recs[:limit]
        ]

    def get_similar_products(self, product_id: int, limit: int = 5) -> List[Dict]:
        """Get products similar to the given product"""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return []

        similar_products = {}
        all_products = self.db.query(Product).filter(Product.id != product_id).all()

        for other_product in all_products:
            # Content similarity (price range, categories, features)
            similarity = self._calculate_product_similarity(product, other_product)

            if similarity > self.min_similarity:
                similar_products[other_product.id] = {
                    "product": other_product,
                    "similarity": similarity
                }

        sorted_similar = sorted(similar_products.items(), key=lambda x: x[1]["similarity"], reverse=True)
        return [
            {
                "id": sim[0],
                "name": sim[1]["product"].name,
                "price": sim[1]["product"].price,
                "image_url": sim[1]["product"].image_url,
                "rating": sim[1]["product"].rating,
                "similarity": sim[1]["similarity"],
                "reason": "Similar to your browsing"
            }
            for sim in sorted_similar[:limit]
        ]

    def _get_trending_products(self, limit: int = 5) -> List[Dict]:
        """Get trending products for cold-start users"""
        # Rank by: views * 0.3 + rating * 0.4 + recent_purchases * 0.3
        all_products = self.db.query(Product).all()

        trending = []
        for product in all_products:
            # Count recent purchases
            recent_purchases = self.db.query(UserInteraction).filter(
                UserInteraction.product_id == product.id,
                UserInteraction.interaction_type == "purchase"
            ).count()

            trend_score = (
                (product.views * 0.3) +
                (product.rating * 10 * 0.4) +
                (recent_purchases * 0.3)
            )

            trending.append({
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "image_url": product.image_url,
                "rating": product.rating,
                "trend_score": trend_score,
                "confidence": 0.7,
                "reason": "Trending now"
            })

        return sorted(trending, key=lambda x: x["trend_score"], reverse=True)[:limit]

    def _collaborative_score(self, user_id: int, product_id: int, user_history: List[UserInteraction]) -> float:
        """Calculate collaborative filtering score"""
        # Find other users who bought products the user bought
        user_bought_products = [i.product_id for i in user_history if i.interaction_type == "purchase"]

        if not user_bought_products:
            return 0.0

        # Find users with similar purchase history
        similar_users = self.db.query(UserInteraction).filter(
            UserInteraction.product_id.in_(user_bought_products),
            UserInteraction.user_id != user_id,
            UserInteraction.interaction_type == "purchase"
        ).all()

        # Count how many similar users also bought this product
        similar_users_bought = self.db.query(UserInteraction).filter(
            UserInteraction.user_id.in_([su.user_id for su in similar_users]),
            UserInteraction.product_id == product_id,
            UserInteraction.interaction_type == "purchase"
        ).count()

        return min(similar_users_bought / max(len(similar_users), 1), 1.0)

    def _content_based_score(self, user_history: List[UserInteraction], product: Product) -> float:
        """Calculate content-based filtering score"""
        if not user_history:
            return 0.0

        # Get products the user interacted with
        interacted_products = self.db.query(Product).filter(
            Product.id.in_([i.product_id for i in user_history])
        ).all()

        if not interacted_products:
            return 0.0

        # Calculate average similarity to user's products
        similarities = [
            self._calculate_product_similarity(ip, product)
            for ip in interacted_products
        ]

        return np.mean(similarities) if similarities else 0.0

    def _context_aware_score(self, product: Product) -> float:
        """Calculate context-aware score based on popularity and ratings"""
        # Normalize views (0-1)
        all_products = self.db.query(Product).all()
        max_views = max([p.views for p in all_products], default=1)
        normalized_views = product.views / max(max_views, 1)

        # Rating score (0-1)
        rating_score = product.rating / 5.0 if product.rating > 0 else 0.0

        # Combine
        return (normalized_views * 0.5) + (rating_score * 0.5)

    def _calculate_product_similarity(self, product1: Product, product2: Product) -> float:
        """Calculate similarity between two products"""
        similarity_score = 0.0
        weight_sum = 0.0

        # 1. Price similarity (inverse of price difference)
        price_diff = abs(product1.price - product2.price)
        max_price = max(product1.price, product2.price)
        if max_price > 0:
            price_similarity = 1.0 - (price_diff / max_price)
            similarity_score += price_similarity * 0.3
            weight_sum += 0.3

        # 2. Rating similarity
        if product1.rating > 0 and product2.rating > 0:
            rating_diff = abs(product1.rating - product2.rating)
            rating_similarity = 1.0 - (rating_diff / 5.0)
            similarity_score += rating_similarity * 0.3
            weight_sum += 0.3

        # 3. Category overlap
        shared_categories = len(set(product1.categories) & set(product2.categories))
        total_categories = len(set(product1.categories) | set(product2.categories))
        if total_categories > 0:
            category_similarity = shared_categories / total_categories
            similarity_score += category_similarity * 0.4
            weight_sum += 0.4

        return similarity_score / weight_sum if weight_sum > 0 else 0.0

    def record_interaction(self, user_id: int, product_id: int, interaction_type: str, rating: float = None):
        """Record user-product interaction"""
        interaction = UserInteraction(
            user_id=user_id,
            product_id=product_id,
            interaction_type=interaction_type,
            rating=rating
        )
        self.db.add(interaction)
        self.db.commit()

    def fetch_external_products(self, category: str = None, limit: int = 10) -> List[Dict]:
        """Fetch products from external API (e.g., fakestoreapi)"""
        try:
            url = "https://fakestoreapi.com/products"
            if limit:
                url += f"?limit={limit}"

            response = requests.get(url, timeout=5)
            response.raise_for_status()
            products = response.json()

            # Map to internal format
            return [
                {
                    "name": p.get("title", ""),
                    "description": p.get("description", ""),
                    "price": float(p.get("price", 0)),
                    "image_url": p.get("image", ""),
                    "external_id": p.get("id"),
                    "source": "fakestoreapi"
                }
                for p in products
            ]
        except Exception as e:
            print(f"Error fetching external products: {e}")
            return []
