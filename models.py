from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Index

db = SQLAlchemy()

class Author(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(255),nullable=False,index=True)
    birth_date = db.Column(db.Date)
    biography = db.Column(db.Text)
    books = db.relationship('Book',backref='author',lazy=True)

    def __repr__(self):
        return f"<Author(name='{self.name}')>"
    
class Publisher(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(255),nullable=False,index=True)
    address = db.Column(db.Text)
    books = db.relationship('Book',backref='publisher',lazy=True)

    def __repr__(self):
        return f"<Publisher(name='{self.name}')>"

class Book(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(255),nullable=False,index=True)
    isbn = db.Column(db.String(20),unique=True)
    publication_year = db.Column(db.Integer,index=True)
    genre = db.Column(db.String(50),index=True)
    author_id = db.Column(db.Integer,db.ForeignKey('author.id'),nullable=False,index=True)
    publisher_id = db.Column(db.Integer,db.ForeignKey('publisher.id'),nullable=False,index=True)
    loans = db.relationship('Loan',backref='book',lazy=True)

    def __repr__(self):
        return f"<Book(title='{self.title}')>"

class Member(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(255),nullable=False,index=True)
    address = db.Column(db.String(255))
    contact_info = db.Column(db.String(255))
    loans = db.relationship('Loan',backref='member',lazy=True)

    def __repr__(self):
        return f"<Member(name='{self.name}')>"
    
class Loan(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    book_id = db.Column(db.Integer,db.ForeignKey('book.id'),nullable=False,index=True)
    member_id = db.Column(db.Integer,db.ForeignKey('member.id'),nullable=False,index=True)
    loan_date = db.Column(db.Date,nullable=False)
    return_date = db.Column(db.Date,nullable=True)
    returned = db.Column(db.Boolean,default=False,nullable=False)

    def __repr__(self):
        return f"<Loan(book_id='{self.book_id}',member_id='{self.member_id}',loan_date='{self.loan_date}')>"

class Librarian(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(255),nullable=False,unique=True)
    password = db.Column(db.String(80),nullable=False)
    name = db.Column(db.String(255),nullable=False)

    def __repr__(self):
        return f"<Librarian(name='{self.name}')>"