import factory
from flaskr.models.trip import TripSession, TripParticipant
from flaskr.models.user import User
import uuid

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User

    name = "test_user"
