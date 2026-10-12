from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.book import Book
from app.models.author import Author
from app.models.book_category import BookCategory
from app.models.category import Category, Subcategory
from app.schemas.admin_book import BookCreate, BookDeleteResponse


router = APIRouter(
    prefix="/api/v1/super-admin/books",
    tags=["Super Administrator - Books"],
)


def require_super_admin(
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("designation") != "Super Administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Administrator access required.",
        )

    return current_user


# --------------------------------------------------
# CREATE BOOK
# POST /api/v1/super-admin/books
# --------------------------------------------------

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_book(
    request: BookCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    existing = (
        db.query(Book)
        .filter(Book.isbn == request.isbn)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A book with this ISBN already exists.",
        )

    # Validate the category.
    category = db.get(Category, request.category)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The specified category does not exist.",
        )

    # Avoid duplicate subcategories in the request.
    if len(request.subcategories) != len(set(request.subcategories)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Duplicate subcategories are not allowed.",
        )

    # Validate that every subcategory belongs to this category.
    for subcategory_name in request.subcategories:
        subcategory = db.get(
            Subcategory,
            (request.category, subcategory_name),
        )

        if subcategory is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Subcategory '{subcategory_name}' does not exist "
                    f"under category '{request.category}'."
                ),
            )

    try:
        book = Book(
            isbn=request.isbn,
            title=request.title,
            type=request.type,
            price_r=request.price_r,
            price_b=request.price_b,
            quantity=request.quantity,
            publisher=request.publisher,
            publication_date=request.publication_date,
            edition_number=request.edition_number,
            language=request.language,
            format=request.format,
        )

        db.add(book)
        db.flush()

        # Insert author mappings.
        for author_name in request.authors:
            db.add(
                Author(
                    isbn=request.isbn,
                    author=author_name,
                )
            )

        # Insert book-category mappings.
        for subcategory_name in request.subcategories:
            db.add(
                BookCategory(
                    isbn=request.isbn,
                    category=request.category,
                    subcategory=subcategory_name,
                )
            )

        # An empty subcategory represents a category-only association.
        if not request.subcategories:
            db.add(
                BookCategory(
                    isbn=request.isbn,
                    category=request.category,
                    subcategory="",
                )
            )

        db.commit()
        db.refresh(book)

        return {
            "message": "Book created successfully.",
            "book": {
                "isbn": book.isbn,
                "title": book.title,
                "quantity": book.quantity,
            },
        }

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Book creation failed because of a database constraint. "
                "Check the ISBN, author mappings, and category mappings."
            ),
        ) from exc

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# DELETE BOOK
# DELETE /api/v1/super-admin/books/{isbn}
# --------------------------------------------------

@router.delete(
    "/{isbn}",
    response_model=BookDeleteResponse,
)
def delete_book(
    isbn: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_super_admin),
):
    book = (
        db.query(Book)
        .filter(Book.isbn == isbn)
        .first()
    )

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found.",
        )

    try:
        # Remove mappings before deleting the book.
        db.query(Author).filter(
            Author.isbn == isbn
        ).delete(synchronize_session=False)

        db.query(BookCategory).filter(
            BookCategory.isbn == isbn
        ).delete(synchronize_session=False)

        db.delete(book)
        db.commit()

        return {
            "isbn": isbn,
            "message": "Book deleted successfully.",
        }

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This book is referenced by another record and cannot "
                "be deleted without affecting existing data."
            ),
        ) from exc

    except Exception:
        db.rollback()
        raise