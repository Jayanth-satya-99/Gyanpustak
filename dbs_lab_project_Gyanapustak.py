import mysql.connector
import os
from datetime import date

# ─────────────────────────────────────────────
#  DB CONNECTION
# ─────────────────────────────────────────────
def get_conn():
    return mysql.connector.connect(
        host="localhost",
        user="DBMS",
        password="Dbms@123",
        database="gyanpustak"
    )

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def header(title):
    print("\n" + "=" * 55)
    print(f"  GyanPustak  |  {title}")
    print("=" * 55)

def divider():
    print("-" * 55)

def pause():
    input("\n  Press Enter to continue...")

def menu(options):
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    print("  [0] Back / Logout")
    return input("\n  Choice: ").strip()

def print_table(rows, columns):
    if not rows:
        print("  (no records found)")
        return
    col_widths = [
        max(len(str(c)), max((len(str(r[i])) for r in rows), default=0))
        for i, c in enumerate(columns)
    ]
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in col_widths)
    divider()
    print(fmt.format(*columns))
    divider()
    for row in rows:
        print(fmt.format(*[str(v) if v is not None else "-" for v in row]))
    divider()

def fetch(query, params=()):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def execute(query, params=()):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    cur.close()
    conn.close()

def execute_many(queries_params):
    conn = get_conn()
    cur  = conn.cursor()
    for q, p in queries_params:
        cur.execute(q, p)
    conn.commit()
    cur.close()
    conn.close()

# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────
def login():
    header("Login")
    print("  Designations: Student | Customer Support | Administrator | Super Administrator")
    designation = input("  Designation : ").strip()
    user_id     = input("  User ID     : ").strip()
    password    = input("  Password    : ").strip()

    rows = fetch(
        "SELECT USER_ID, DESIGNATION FROM USER WHERE USER_ID=%s AND PASSWORD=%s AND DESIGNATION=%s",
        (user_id, password, designation)
    )
    if rows:
        print(f"\n  Welcome! Logged in as {rows[0][1]} (ID: {rows[0][0]})")
        pause()
        return {"id": rows[0][0], "designation": rows[0][1]}
    else:
        print("\n  Invalid credentials.")
        pause()
        return None

# ─────────────────────────────────────────────
#  BROWSE BOOKS  (shared)
# ─────────────────────────────────────────────
def browse_books():
    while True:
        header("Browse Books")
        choice = menu(["View all books", "Search by title",
                       "Search by author", "Search by category",
                       "View book details & reviews"])
        if choice == "0":
            break
        elif choice == "1":
            header("All Books")
            rows = fetch("SELECT ISBN, TITLE, TYPE, PRICE_B, PRICE_R, FORMAT, QUANTITY FROM BOOK ORDER BY TITLE")
            print_table(rows, ["ISBN","Title","Type","Price(Buy)","Price(Rent)","Format","Qty"])
            pause()
        elif choice == "2":
            header("Search by Title")
            kw = input("  Keyword: ").strip()
            rows = fetch("SELECT ISBN, TITLE, TYPE, PRICE_B, PRICE_R, FORMAT FROM BOOK WHERE TITLE LIKE %s",
                         (f"%{kw}%",))
            print_table(rows, ["ISBN","Title","Type","Price(Buy)","Price(Rent)","Format"])
            pause()
        elif choice == "3":
            header("Search by Author")
            kw = input("  Author name: ").strip()
            rows = fetch("""
                SELECT b.ISBN, b.TITLE, a.AUTHOR, b.PRICE_B, b.PRICE_R
                FROM BOOK b JOIN AUTHORS a ON b.ISBN=a.ISBN WHERE a.AUTHOR LIKE %s
            """, (f"%{kw}%",))
            print_table(rows, ["ISBN","Title","Author","Price(Buy)","Price(Rent)"])
            pause()
        elif choice == "4":
            header("Search by Category")
            kw = input("  Category/Subcategory: ").strip()
            rows = fetch("""
                SELECT b.ISBN, b.TITLE, bc.CATEGORY, bc.SUBCATEGORY, b.PRICE_B, b.PRICE_R
                FROM BOOK b JOIN BOOK_CATEGORY bc ON b.ISBN=bc.ISBN
                WHERE bc.CATEGORY LIKE %s OR bc.SUBCATEGORY LIKE %s
            """, (f"%{kw}%", f"%{kw}%"))
            print_table(rows, ["ISBN","Title","Category","Subcategory","Price(Buy)","Price(Rent)"])
            pause()
        elif choice == "5":
            header("Book Details")
            isbn = input("  ISBN: ").strip()
            rows = fetch("SELECT * FROM BOOK WHERE ISBN=%s", (isbn,))
            if not rows:
                print("  Book not found.")
                pause()
                continue
            book = rows[0]
            fields = ["Type","Price(Rent)","Price(Buy)","Qty","Title","ISBN",
                      "Publisher","Pub Date","Edition","Language","Format"]
            divider()
            for f, v in zip(fields, book):
                print(f"  {f:<14}: {v}")
            authors = fetch("SELECT AUTHOR FROM AUTHORS WHERE ISBN=%s", (isbn,))
            print(f"  {'Authors':<14}: {', '.join(r[0] for r in authors)}")
            reviews = fetch("""
                SELECT s.NAME, rr.RATING, rr.REVIEW
                FROM REVIEW_RATING rr JOIN STUDENTS s ON rr.STUDENT_ID=s.STUDENT_ID
                WHERE rr.ISBN=%s
            """, (isbn,))
            divider()
            if reviews:
                print("  Reviews:")
                for r in reviews:
                    stars = "*" * r[1] + "-" * (5 - r[1])
                    print(f"    [{stars}]  {r[0]}: {r[2]}")
            else:
                print("  No reviews yet.")
            divider()
            pause()

# ─────────────────────────────────────────────
#  ADD BOOK  (admin + super admin)
# ─────────────────────────────────────────────
def add_book():
    header("Add New Book")
    isbn = input("  ISBN                          : ").strip()
    if fetch("SELECT 1 FROM BOOK WHERE ISBN=%s", (isbn,)):
        print("  A book with this ISBN already exists.")
        pause()
        return
    title     = input("  Title                         : ").strip()
    btype     = input("  Type (NEW/USED)               : ").strip().upper()
    price_b   = input("  Price (Buy, 0=not available)  : ").strip()
    price_r   = input("  Price (Rent, 0=not available) : ").strip()
    quantity  = input("  Quantity                      : ").strip()
    publisher = input("  Publisher                     : ").strip()
    pub_date  = input("  Publication Date (YYYY-MM-DD) : ").strip()
    edition   = input("  Edition Number                : ").strip()
    language  = input("  Language                      : ").strip()
    fmt       = input("  Format (HARDCOPY/SOFTCOPY/ELECTRONIC): ").strip().upper()
    author    = input("  Author(s) comma separated     : ").strip()
    category  = input("  Category                      : ").strip()
    subcat    = input("  Subcategory                   : ").strip()

    price_b_val = int(price_b) if price_b and price_b != "0" else None
    price_r_val = int(price_r) if price_r and price_r != "0" else None

    ops = [
        ("INSERT INTO BOOK VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
         (btype, price_r_val, price_b_val, int(quantity), title, isbn,
          publisher, pub_date, int(edition), language, fmt))
    ]
    for a in [x.strip() for x in author.split(",") if x.strip()]:
        ops.append(("INSERT INTO AUTHORS VALUES (%s,%s)", (isbn, a)))
    if category and subcat:
        ops.append(("INSERT INTO BOOK_CATEGORY VALUES (%s,%s,%s)", (category, isbn, subcat)))

    execute_many(ops)
    print(f"\n  Book '{title}' added successfully.")
    pause()

# ─────────────────────────────────────────────
#  INVENTORY  (admin + super admin)
# ─────────────────────────────────────────────
def update_inventory():
    header("Update Book Inventory")
    isbn = input("  ISBN: ").strip()
    rows = fetch("SELECT TITLE, QUANTITY FROM BOOK WHERE ISBN=%s", (isbn,))
    if not rows:
        print("  Book not found.")
        pause()
        return
    print(f"  Book: {rows[0][0]}  |  Current Qty: {rows[0][1]}")
    new_qty = input("  New quantity: ").strip()
    if not new_qty.isdigit():
        print("  Invalid quantity.")
        pause()
        return
    execute("UPDATE BOOK SET QUANTITY=%s WHERE ISBN=%s", (int(new_qty), isbn))
    print(f"  Inventory updated to {new_qty}.")
    pause()

# ─────────────────────────────────────────────
#  COURSE BOOKS  (admin + super admin)
# ─────────────────────────────────────────────
def add_course_book():
    header("Add Course-Required Book")
    rows = fetch("SELECT COURSE_ID, UNIVERSITY_ID, COURSE_NAME FROM COURSE")
    print_table(rows, ["Course ID","University ID","Course Name"])
    course_id = input("  Course ID    : ").strip()
    uni_id    = input("  University ID: ").strip()
    isbn      = input("  Book ISBN    : ").strip()
    if not fetch("SELECT 1 FROM BOOK WHERE ISBN=%s", (isbn,)):
        print("  Book not found.")
        pause()
        return
    if fetch("SELECT 1 FROM RECOMMEND WHERE COURSE_ID=%s AND UNIVERSITY_ID=%s AND ISBN=%s",
             (course_id, uni_id, isbn)):
        print("  Already linked.")
        pause()
        return
    execute("INSERT INTO RECOMMEND VALUES (%s,%s,%s)", (course_id, uni_id, isbn))
    print("  Book linked to course.")
    pause()

# ─────────────────────────────────────────────
#  TICKET HANDLING  (admin + super admin)
# ─────────────────────────────────────────────
def handle_tickets(emp_id):
    header("Handle My Tickets")
    rows = fetch("""
        SELECT t.TICKET_ID, t.TYPE, t.DATE_OF_CREATION, t.TITLE, t.TICKET_STATUS
        FROM TICKET t JOIN TICKET_FLOW tf ON t.TICKET_ID=tf.TICKET_ID
        WHERE tf.ASSIGNED_TO_ID=%s AND t.TICKET_STATUS IN ('assigned','in-process')
        ORDER BY t.DATE_OF_CREATION
    """, (emp_id,))
    if not rows:
        print("  No tickets assigned to you.")
        pause()
        return
    print_table(rows, ["Ticket ID","Type","Date","Title","Status"])

    ticket_id = input("  Ticket ID to handle: ").strip()
    t_rows = fetch("""
        SELECT t.TICKET_STATUS FROM TICKET t
        JOIN TICKET_FLOW tf ON t.TICKET_ID=tf.TICKET_ID
        WHERE t.TICKET_ID=%s AND tf.ASSIGNED_TO_ID=%s
    """, (ticket_id, emp_id))
    if not t_rows:
        print("  Ticket not found or not assigned to you.")
        pause()
        return

    current = t_rows[0][0]
    print(f"\n  Current status: {current}")

    if current == "assigned":
        print("  [1] Mark as in-process")
        print("  [2] Mark as completed")
        choice = input("  Choice: ").strip()
        if choice == "1":
            execute("UPDATE TICKET SET TICKET_STATUS='in-process' WHERE TICKET_ID=%s", (ticket_id,))
            print(f"  Ticket #{ticket_id} marked as in-process.")
        elif choice == "2":
            solution = input("  Solution description: ").strip()
            execute("""
                UPDATE TICKET SET TICKET_STATUS='completed',
                SOLUTION_DESCRIPTION=%s, COMPLETION_DATE=%s WHERE TICKET_ID=%s
            """, (solution, date.today(), ticket_id))
            print(f"  Ticket #{ticket_id} resolved and closed.")
        else:
            print("  Invalid choice.")
    elif current == "in-process":
        print("  [1] Mark as completed")
        choice = input("  Choice: ").strip()
        if choice == "1":
            solution = input("  Solution description: ").strip()
            execute("""
                UPDATE TICKET SET TICKET_STATUS='completed',
                SOLUTION_DESCRIPTION=%s, COMPLETION_DATE=%s WHERE TICKET_ID=%s
            """, (solution, date.today(), ticket_id))
            print(f"  Ticket #{ticket_id} resolved and closed.")
        else:
            print("  Invalid choice.")
    pause()

# ─────────────────────────────────────────────
#  VIEW MY TICKET STATUS  (student + support)
# ─────────────────────────────────────────────
def view_my_tickets(user_id, designation):
    header("My Tickets")
    rows = fetch("""
        SELECT TICKET_ID, TYPE, DATE_OF_CREATION, TITLE,
               TICKET_STATUS, SOLUTION_DESCRIPTION, COMPLETION_DATE
        FROM TICKET
        WHERE USER_ID=%s AND CREATER=%s
        ORDER BY DATE_OF_CREATION DESC
    """, (user_id, designation))
    if not rows:
        print("  You have not raised any tickets.")
        pause()
        return
    print_table(rows, ["ID","Type","Date","Title","Status","Solution","Completed"])
    pause()

# ─────────────────────────────────────────────
#  BROWSE BOOKS BY UNIVERSITY -> COURSE (student)
# ─────────────────────────────────────────────
def browse_recommended_books():
    header("Recommended Books by Course")

    # Step 1: show all universities
    unis = fetch("SELECT UNIVERSITY_ID, UNIVERSITY_NAME FROM UNIVERSITY ORDER BY UNIVERSITY_ID")
    if not unis:
        print("  No universities found.")
        pause()
        return
    print_table(unis, ["University ID","University Name"])
    uni_id = input("  Choose University ID: ").strip()

    if not fetch("SELECT 1 FROM UNIVERSITY WHERE UNIVERSITY_ID=%s", (uni_id,)):
        print("  University not found.")
        pause()
        return

    # Step 2: show departments of that university
    depts = fetch("""
        SELECT DEPART_NAME FROM DEPARTMENT
        WHERE UNIVERSITY_ID=%s ORDER BY DEPART_NAME
    """, (uni_id,))
    if not depts:
        print("  No departments found for this university.")
        pause()
        return
    print("\n  Departments offered:")
    for d in depts:
        print(f"    - {d[0]}")

    # Step 3: show courses offered by that university
    courses = fetch("""
        SELECT c.COURSE_ID, c.COURSE_NAME, c.SEMESTER, c.YEAR, co.DEPART_NAME
        FROM COURSE c
        JOIN COURSE_OFFEREDBY co
          ON c.COURSE_ID=co.COURSE_ID AND c.UNIVERSITY_ID=co.UNIVERSITY_ID
        WHERE c.UNIVERSITY_ID=%s
        ORDER BY c.COURSE_NAME
    """, (uni_id,))
    if not courses:
        print("  No courses found for this university.")
        pause()
        return
    print()
    print_table(courses, ["Course ID","Course Name","Semester","Year","Department"])
    course_id = input("  Choose Course ID: ").strip()

    if not fetch("SELECT 1 FROM COURSE WHERE COURSE_ID=%s AND UNIVERSITY_ID=%s",
                 (course_id, uni_id)):
        print("  Course not found.")
        pause()
        return

    # Step 4: show recommended books
    books = fetch("""
        SELECT b.ISBN, b.TITLE, b.TYPE, b.PRICE_B, b.PRICE_R, b.FORMAT
        FROM RECOMMEND r JOIN BOOK b ON r.ISBN=b.ISBN
        WHERE r.COURSE_ID=%s AND r.UNIVERSITY_ID=%s
    """, (course_id, uni_id))
    if not books:
        print("  No books recommended for this course.")
        pause()
        return
    header("Recommended Books")
    print_table(books, ["ISBN","Title","Type","Price(Buy)","Price(Rent)","Format"])
    pause()

# ─────────────────────────────────────────────
#  STUDENT PORTAL
# ─────────────────────────────────────────────
def student_portal(user):
    student_id = user["id"]
    while True:
        header(f"Student Portal | ID: {student_id}")
        choice = menu([
            "Browse books", "View my cart", "Add book to cart",
            "Checkout", "View my orders", "Request order cancellation",
            "Write a review", "Submit trouble ticket", "View my profile",
            "View my ticket status", "Browse books by course"
        ])
        if choice == "0":
            break
        elif choice == "1":
            browse_books()
        elif choice == "2":
            view_cart(student_id)
        elif choice == "3":
            add_to_cart(student_id)
        elif choice == "4":
            checkout(student_id)
        elif choice == "5":
            view_orders(student_id)
        elif choice == "6":
            request_cancellation(student_id)
        elif choice == "7":
            write_review(student_id)
        elif choice == "8":
            submit_ticket(student_id, "Student")
        elif choice == "9":
            view_student_profile(student_id)
        elif choice == "10":
            view_my_tickets(student_id, "Student")
        elif choice == "11":
            browse_recommended_books()

def view_cart(student_id):
    header("My Cart")
    cart = fetch("SELECT CART_ID, DATE_CREATE, DATE_LAST_UPDATE FROM CARTS WHERE STUDENT_ID=%s AND STATUS1='Active'",
                 (student_id,))
    if not cart:
        print("  Your cart is empty.")
        pause()
        return
    cart_id = cart[0][0]
    print(f"  Cart ID: {cart_id}  |  Created: {cart[0][1]}  |  Updated: {cart[0][2]}")
    items = fetch("""
        SELECT b.ISBN, b.TITLE, b.PRICE_B, b.PRICE_R, cc.PURCH_OPTION
        FROM CART_CONTAINS cc JOIN BOOK b ON cc.ISBN=b.ISBN WHERE cc.CART_ID=%s
    """, (cart_id,))
    print_table(items, ["ISBN","Title","Price(Buy)","Price(Rent)","Option"])
    total = sum(r[2] if r[4] == "Buy" else r[3] for r in items)
    print(f"\n  Total: Rs.{total}")
    pause()

def add_to_cart(student_id):
    header("Add to Cart")
    isbn = input("  ISBN: ").strip()
    book = fetch("SELECT TITLE, PRICE_R, PRICE_B, QUANTITY FROM BOOK WHERE ISBN=%s", (isbn,))
    if not book:
        print("  Book not found.")
        pause()
        return
    if book[0][3] == 0:
        print("  This book is out of stock.")
        pause()
        return
    purch_opt = input("  Purchase option (Buy/Rent): ").strip().capitalize()
    if purch_opt not in ("Buy", "Rent"):
        print("  Invalid option.")
        pause()
        return
    if purch_opt == "Rent" and book[0][1] is None:
        print("  This book is not available for rent.")
        pause()
        return
    if purch_opt == "Buy" and book[0][2] is None:
        print("  This book is not available for purchase.")
        pause()
        return

    cart_row = fetch("SELECT CART_ID FROM CARTS WHERE STUDENT_ID=%s AND STATUS1='Active'", (student_id,))
    if not cart_row:
        max_id  = fetch("SELECT MAX(CART_ID) FROM CARTS")
        cart_id = (max_id[0][0] or 1000) + 1
        ops = [
            ("INSERT INTO CARTS VALUES (%s,'Active',%s,%s,%s)",
             (student_id, cart_id, date.today(), date.today())),
            ("INSERT INTO CART_CONTAINS VALUES (%s,%s,%s)", (cart_id, isbn, purch_opt)),
            ("UPDATE BOOK SET QUANTITY=QUANTITY-1 WHERE ISBN=%s", (isbn,))
        ]
    else:
        cart_id = cart_row[0][0]
        if fetch("SELECT 1 FROM CART_CONTAINS WHERE CART_ID=%s AND ISBN=%s", (cart_id, isbn)):
            print("  Book already in cart.")
            pause()
            return
        ops = [
            ("UPDATE CARTS SET DATE_LAST_UPDATE=%s WHERE CART_ID=%s", (date.today(), cart_id)),
            ("INSERT INTO CART_CONTAINS VALUES (%s,%s,%s)", (cart_id, isbn, purch_opt)),
            ("UPDATE BOOK SET QUANTITY=QUANTITY-1 WHERE ISBN=%s", (isbn,))
        ]
    execute_many(ops)
    print(f"  '{book[0][0]}' added to cart.")
    pause()

def checkout(student_id):
    header("Checkout")
    cart_row = fetch("SELECT CART_ID FROM CARTS WHERE STUDENT_ID=%s AND STATUS1='Active'", (student_id,))
    if not cart_row:
        print("  Your cart is empty.")
        pause()
        return
    cart_id = cart_row[0][0]
    items = fetch("""
        SELECT b.TITLE, cc.PURCH_OPTION, b.PRICE_B, b.PRICE_R
        FROM CART_CONTAINS cc JOIN BOOK b ON cc.ISBN=b.ISBN WHERE cc.CART_ID=%s
    """, (cart_id,))
    if not items:
        print("  Your cart is empty.")
        pause()
        return

    print("\n  Items in your cart:")
    divider()
    total = 0
    for r in items:
        price = r[2] if r[1] == "Buy" else r[3]
        print(f"  {r[0]:<35} {r[1]:<6} Rs.{price}")
        total += price
    divider()
    print(f"  Total: Rs.{total}")

    confirm = input("\n  Proceed to payment? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("  Checkout cancelled.")
        pause()
        return

    print("  Shipping: [1] Standard  [2] 2-day  [3] 1-day")
    ship_map = {"1":"Standard","2":"2-day","3":"1-day"}
    ship    = ship_map.get(input("  Choice: ").strip(), "Standard")
    cc_num  = input("  Card number         : ").strip()
    cc_exp  = input("  Expiry (YYYY-MM-DD) : ").strip()
    cc_name = input("  Card holder name    : ").strip()
    cc_type = input("  Card type (Visa/MC) : ").strip()

    max_oid  = fetch("SELECT MAX(ORDER_ID) FROM ORDERS")
    order_id = (max_oid[0][0] or 2000) + 1
    ops = [
        ("INSERT INTO ORDERS VALUES (%s,%s,%s,NULL,%s,%s,%s,%s,%s,'new')",
         (order_id, cart_id, date.today(), ship, cc_num, cc_exp, cc_name, cc_type)),
        ("UPDATE CARTS SET STATUS1='Inactive' WHERE CART_ID=%s", (cart_id,))
    ]
    execute_many(ops)
    print(f"\n  Order #{order_id} placed successfully! Status: New")
    pause()

def view_orders(student_id):
    header("My Orders")
    rows = fetch("""
        SELECT o.ORDER_ID, o.DATE_CREATED, o.SHIPPING_TYPE, o.ORDER_STATUS, o.DATE_FULFILLED
        FROM ORDERS o JOIN CARTS c ON o.CART_ID=c.CART_ID WHERE c.STUDENT_ID=%s
    """, (student_id,))
    print_table(rows, ["Order ID","Date","Shipping","Status","Fulfilled"])
    pause()

def request_cancellation(student_id):
    header("Request Order Cancellation")
    rows = fetch("""
        SELECT o.ORDER_ID, o.DATE_CREATED, o.SHIPPING_TYPE, o.ORDER_STATUS
        FROM ORDERS o JOIN CARTS c ON o.CART_ID=c.CART_ID
        WHERE c.STUDENT_ID=%s AND o.ORDER_STATUS IN ('new','processed')
    """, (student_id,))
    if not rows:
        print("  No orders available for cancellation.")
        pause()
        return
    print_table(rows, ["Order ID","Date","Shipping","Status"])
    order_id = input("  Order ID to cancel: ").strip()

    row = fetch("""
        SELECT o.ORDER_STATUS FROM ORDERS o JOIN CARTS c ON o.CART_ID=c.CART_ID
        WHERE o.ORDER_ID=%s AND c.STUDENT_ID=%s
    """, (order_id, student_id))
    if not row:
        print("  Order not found.")
        pause()
        return
    if row[0][0] not in ('new','processed'):
        print(f"  Cannot cancel order with status '{row[0][0]}'.")
        pause()
        return
    if fetch("SELECT 1 FROM CANCELLATION_REQUEST WHERE ORDER_ID=%s AND REQUEST_STATUS='pending'",
             (order_id,)):
        print("  Cancellation already requested.")
        pause()
        return

    max_rid    = fetch("SELECT MAX(REQUEST_ID) FROM CANCELLATION_REQUEST")
    request_id = (max_rid[0][0] or 0) + 1
    ops = [
        ("INSERT INTO CANCELLATION_REQUEST VALUES (%s,%s,%s,%s,'pending')",
         (request_id, order_id, date.today(), row[0][0])),
        ("UPDATE ORDERS SET ORDER_STATUS='cancellation_requested' WHERE ORDER_ID=%s", (order_id,))
    ]
    execute_many(ops)
    print(f"  Cancellation requested for Order #{order_id}.")
    print("  Customer support will process your request.")
    pause()

def write_review(student_id):
    header("Write a Review")
    isbn = input("  ISBN: ").strip()
    book = fetch("SELECT TITLE FROM BOOK WHERE ISBN=%s", (isbn,))
    if not book:
        print("  Book not found.")
        pause()
        return
    if fetch("SELECT 1 FROM REVIEW_RATING WHERE ISBN=%s AND STUDENT_ID=%s", (isbn, student_id)):
        print("  You have already reviewed this book.")
        pause()
        return
    rating = input("  Rating (1-5): ").strip()
    review = input("  Review text : ").strip()
    if not rating.isdigit() or not (1 <= int(rating) <= 5):
        print("  Invalid rating.")
        pause()
        return
    execute("INSERT INTO REVIEW_RATING VALUES (%s,%s,%s,%s)",
            (isbn, student_id, review, int(rating)))
    print(f"  Review submitted for '{book[0][0]}'.")
    pause()

def submit_ticket(user_id, designation):
    header("Submit Trouble Ticket")
    print("  Categories: [1] User Profile  [2] Products  [3] Cart  [4] Orders  [5] Other")
    cat_map   = {"1":"User Profile","2":"Products","3":"Cart","4":"Orders","5":"Other"}
    cat       = cat_map.get(input("  Category: ").strip(), "Other")
    title     = input("  Title           : ").strip()
    problem   = input("  Problem desc    : ").strip()
    max_tid   = fetch("SELECT MAX(TICKET_ID) FROM TICKET")
    ticket_id = (max_tid[0][0] or 3000) + 1
    execute("""
        INSERT INTO TICKET(TYPE,DATE_OF_CREATION,TICKET_ID,USER_ID,CREATER,
        TITLE,PROBLEM_DESCRIPTION,TICKET_STATUS)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'new')
    """, (cat, date.today(), ticket_id, user_id, designation, title, problem))
    print(f"  Ticket #{ticket_id} submitted.")
    pause()

def view_student_profile(student_id):
    header("My Profile")
    rows = fetch("SELECT * FROM STUDENTS WHERE STUDENT_ID=%s", (student_id,))
    if rows:
        fields = ["Student ID","Name","Email","Phone","Address","DOB",
                  "University ID","Major","Status","Year of Study"]
        divider()
        for f, v in zip(fields, rows[0]):
            print(f"  {f:<16}: {v}")
        divider()
    pause()

# ─────────────────────────────────────────────
#  CUSTOMER SUPPORT PORTAL
# ─────────────────────────────────────────────
def support_portal(user):
    emp_id = user["id"]
    while True:
        header(f"Customer Support | ID: {emp_id}")
        choice = menu([
            "View all tickets", "View new tickets",
            "Assign ticket to administrator", "Create a ticket",
            "View my ticket status", "Process order cancellations",
            "Browse books"
        ])
        if choice == "0":
            break
        elif choice == "1":
            view_tickets(filter_status=None)
        elif choice == "2":
            view_tickets(filter_status="new")
        elif choice == "3":
            assign_ticket(emp_id)
        elif choice == "4":
            submit_ticket(emp_id, "Customer Support")
        elif choice == "5":
            view_my_tickets(emp_id, "Customer Support")
        elif choice == "6":
            process_cancellation()
        elif choice == "7":
            browse_books()

def view_tickets(filter_status=None):
    header("Tickets" + (f" — {filter_status}" if filter_status else " — All"))
    if filter_status:
        rows = fetch("""
            SELECT TICKET_ID, TYPE, DATE_OF_CREATION, TITLE, TICKET_STATUS, CREATER
            FROM TICKET WHERE TICKET_STATUS=%s ORDER BY DATE_OF_CREATION DESC
        """, (filter_status,))
    else:
        rows = fetch("""
            SELECT TICKET_ID, TYPE, DATE_OF_CREATION, TITLE, TICKET_STATUS, CREATER
            FROM TICKET ORDER BY DATE_OF_CREATION DESC
        """)
    print_table(rows, ["Ticket ID","Type","Date","Title","Status","Creator"])
    pause()

def assign_ticket(emp_id):
    header("Assign Ticket to Administrator")
    rows = fetch("SELECT TICKET_ID, TITLE, DATE_OF_CREATION, CREATER FROM TICKET WHERE TICKET_STATUS='new'")
    if not rows:
        print("  No new tickets to assign.")
        pause()
        return
    print_table(rows, ["Ticket ID","Title","Date","Creator"])

    ticket_id = input("  Ticket ID to assign: ").strip()
    row = fetch("SELECT TICKET_STATUS FROM TICKET WHERE TICKET_ID=%s", (ticket_id,))
    if not row:
        print("  Ticket not found.")
        pause()
        return
    if row[0][0] != "new":
        print(f"  Can only assign 'new' tickets. This ticket is '{row[0][0]}'.")
        pause()
        return

    admins = fetch("SELECT EMPLOYEE_ID, FIRST_NAME, LAST_NAME FROM EMPLOYEE WHERE DESIGNATION='Administrator'")
    if not admins:
        print("  No administrators available.")
        pause()
        return
    print("\n  Available Administrators:")
    for a in admins:
        print(f"    [{a[0]}] {a[1]} {a[2]}")

    admin_id = input("\n  Assign to Admin ID: ").strip()
    existing = fetch("SELECT 1 FROM TICKET_FLOW WHERE TICKET_ID=%s", (ticket_id,))
    if existing:
        ops = [
            ("UPDATE TICKET SET TICKET_STATUS='assigned' WHERE TICKET_ID=%s", (ticket_id,)),
            ("""UPDATE TICKET_FLOW SET ASSIGNED_BY='Customer Support',
                ASSIGNED_TO='Administrator', ASSIGNED_BY_ID=%s, ASSIGNED_TO_ID=%s
                WHERE TICKET_ID=%s""", (emp_id, admin_id, ticket_id))
        ]
    else:
        ops = [
            ("UPDATE TICKET SET TICKET_STATUS='assigned' WHERE TICKET_ID=%s", (ticket_id,)),
            ("INSERT INTO TICKET_FLOW VALUES (%s,'Customer Support','Administrator',%s,%s)",
             (ticket_id, emp_id, admin_id))
        ]
    execute_many(ops)
    print(f"  Ticket #{ticket_id} assigned to Admin #{admin_id}.")
    pause()

def process_cancellation():
    header("Process Order Cancellations")
    rows = fetch("""
        SELECT cr.REQUEST_ID, cr.ORDER_ID, cr.REQUEST_DATE, cr.ORIGINAL_STATUS
        FROM CANCELLATION_REQUEST cr WHERE cr.REQUEST_STATUS='pending'
    """)
    if not rows:
        print("  No cancellation requests pending.")
        pause()
        return
    print_table(rows, ["Req ID","Order ID","Date","Original Status"])

    request_id = input("  Request ID to process: ").strip()
    row = fetch("""
        SELECT cr.ORDER_ID, cr.ORIGINAL_STATUS, o.CART_ID
        FROM CANCELLATION_REQUEST cr JOIN ORDERS o ON cr.ORDER_ID=o.ORDER_ID
        WHERE cr.REQUEST_ID=%s AND cr.REQUEST_STATUS='pending'
    """, (request_id,))
    if not row:
        print("  Request not found.")
        pause()
        return

    order_id, original_status, cart_id = row[0]
    print(f"\n  Order #{order_id}  |  Original status: {original_status}")
    print("  [1] Approve cancellation")
    print("  [2] Reject cancellation")
    choice = input("  Choice: ").strip()

    if choice == "1":
        books = fetch("SELECT ISBN FROM CART_CONTAINS WHERE CART_ID=%s", (cart_id,))
        ops = [
            ("UPDATE ORDERS SET ORDER_STATUS='canceled' WHERE ORDER_ID=%s", (order_id,)),
            ("UPDATE CANCELLATION_REQUEST SET REQUEST_STATUS='approved' WHERE REQUEST_ID=%s", (request_id,))
        ]
        for b in books:
            ops.append(("UPDATE BOOK SET QUANTITY=QUANTITY+1 WHERE ISBN=%s", (b[0],)))
        execute_many(ops)
        print(f"  Order #{order_id} cancelled. Stock restored.")
    elif choice == "2":
        ops = [
            ("UPDATE ORDERS SET ORDER_STATUS=%s WHERE ORDER_ID=%s", (original_status, order_id)),
            ("UPDATE CANCELLATION_REQUEST SET REQUEST_STATUS='rejected' WHERE REQUEST_ID=%s", (request_id,))
        ]
        execute_many(ops)
        print(f"  Rejected. Order #{order_id} restored to '{original_status}'.")
    else:
        print("  Invalid choice.")
    pause()

# ─────────────────────────────────────────────
#  ADMINISTRATOR PORTAL
# ─────────────────────────────────────────────
def admin_portal(user):
    emp_id = user["id"]
    while True:
        header(f"Administrator | ID: {emp_id}")
        choice = menu([
            "View all tickets", "Handle my tickets",
            "Add new book", "Update book inventory",
            "Add course-required book", "Browse books"
        ])
        if choice == "0":
            break
        elif choice == "1":
            view_admin_tickets()
        elif choice == "2":
            handle_tickets(emp_id)
        elif choice == "3":
            add_book()
        elif choice == "4":
            update_inventory()
        elif choice == "5":
            add_course_book()
        elif choice == "6":
            browse_books()

def view_admin_tickets():
    header("All Tickets")
    rows = fetch("""
        SELECT TICKET_ID, TYPE, DATE_OF_CREATION, TITLE, TICKET_STATUS
        FROM TICKET WHERE TICKET_STATUS IN ('assigned','in-process','completed')
        ORDER BY DATE_OF_CREATION DESC
    """)
    print_table(rows, ["Ticket ID","Type","Date","Title","Status"])
    pause()

# ─────────────────────────────────────────────
#  SUPER ADMINISTRATOR PORTAL
# ─────────────────────────────────────────────
def super_admin_portal(user):
    emp_id = user["id"]
    while True:
        header(f"Super Administrator | ID: {emp_id}")
        choice = menu([
            "Add new employee", "View all employees",
            "View all tickets", "Handle my tickets",
            "Add new book", "Update book inventory",
            "Add course-required book", "Browse books"
        ])
        if choice == "0":
            break
        elif choice == "1":
            add_employee()
        elif choice == "2":
            view_all_employees()
        elif choice == "3":
            view_all_tickets_sa()
        elif choice == "4":
            handle_tickets(emp_id)
        elif choice == "5":
            add_book()
        elif choice == "6":
            update_inventory()
        elif choice == "7":
            add_course_book()
        elif choice == "8":
            browse_books()

def add_employee():
    header("Add New Employee")
    max_id     = fetch("SELECT MAX(EMPLOYEE_ID) FROM EMPLOYEE")
    emp_id_new = (max_id[0][0] or 500) + 1
    first    = input("  First name      : ").strip()
    last     = input("  Last name       : ").strip()
    gender   = input("  Gender (M/F)    : ").strip()
    salary   = input("  Salary          : ").strip()
    aadhar   = input("  Aadhaar number  : ").strip()
    email    = input("  Email           : ").strip()
    address  = input("  Address         : ").strip()
    phone    = input("  Phone           : ").strip()
    print("  Designation: [1] Customer Support  [2] Administrator")
    desig_map   = {"1":"Customer Support","2":"Administrator"}
    designation = desig_map.get(input("  Choice: ").strip())
    if not designation:
        print("  Invalid designation.")
        pause()
        return
    password = input("  Set login password (numeric): ").strip()
    ops = [
        ("INSERT INTO EMPLOYEE VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
         (emp_id_new, first, last, gender, salary, aadhar, email, address, phone, designation)),
        ("INSERT INTO USER VALUES (%s,%s,%s)", (emp_id_new, password, designation))
    ]
    execute_many(ops)
    print(f"  Employee #{emp_id_new} ({first} {last}) added as {designation}.")
    pause()

def view_all_employees():
    header("All Employees")
    rows = fetch("""
        SELECT EMPLOYEE_ID, FIRST_NAME, LAST_NAME, DESIGNATION, EMAIL, SALARY
        FROM EMPLOYEE ORDER BY DESIGNATION, EMPLOYEE_ID
    """)
    print_table(rows, ["ID","First Name","Last Name","Designation","Email","Salary"])
    pause()

def view_all_tickets_sa():
    header("All Tickets")
    rows = fetch("""
        SELECT TICKET_ID, TYPE, DATE_OF_CREATION, TITLE, TICKET_STATUS, CREATER
        FROM TICKET ORDER BY DATE_OF_CREATION DESC
    """)
    print_table(rows, ["Ticket ID","Type","Date","Title","Status","Creator"])
    pause()

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
PORTAL_MAP = {
    "Student":             student_portal,
    "Customer Support":    support_portal,
    "Administrator":       admin_portal,
    "Super Administrator": super_admin_portal,
}

def main():
    while True:
        header("Welcome")
        print("  [1] Login")
        print("  [0] Exit")
        choice = input("\n  Choice: ").strip()
        if choice == "0":
            print("\n  Goodbye!\n")
            break
        elif choice == "1":
            user = login()
            if user:
                portal_fn = PORTAL_MAP.get(user["designation"])
                if portal_fn:
                    portal_fn(user)
                else:
                    print("  Unknown role.")

if __name__ == "__main__":
    main()