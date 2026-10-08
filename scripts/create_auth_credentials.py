from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models.user import User, AuthCredential


def migrate_users():
    db: Session = SessionLocal()

    try:
        users = db.query(User).all()

        for user in users:

            if user.password is None:
                continue

            existing = (
                db.query(AuthCredential)
                .filter(
                    AuthCredential.user_id == user.user_id,
                    AuthCredential.designation
                    == user.designation,
                )
                .first()
            )

            if existing:
                continue

            hashed = hash_password(
                str(user.password)
            )

            credential = AuthCredential(
                user_id=user.user_id,
                designation=user.designation,
                password_hash=hashed,
            )

            db.add(credential)

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    migrate_users()