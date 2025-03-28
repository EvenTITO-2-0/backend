# flake8: noqa
from app.database.database import engine
from app.database.session_dep import get_db
from app.database.models.base import Base
from app.database.models.payment import PaymentModel
from app.database.models.reviewer import ReviewerModel
from app.database.models.work import WorkModel
from app.database.models.submission import SubmissionModel
from app.database.models.review import ReviewModel
from app.database.models.organizer import OrganizerModel
from app.database.models.inscription import InscriptionModel
from app.database.models.event import EventModel
from app.database.models.user import UserModel
from app.database.models.chair import ChairModel
import asyncio
from app.schemas.users.user import UserReply
from app.repository.users_repository import UsersRepository
from app.database.models.user import UserRole
import sys
import os
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)
load_dotenv()


async def add_first_admin():
    db_gen = get_db()
    db = await anext(db_gen)

    name = os.getenv("ADMIN_NAME")
    lastname = os.getenv("ADMIN_LASTNAME")
    email = os.getenv("ADMIN_EMAIL")
    admin_id = os.getenv("ADMIN_ID")
    print(f"Adding admin: {name}, {lastname}, {email}, {admin_id}")

    repository = UsersRepository(db)
    admin_user = UserReply(id=admin_id, role=UserRole.ADMIN, name=name, lastname=lastname, email=email)
    await repository.create(admin_user)
    print("SUCCESS")


async def create_models():
    try:
        print("Creating DB Connection...")
        async with engine.begin() as conn:
            print("SUCCESS")
            print("Drop all tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("SUCCESS")
            print("Creating all tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("SUCCESS")
        await add_first_admin()
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(create_models())
