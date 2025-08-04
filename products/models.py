# products/models.py

from mongoengine import (
    Document,
    StringField,
    FloatField,
    ListField,
    DictField,
    BooleanField,
    IntField,
)


class Product(Document):
    _id = StringField(primary_key=True)  # Always a string
    product_name = StringField(max_length=255)
    category = StringField(max_length=100)
    description = StringField()
    price = FloatField()
    ingredients = ListField(StringField(max_length=255))
    images = ListField(StringField())
    variations = ListField(DictField())
    weight = FloatField(null=True, blank=True)
    dimensions = StringField(max_length=255, null=True, blank=True)
    benefits = ListField(StringField(max_length=255))
    scent_profile = StringField(max_length=255, null=True, blank=True)
    variants = ListField(DictField(), default=list)
    tags = ListField(StringField(max_length=255))
    availability = BooleanField(default=True)
    inventory = IntField(default=0)
    reserved_inventory = IntField(default=0)
    average_rating = FloatField(default=0.0)
    review_count = IntField(default=0)
    approved_review_count = IntField(default=0)

    meta = {
        "indexes": [
            "category",
            "tags",
            "product_name",
        ]
    }

    def __str__(self):
        return self.product_name

    @property
    def id_str(self):
        return str(self._id)

    def add_review(self, rating: int, status: str) -> None:
        """Increment review counts and update average rating."""
        self.review_count += 1
        if status == "approved":
            if self.approved_review_count == 0:
                self.average_rating = rating
            else:
                self.average_rating = (
                    (self.average_rating * self.approved_review_count) + rating
                ) / (self.approved_review_count + 1)
            self.approved_review_count += 1
        self.save()

    def update_review(
        self,
        old_rating: int,
        new_rating: int,
        old_status: str,
        new_status: str,
    ) -> None:
        """Update rating averages when a review changes."""
        if old_status == "approved" and new_status == "approved":
            if self.approved_review_count > 0:
                self.average_rating = (
                    (self.average_rating * self.approved_review_count)
                    - old_rating
                    + new_rating
                ) / self.approved_review_count
        elif old_status != "approved" and new_status == "approved":
            if self.approved_review_count == 0:
                self.average_rating = new_rating
            else:
                self.average_rating = (
                    (self.average_rating * self.approved_review_count) + new_rating
                ) / (self.approved_review_count + 1)
            self.approved_review_count += 1
        elif old_status == "approved" and new_status != "approved":
            if self.approved_review_count > 1:
                self.average_rating = (
                    (self.average_rating * self.approved_review_count) - old_rating
                ) / (self.approved_review_count - 1)
            else:
                self.average_rating = 0.0
            self.approved_review_count -= 1
        self.save()

    def remove_review(self, rating: int, status: str) -> None:
        """Decrement review counts and update rating on deletion."""
        if status == "approved":
            if self.approved_review_count > 1:
                self.average_rating = (
                    (self.average_rating * self.approved_review_count) - rating
                ) / (self.approved_review_count - 1)
            else:
                self.average_rating = 0.0
            self.approved_review_count -= 1
        self.review_count -= 1
        self.save()


class Category(Document):
    _id = StringField(primary_key=True)  # Use string primary key for references
    name = StringField(max_length=100, required=True, unique=True)
    description = StringField(null=True, blank=True)

    def __str__(self):
        return self.name
