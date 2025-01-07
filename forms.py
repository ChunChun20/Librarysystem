import datetime


from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, DateField, BooleanField
from wtforms.validators import InputRequired,Length,ValidationError
from models import Book, Author, Member, Publisher, Loan


class AddBookForm(FlaskForm):
    title = StringField(validators=[InputRequired(),
                                    Length(min=4,max=255)],
                        render_kw={"placeholder":"Title"})
    isbn = StringField(validators=[InputRequired(),
                                    Length(min=4,max=20)],
                       render_kw={"placeholder": "ISBN"})

    publication_year = IntegerField(validators=[InputRequired()],
                       render_kw={"placeholder": "Publication Year"})

    genre = StringField(validators=[InputRequired(),
                                    Length(min=4,max=50)],
                       render_kw={"placeholder": "Genre"})

    author = SelectField('Author', validators=[InputRequired()], choices=[])

    publisher = SelectField('Publisher', validators=[InputRequired()], choices=[])

    submit = SubmitField("Add Book")

    def validate_isbn(self,isbn):
        existing_book = Book.query.filter_by(isbn=isbn.data).first()
        if existing_book:
            raise ValidationError("This ISBN is already in use. Please enter unique ISBN.")

class AddAuthorForm(FlaskForm):
    name = StringField(validators=[InputRequired(),
                                    Length(min=4, max=255)],
                        render_kw={"placeholder": "Name"})

    birth_date = DateField(validators=[InputRequired()],
                        render_kw={"placeholder": "Date"})

    biography = StringField(validators=[InputRequired(),
                                    Length(min=4, max=255)],
                        render_kw={"placeholder": "Biography"})

    submit = SubmitField("Add Author")

    def validate_name(self, name):
        existing_author = Author.query.filter_by(name=name.data).first()
        if existing_author:
            raise ValidationError("This author is already registered. Please enter unique author.")

class AddMemberForm(FlaskForm):
    name = StringField(validators=[InputRequired(),
                                    Length(min=4, max=255)],
                        render_kw={"placeholder": "Name"})

    address = StringField(validators=[InputRequired(),
                                      Length(min=4, max=255)],
                        render_kw={"placeholder": "Address"})

    contact_info = StringField(validators=[InputRequired(),
                                    Length(min=4, max=255)],
                        render_kw={"placeholder": "Contact Info"})

    submit = SubmitField("Add Member")

    def validate_name(self, name):
        existing_member = Member.query.filter_by(name=name.data).first()
        if existing_member:

            raise ValidationError("This member is already registered. Please enter unique member.")





class AddPublisherForm(FlaskForm):
    name = StringField(validators=[InputRequired(),
                                   Length(min=4, max=255)],
                       render_kw={"placeholder": "Name"})

    address = StringField(validators=[InputRequired(),
                                      Length(min=4, max=255)],
                          render_kw={"placeholder": "Address"})


    def validate_name(self, name):
        existing_publisher = Publisher.query.filter_by(name=name.data).first()
        if existing_publisher:
            raise ValidationError("This member is already registered. Please enter unique member.")

    submit = SubmitField("Add Publisher")

class UpdateAuthorForm(FlaskForm):
    name = StringField("Name",validators=[InputRequired(),
                                    Length(min=4, max=255)])

    birth_date = DateField("Birth Date",validators=[InputRequired()])

    biography = StringField("Biography",validators=[InputRequired(),
                                    Length(min=4, max=255)])

    submit = SubmitField("Update Author")

class UpdateMemberForm(FlaskForm):
    name = StringField("Name",validators=[InputRequired(),
                                    Length(min=4, max=255)])

    address = StringField("Address",validators=[InputRequired(),
                                      Length(min=4, max=255)])

    contact_info = StringField("Contact info",validators=[InputRequired(),
                                    Length(min=4, max=255)])

    submit = SubmitField("Update Member")

class UpdatePublisherForm(FlaskForm):
    name = StringField("Name",validators=[InputRequired(),
                                   Length(min=4, max=255)])

    address = StringField("Address",validators=[InputRequired(),
                                      Length(min=4, max=255)])

class UpdateBookForm(FlaskForm):
    title = StringField("Title",validators=[InputRequired(),
                                    Length(min=4,max=255)])
    isbn = StringField("ISBN",validators=[InputRequired(),
                                    Length(min=4,max=20)])

    publication_year = IntegerField("Publication Year",validators=[InputRequired()])

    genre = StringField("Genre",validators=[InputRequired(),
                                    Length(min=4,max=50)])

    author = SelectField('Author', validators=[InputRequired()], choices=[])

    publisher = SelectField('Publisher', validators=[InputRequired()], choices=[])

    submit = SubmitField("Add Book")

    # def validate_isbn(self, isbn):
    #     existing_book = Book.query.filter_by(isbn=isbn.data).first()
    #     if existing_book:
    #         raise ValidationError("This ISBN is already in use. Please enter unique ISBN.")


class LoanForm(FlaskForm):

    member = SelectField('Member', validators=[InputRequired()], choices=[])
    loan_date = DateField("Loan Date",validators=[InputRequired()])
    return_date = DateField("Return Date",validators=[InputRequired()])

    submit = SubmitField("Loan Book")

    def validate_loan_date(self,loan_date):
        if loan_date.data > datetime.date.today():
            raise ValidationError("Loan date cannot be in the future.")

    def validate_return_date(self,return_date):
        if self.loan_date.data and return_date.data <= self.loan_date.data:
            raise ValidationError("Return date must be after the loan date.")





