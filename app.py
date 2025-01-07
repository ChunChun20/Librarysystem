from datetime import date
from flask import Flask, render_template, redirect, url_for, flash,request
from sqlalchemy import desc, func
from forms import AddBookForm, AddAuthorForm, AddMemberForm, AddPublisherForm, UpdateAuthorForm, UpdateMemberForm, \
    UpdatePublisherForm, UpdateBookForm, LoanForm
from models import db,Author, Publisher, Book, Member, Loan


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Peanuts12345@localhost/library_db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SECRET_KEY'] = 'SUPER SECRET KEY'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route("/")
def home():

    return render_template("home.html")


@app.route("/menu")
def menu():

    return render_template("menu.html")


def get_filtered_books(search_query,filter_option):
    """Function that is used for both the search bar and the filter dropdown button
        for the books.html and is also responsible for finding the count of loans
        for each book.
    """

    query = db.session.query(Book,func.count(Loan.id)
                             .label('loan_count')).join(Author).join(Publisher)\
        .outerjoin(Loan,Loan.book_id == Book.id).group_by(Book.id)

    if search_query:
        query = query.filter(
            (Book.title.ilike(f"%{search_query}%")) |
            (Book.genre.ilike(f"%{search_query}%")) |
            (Author.name.ilike(f"%{search_query}%")) |
            (Publisher.name.ilike(f"%{search_query}%")) |
            (Book.publication_year.ilike(f"%{search_query}%"))
        )

    filter_options = {
        'filter_by_title': Book.title,
        "filter_by_title_desc": desc(Book.title),
        "filter_by_year": Book.publication_year,
        "filter_by_year_desc": desc(Book.publication_year),
        "filter_by_popularity": desc("loan_count"),
        "filter_by_popularity_desc": "loan_count"
    }


    if filter_option in filter_options:
        query = query.order_by(filter_options[filter_option])

    return query.all()


@app.route("/books",methods=['GET'])
def books():
    search_query = request.args.get('search_query','').strip()
    filter_option = request.args.get('filter', 'all')

    books = get_filtered_books(search_query,filter_option)

    return render_template("books.html",books=books)


@app.route("/add_books",methods=["GET","POST"])
def add_books():
    form = AddBookForm()

    if request.method == "GET":
        form.author.choices = [author.name for author in Author.query.all()]
        form.publisher.choices = [publisher.name for publisher in Publisher.query.all()]

    if form.validate_on_submit():
        try:
            author = Author.query.filter_by(name=form.author.data).first()

            if not author:
                flash(f"Author {form.author.data} not found", "warning")
                return render_template("add_books.html",form=form)

            publisher = Publisher.query.filter_by(name=form.publisher.data).first()

            if not publisher:
                flash(f"Publisher {form.publisher.data} not found", "warning")
                return render_template("add_books.html",form=form)

            new_book = Book(
                title=form.title.data,
                isbn=form.isbn.data,
                publication_year=form.publication_year.data,
                genre=form.genre.data,
                author_id=author.id,
                publisher_id=publisher.id
            )
            db.session.add(new_book)
            db.session.commit()

            flash(f"Successfully added {new_book.title}",'success')

            return redirect(url_for("books"))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "warning")
            db.session.rollback()
            return render_template("add_books.html", form=form)
    elif form.errors:
        for field,errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}","danger")

    return render_template("add_books.html",form=form)


def delete_loans(book_id):
    """This function deletes all information about loans of the deleted book."""
    try:
        loans_to_delete = Loan.query.filter_by(book_id=book_id).all()
        for loan in loans_to_delete:
            db.session.delete(loan)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error while deleting loans: {e}","warning")
        return False
    return True


@app.route("/delete_book/<int:book_id>",methods=["POST"])
def delete_book(book_id):
    book_to_delete = Book.query.get(book_id)

    if book_to_delete:
        is_book_loaned = Loan.query.filter_by(book_id=book_id,returned=False).first()
        if is_book_loaned:
            flash("Cannot delete a book that is currently loaned out.", "danger")
            return redirect(url_for('books'))

        if not delete_loans(book_id):
            return redirect(url_for("books"))

        db.session.delete(book_to_delete)
        db.session.commit()
        flash(f"Book deleted successfully!",'success')
    else:
        flash("Book not found.","danger")

    return redirect(url_for("books"))


@app.route("/update_book/<int:book_id>",methods=["GET","POST"])
def update_book(book_id):
    book_to_update = Book.query.get_or_404(book_id)
    form = UpdateBookForm(obj=book_to_update)

    form.author.choices = [author.name for author in Author.query.all()]
    form.publisher.choices = [publisher.name for publisher in Publisher.query.all()]

    if not form.is_submitted():
        if book_to_update.author:
            form.author.data = book_to_update.author.name
        if book_to_update.publisher:
            form.publisher.data = book_to_update.publisher.name

    if form.validate_on_submit():

        author = Author.query.filter_by(name=form.author.data).first()

        if not author:
            flash(f"Author {form.author.data} not found", "warning")
            return render_template("update_book.html", form=form)

        publisher = Publisher.query.filter_by(name=form.publisher.data).first()

        if not publisher:
            flash(f"Publisher {form.publisher.data} not found", "warning")
            return render_template("update_book.html", form=form)

        isbns = [book.isbn for book in Book.query.all()]

        if form.isbn.data in isbns and book_to_update.isbn != form.isbn.data:
            flash(f"Isbn must be unique!","warning")
            return render_template("update_book.html", form=form)

        book_to_update.title = form.title.data
        book_to_update.isbn = form.isbn.data
        book_to_update.publication_year = form.publication_year.data
        book_to_update.genre = form.genre.data
        book_to_update.author_id = author.id
        book_to_update.publisher_id = publisher.id

        db.session.commit()
        flash(f"Book updated successfully!","success")
        return redirect(url_for("books"))
    elif form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", "danger")

    return render_template("update_book.html", form=form,book=book_to_update)


@app.route("/loan_book/<int:book_id>",methods=["GET","POST"])
def loan_book(book_id):
    form = LoanForm()
    book_to_loan = Book.query.get_or_404(book_id)

    is_book_loaned = Loan.query.filter_by(book_id=book_id,returned=False).first()

    if is_book_loaned:
        flash(f"Book is not available!","danger")
        return redirect(url_for('books'))

    form.member.choices = [member.name for member in Member.query.all()]

    if form.validate_on_submit():

        member = Member.query.filter_by(name=form.member.data).first()

        new_loan = Loan(
            book=book_to_loan,
            member=member,
            loan_date=form.loan_date.data,
            return_date=form.return_date.data,
            returned=False)
        db.session.add(new_loan)
        db.session.commit()

        flash(f"Successfully created new loan","success")

        return redirect(url_for("loans"))

    elif form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", "danger")

    return render_template("loan_book.html", form=form,book=book_to_loan)


@app.route("/return_book/<int:loan_id>",methods=["POST"])
def return_book(loan_id):
    loan = Loan.query.get(loan_id)

    if not loan:
        flash("Loan doesn't exist","danger")
        return redirect(url_for("loans"))

    member_id = loan.member_id

    try:
        loan.returned = True
        loan.return_date = date.today()
        db.session.add(loan)
        db.session.commit()
        flash(f"Successfully returned book {loan.book.title}.","success")
    except Exception as e:
        flash(f"Error: {e}")
    return redirect(url_for('loaned_books', member_id=member_id))



def get_filtered_members(search_query):
    if search_query:
        members = Member.query.filter(
            (Member.name.ilike(f"%{search_query}%")) |
            (Member.address.ilike(f"%{search_query}%")) |
            (Member.contact_info.ilike(f"%{search_query}%"))
        ).all()
    else:
        members = Member.query.all()

    return members


@app.route("/members",methods=["GET"])
def members():
    search_query = request.args.get('search_query', '').strip()

    members = get_filtered_members(search_query)

    return render_template("members.html",members=members)


@app.route("/add_members",methods=["GET","POST"])
def add_members():
        form = AddMemberForm()

        if form.validate_on_submit():
            try:
                new_member = Member(
                    name=form.name.data,
                    address=form.address.data,
                    contact_info=form.contact_info.data
                )
                db.session.add(new_member)
                db.session.commit()

                flash(f"Successfully added {new_member.name}","success")

                return redirect(url_for("members"))
            except Exception as e:
                flash(f"An error occurred: {str(e)}", "error")
                db.session.rollback()
                return render_template("add_member.html", form=form)

        elif form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field.capitalize()}: {error}", "danger")

        return render_template("add_member.html", form=form)


def delete_member_loans(member_id):
    """This function deletes all information about loans of the deleted member."""
    try:
        loans_to_delete = Loan.query.filter_by(member_id=member_id).all()
        for loan in loans_to_delete:
            db.session.delete(loan)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error while deleting loans: {e}","warning")
        return False
    return True


@app.route("/delete_member/<int:member_id>",methods=["POST"])
def delete_member(member_id):
    member_to_delete = Member.query.get(member_id)

    if member_to_delete:

        if not delete_member_loans(member_id):
            return redirect(url_for("members"))


        db.session.delete(member_to_delete)
        db.session.commit()
        flash(f"Member deleted successfully!",'success')
    else:
        flash("Member not found.","danger")

    return redirect(url_for("members"))


@app.route("/update_member/<int:member_id>",methods=["GET","POST"])
def update_member(member_id):
    member_to_update = Member.query.get_or_404(member_id)
    form = UpdateMemberForm(obj=member_to_update)

    if form.validate_on_submit():
        member_to_update.name = form.name.data
        member_to_update.address = form.address.data
        member_to_update.contact_info = form.contact_info.data

        db.session.commit()
        flash(f"Member updated successfully!","success")
        return redirect(url_for("members"))
    elif form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", "danger")

    return render_template("update_member.html", form=form,member=member_to_update)


def get_filtered_publishers(search_query):
    if search_query:
        publishers = Publisher.query.filter(
            (Publisher.name.ilike(f"%{search_query}%")) |
            (Publisher.address.ilike(f"%{search_query}%"))
        ).all()
    else:
        publishers = Publisher.query.all()

    return publishers


@app.route("/publishers",methods=["GET"])
def publishers():
    search_query = request.args.get('search_query', '').strip()

    publishers = get_filtered_publishers(search_query)

    return render_template("publishers.html",publishers=publishers)


@app.route("/add_publisher",methods=["GET","POST"])
def add_publisher():
    form = AddPublisherForm()

    if form.validate_on_submit():
        try:
            new_publisher = Publisher(
                name=form.name.data,
                address=form.address.data,
            )
            db.session.add(new_publisher)
            db.session.commit()

            flash(f"Successfully added {new_publisher.name}","success")

            return redirect(url_for("publishers"))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            db.session.rollback()
            return render_template("add_publisher.html", form=form)
    elif form.errors:
        for field,errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}","danger")

    return render_template("add_publisher.html",form=form)


@app.route("/update_publisher/<int:publisher_id>",methods=["GET","POST"])
def update_publisher(publisher_id):
    publisher_to_update = Publisher.query.get_or_404(publisher_id)
    form = UpdatePublisherForm(obj=publisher_to_update)
    if form.validate_on_submit():
        publisher_to_update.name = form.name.data
        publisher_to_update.address = form.address.data

        db.session.commit()
        flash(f"Publisher updated successfully!","success")
        return redirect(url_for("publishers"))
    elif form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", "danger")

    return render_template("update_publisher.html", form=form,publisher=publisher_to_update)


@app.route("/delete_publisher/<int:publisher_id>",methods=["POST"])
def delete_publisher(publisher_id):
    publisher_to_delete = Publisher.query.get(publisher_id)

    if publisher_to_delete:
        has_books = Book.query.filter_by(publisher_id=publisher_id).first()
        if has_books:
            flash("Cannot delete a publisher that has associated books.", "danger")
            return redirect(url_for("publishers"))
        db.session.delete(publisher_to_delete)
        db.session.commit()
        flash(f"Publisher deleted successfully!",'success')
    else:
        flash("Publisher not found.","danger")

    return redirect(url_for("publishers"))


def get_filtered_authors(search_query):
    if search_query:
        authors = Author.query.filter(
            (Author.name.ilike(f"%{search_query}%")) |
            (Author.birth_date.ilike(f"%{search_query}%")) |
            (Author.biography.ilike(f"%{search_query}%"))
        ).all()
    else:
        authors = Author.query.all()

    return authors


@app.route("/authors",methods=["GET"])
def authors():
    search_query = request.args.get('search_query', '').strip()

    authors = get_filtered_authors(search_query)

    return render_template("authors.html",authors=authors)


@app.route("/add_author",methods=["GET","POST"])
def add_author():
    form = AddAuthorForm()

    if form.validate_on_submit():
        try:
            new_author = Author(
                name=form.name.data,
                birth_date=form.birth_date.data,
                biography=form.biography.data
            )
            db.session.add(new_author)
            db.session.commit()

            flash(f"Successfully added {new_author.name}","success")

            return redirect(url_for("authors"))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            db.session.rollback()
            return render_template("add_author.html", form=form)
    elif form.errors:
        for field,errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}","danger")

    return render_template("add_author.html",form=form)


@app.route("/delete_author/<int:author_id>",methods=["POST"])
def delete_author(author_id):
    author_to_delete = Author.query.get(author_id)

    if author_to_delete:
        has_books = Book.query.filter_by(author_id=author_id).first()
        if has_books:
            flash("Cannot delete an author that has associated books.","danger")
            return redirect(url_for("authors"))
        db.session.delete(author_to_delete)
        db.session.commit()
        flash(f"Author deleted successfully!",'success')
    else:
        flash("Author not found.","danger")

    return redirect(url_for("authors"))


@app.route("/update_author/<int:author_id>",methods=["GET","POST"])
def update_author(author_id):
    author_to_update = Author.query.get_or_404(author_id)
    form = UpdateAuthorForm(obj=author_to_update)

    if form.validate_on_submit():
        author_to_update.name = form.name.data
        author_to_update.birth_date = form.birth_date.data
        author_to_update.biography = form.biography.data

        db.session.commit()
        flash(f"Author updated successfully!","success")
        return redirect(url_for("authors"))
    elif form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", "danger")

    return render_template("update_author.html", form=form,author=author_to_update)

def overdue_loans(loans):
    """Checks if the current date is greater than the book loan return date
        and if that is true and the book hasn't been returned it adds the book id to
        a dictionary.
    """

    today = date.today()
    loan_statuses = {}

    for loan in loans:
        if loan.return_date and today > loan.return_date and not loan.returned:
            loan_statuses[loan.id] = "overdue"
        else:
            loan_statuses[loan.id] = "ok"

    return loan_statuses

@app.route("/loans")
def loans():
    filter_option = request.args.get('filter','all')
    loans_query = Loan.query

    if filter_option:
        if filter_option == 'returned':
            loans_query = Loan.query.filter_by(returned=True)
        elif filter_option == "not_returned":
            loans_query = Loan.query.filter_by(returned=False)

    loans = loans_query.all()
    loan_statuses = overdue_loans(loans)

    return render_template("loans.html",loans=loans,loan_statuses=loan_statuses)

@app.route("/loaned_books/<int:member_id>",methods=["GET","POST"])
def loaned_books(member_id):
    loans = Loan.query.filter_by(member_id=member_id).all()

    loan_statuses = overdue_loans(loans)

    return render_template("user_loans.html", loans=loans,loan_statuses=loan_statuses)

def seed_database():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Authors
        author1 = Author(name="Jane Austen", birth_date=date(1775, 12, 16),
                         biography="English novelist known for her social commentary and romantic fiction.")
        author2 = Author(name="Agatha Christie", birth_date=date(1890, 9, 15),
                         biography="British crime novelist, short story writer, and playwright, known as the 'Queen of Crime'.")
        author3 = Author(name="Ernest Hemingway", birth_date=date(1899, 7, 21),
                         biography="American novelist, short story writer, journalist, and sportsman known for his influence on 20th-century fiction.")
        author4 = Author(name="Gabriel Garcia Marquez", birth_date=date(1927, 3, 6),
                         biography="Colombian novelist, short story writer, screenwriter and journalist, Nobel Prize laureate.")
        author5 = Author(name="Harper Lee", birth_date=date(1926, 4, 28),
                         biography="American novelist best known for her Pulitzer Prize-winning novel To Kill a Mockingbird")
        author6 = Author(name="George Orwell", birth_date=date(1926, 4, 28),
                         biography="English novelist and essayist known for his dystopian works.")
        author7 = Author(name="J.R.R. Tolkien",birth_date=date(1926, 4, 28),
                         biography="English writer, poet, philologist, and academic, author of The Lord of the Rings.")
        author8 = Author(name="Virginia Woolf",birth_date=date(1926, 4, 28),
                         biography="English writer, considered one of the most important modernist 20th-century authors")
        author9 = Author(name="Stephen King",birth_date=date(1926, 4, 28),
                         biography="American author of horror, supernatural fiction, suspense, and fantasy novels.")
        author10 = Author(name="Toni Morrison",birth_date=date(1926, 4, 28),
                          biography="American novelist, essayist, book editor, and professor, Nobel Prize laureate.")

        # Publishers
        publisher1 = Publisher(name="Penguin Classics", address="80 Strand, London, England")
        publisher2 = Publisher(name="HarperCollins", address="195 Broadway, New York, USA")
        publisher3 = Publisher(name="Simon & Schuster", address="1230 Avenue of the Americas, New York, USA")
        publisher4 = Publisher(name="Planeta", address="Av. Diagonal, 662-664, Barcelona, Spain")
        publisher5 = Publisher(name="Vintage Books", address="1745 Broadway, New York, USA")
        publisher6 = Publisher(name="Scribner", address="1230 Avenue of the Americas, New York, USA")

        # Books
        book1 = Book(title="Pride and Prejudice", isbn="9780141439518", publication_year="1813", genre="Romance",
                     author=author1, publisher=publisher1)
        book2 = Book(title="Murder on the Orient Express", isbn="9780007119318", publication_year="1934",
                     genre="Mystery", author=author2, publisher=publisher2)
        book3 = Book(title="The Old Man and the Sea", isbn="9780684801223", publication_year="1952", genre="Novel",
                     author=author3, publisher=publisher3)
        book4 = Book(title="One Hundred Years of Solitude", isbn="9780061120039", publication_year="1967",
                     genre="Magical Realism", author=author4, publisher=publisher4)
        book5 = Book(title="And Then There Were None", isbn="9780007136834", publication_year="1939", genre="Mystery",
                     author=author2, publisher=publisher1)
        book6 = Book(title="To Kill a Mockingbird", isbn="9780446310789", publication_year="1960", genre="Classic",
                     author=author5, publisher=publisher2)
        book7 = Book(title="A Farewell to Arms", isbn="9780684801032", publication_year="1929", genre="Novel",
                     author=author3, publisher=publisher3)
        book8 = Book(title="Sense and Sensibility", isbn="9780141439662", publication_year="1811", genre="Romance",
                     author=author1, publisher=publisher1)
        book9 = Book(title="1984", isbn="9780451524935", publication_year="1949", genre="Dystopian", author=author6,
                     publisher=publisher5)
        book10 = Book(title="The Hobbit", isbn="9780618260264", publication_year="1937", genre="Fantasy",
                      author=author7, publisher=publisher6)
        book11 = Book(title="Mrs Dalloway", isbn="9780156631608", publication_year="1925", genre="Modernist",
                      author=author8, publisher=publisher1)
        book12 = Book(title="It", isbn="9781501142970", publication_year="1986", genre="Horror", author=author9,
                      publisher=publisher2)
        book13 = Book(title="Beloved", isbn="9781400033416", publication_year="1987", genre="Novel", author=author10,
                      publisher=publisher3)
        book14 = Book(title="The Fellowship of the Ring", isbn="9780618260267", publication_year="1954",
                      genre="Fantasy", author=author7, publisher=publisher6)
        book15 = Book(title="A Room of One's Own", isbn="9780156798428", publication_year="1929", genre="Essay",
                      author=author8, publisher=publisher5)
        book16 = Book(title="The Shining", isbn="9780307743657", publication_year="1977", genre="Horror",
                      author=author9, publisher=publisher2)
        book17 = Book(title="Song of Solomon", isbn="9781400033423", publication_year="1977", genre="Novel",
                      author=author10, publisher=publisher3)

        # Members
        member1 = Member(name="John Smith", address="123 Main St, Anytown", contact_info="john.smith@email.com")
        member2 = Member(name="Alice Brown", address="456 Oak Ave, Anotherville", contact_info="alice.brown@email.com")
        member3 = Member(name="Bob Johnson", address="789 Pine Ln, Someplace", contact_info="bob.johnson@email.com")
        member4 = Member(name="Emily Davis", address="101 Elm St, Different City", contact_info="emily.davis@email.com")
        member5 = Member(name="Charlie Green", address="222 Maple Dr, Another Town",
                         contact_info="charlie.green@email.com")
        member6 = Member(name="Diana White", address="333 Birch Rd, A Small Village",
                         contact_info="diana.white@email.com")
        member7 = Member(name="Frank Black", address="444 Willow Ct, A Big City", contact_info="frank.black@email.com")
        member8 = Member(name="Grace Grey", address="555 Cedar Ln, A Faraway Place",
                         contact_info="grace.grey@email.com")

        # Loans
        loan1 = Loan(book=book1, member=member1, loan_date=date(2023, 1, 15), return_date=date(2023, 2, 1),
                     returned=True)
        loan2 = Loan(book=book2, member=member2, loan_date=date(2023, 2, 10), return_date=date(2023, 2, 28),
                     returned=True)
        loan3 = Loan(book=book3, member=member1, loan_date=date(2023, 3, 1), returned=False)
        loan4 = Loan(book=book4, member=member3, loan_date=date(2023, 4, 1), return_date=date(2023, 4, 20),
                     returned=True)
        loan5 = Loan(book=book5, member=member4, loan_date=date(2023, 5, 1), returned=False)
        loan6 = Loan(book=book6, member=member1, loan_date=date(2023, 5, 1), returned=False)
        loan7 = Loan(book=book7, member=member2, loan_date=date(2023, 2, 15), return_date=date(2023, 2, 28),
                     returned=True)
        loan8 = Loan(book=book8, member=member4, loan_date=date(2023, 2, 15), return_date=date(2023, 3, 1),
                     returned=True)
        loan9 = Loan(book=book9, member=member5, loan_date=date(2023, 6, 10), return_date=date(2023, 6, 25),
                     returned=True)
        loan10 = Loan(book=book10, member=member6, loan_date=date(2023, 7, 5), return_date=date(2023, 7, 15),
                      returned=True)
        loan11 = Loan(book=book11, member=member7, loan_date=date(2023, 8, 1), return_date=date(2023, 8, 15),
                      returned=True)
        loan12 = Loan(book=book12, member=member8, loan_date=date(2023, 9, 2), returned=False)
        loan13 = Loan(book=book13, member=member1, loan_date=date(2023, 10, 10), return_date=date(2023, 10, 20),
                      returned=True)
        loan14 = Loan(book=book14, member=member2, loan_date=date(2023, 11, 15), return_date=date(2023, 12, 1),
                      returned=False)
        loan15 = Loan(book=book15, member=member3, loan_date=date(2023, 12, 1), returned=False)
        loan16 = Loan(book=book16, member=member4, loan_date=date(2024, 1, 1), returned=False)
        loan17 = Loan(book=book17, member=member5, loan_date=date(2024, 1, 15), return_date=date(2024, 2, 1),
                      returned=False)

        db.session.add_all([
            author1, author2, author3, author4, author5, author6, author7, author8, author9, author10,
            publisher1, publisher2, publisher3, publisher4, publisher5, publisher6,
            book1, book2, book3, book4, book5, book6, book7, book8, book9, book10, book11, book12, book13, book14,
            book15, book16, book17,
            member1, member2, member3, member4, member5, member6, member7, member8,
            loan1, loan2, loan3, loan4, loan5, loan6, loan7, loan8, loan9, loan10, loan11, loan12, loan13, loan14,
            loan15, loan16, loan17
        ])
        db.session.commit()


if __name__ == "__main__":
    seed_database()
    app.run(debug=True)