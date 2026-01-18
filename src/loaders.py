from typing import List, Set

import pandas as pd
from pymongo import MongoClient

from .base import BaseDatasetLoader
from .constants import MONGO_DB, MONGO_URI
from .entities.dataset import CSVDataset, MongoDataset


class CSVDatasetLoader(BaseDatasetLoader):
    def load(self, *, file_path: str):
        """
        Load data from a CSV file and convert it into a Pandas DataFrame.
        Finally, return the CSVDataset domain entity.
        """

        df = pd.read_csv(file_path)
        return CSVDataset(
            pandas_df=df,
        )


class MongoDatasetLoader(BaseDatasetLoader):
    def __init__(self, uri: str = MONGO_URI, db_name: str = MONGO_DB):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def load(self, *, collection_name: str = "Enrollments"):
        """Load interactions from MongoDB collection (Enrollments by default)."""
        cursor = self.db[collection_name].find({"user_id": {"$ne": None}})
        records = []
        for doc in cursor:
            records.append(
                {
                    "user_id": str(doc.get("user_id")),
                    "item_id": str(doc.get("course_id")),
                    "interaction": 1,
                    "timestamp": doc.get("enrolledAt") or doc.get("viewedAt"),
                }
            )

        if not records:
            df = pd.DataFrame(
                columns=["user_id", "item_id", "interaction", "timestamp"]
            )
        else:
            df = pd.DataFrame(records)
        return MongoDataset(pandas_df=df)

    def load_courses_popularity(self, n: int = 100):
        """Load popular courses directly from Courses collection views field.
        
        Using 'Courses' collection because 'Enrollments' and 'CourseViews' 
        currently have insufficient data for the demo.
        """
        cursor = (
            self.db["Courses"]
            .find({"views": {"$gt": 0}}, {"_id": 1, "views": 1})
            .sort("views", -1)
            .limit(n)
        )

        records = []
        for doc in cursor:
            records.append(
                {
                    "item_id": str(doc["_id"]),
                    "interaction": doc.get("views", 0),
                }
            )

        if not records:
            df = pd.DataFrame(columns=["item_id", "interaction"])
        else:
            df = pd.DataFrame(records)
            
        return MongoDataset(
            pandas_df=df,
            user_col="user_id",
            item_col="item_id",
            interaction_col="interaction",
            timestamp_col="timestamp",
        )

    def load_courses_by_tags(self, max_transaction_size: int = 20):
        """Load courses grouped by learner_tags for FP-Growth transactions.

        Creates transactions per course (each course's tags become a basket of related courses).
        This is faster and more meaningful than grouping all courses by single tags.
        """
        cursor = (
            self.db["Courses"]
            .find(
                {"learner_tags": {"$exists": True, "$ne": []}},
                {"_id": 1, "learner_tags": 1},
            )
            .limit(500)
        )  # Limit courses to process

        # Build tag -> courses mapping first
        tag_to_courses = {}
        all_courses = []
        for doc in cursor:
            course_id = str(doc["_id"])
            tags = doc.get("learner_tags", [])
            all_courses.append((course_id, tags))
            for tag in tags:
                if tag not in tag_to_courses:
                    tag_to_courses[tag] = set()
                tag_to_courses[tag].add(course_id)

        # Create transactions: for each course, find related courses (share at least 2 tags)
        transactions = []
        for course_id, tags in all_courses:
            related = set()
            for tag in tags:
                related.update(tag_to_courses.get(tag, set()))
            related.discard(course_id)  # Remove self
            if len(related) >= 2:
                # Limit transaction size
                transaction = [course_id] + list(related)[: max_transaction_size - 1]
                transactions.append(transaction)

        return transactions

    def load_user_baskets(self) -> List[List[str]]:
        """Load user baskets (enrollments) for FP-Growth basket analysis.

        Each user's enrolled courses form a transaction/basket.
        This is the proper way to do market basket analysis.
        """
        # Get all enrollments grouped by user
        pipeline = [
            {"$group": {"_id": "$user_id", "courses": {"$addToSet": "$course_id"}}},
            {
                "$match": {
                    "courses.1": {"$exists": True}  # Only users with 2+ courses
                }
            },
        ]

        cursor = self.db["Enrollments"].aggregate(pipeline)
        transactions = []
        for doc in cursor:
            courses = [str(c) for c in doc.get("courses", [])]
            if len(courses) >= 2:
                transactions.append(courses)

        # If not enough enrollment data, also use CourseViews
        if len(transactions) < 1:
            view_pipeline = [
                {"$group": {"_id": "$user_id", "courses": {"$addToSet": "$course_id"}}},
                {"$match": {"courses.1": {"$exists": True}}},
            ]
            view_cursor = self.db["CourseViews"].aggregate(view_pipeline)
            for doc in view_cursor:
                courses = [str(c) for c in doc.get("courses", [])]
                if len(courses) >= 2:
                    transactions.append(courses)

        return transactions

    def get_user_courses(self, user_id: str) -> List[str]:
        """Get all courses a user has enrolled in or viewed, sorted by latest interaction."""
        from bson import ObjectId

        # Map course_id -> timestamp
        # We use a dict to deduplicate, keeping the latest timestamp
        course_timestamps = {}

        # Try both string and ObjectId formats
        query_variants = [{"user_id": user_id}]
        try:
            query_variants.append({"user_id": ObjectId(user_id)})
        except Exception:
            pass  # Invalid ObjectId format, skip

        def _update_course_ts(c_id, ts):
            if not c_id:
                return
            c_id = str(c_id)
            # Normalize timestamp to 0 if missing
            ts_val = 0
            if ts:
                if hasattr(ts, "timestamp"):
                    ts_val = ts.timestamp()
                else:
                    try:
                        ts_val = float(ts)
                    except (ValueError, TypeError):
                        ts_val = 0
            
            if c_id not in course_timestamps or ts_val > course_timestamps[c_id]:
                course_timestamps[c_id] = ts_val

        # Get enrolled courses
        for query in query_variants:
            enrollments = self.db["Enrollments"].find(query)
            for doc in enrollments:
                _update_course_ts(doc.get("course_id"), doc.get("enrolledAt"))

        # Get viewed courses
        for query in query_variants:
            views = self.db["CourseViews"].find(query)
            for doc in views:
                _update_course_ts(doc.get("course_id"), doc.get("viewedAt"))

        # Sort by timestamp descending
        sorted_courses = sorted(
            course_timestamps.items(), key=lambda x: x[1], reverse=True
        )
        return [c[0] for c in sorted_courses]
