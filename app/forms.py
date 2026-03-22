from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, FieldList, FloatField, FormField, Form, IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

ROLE_CHOICES = [('registrar', 'Registrar'), ('finance', 'Finance/Bursar'), ('lecturer', 'Lecturer'), ('principal', 'Principal'), ('student', 'Student')]
GRADE_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('P', 'Pass'), ('F', 'Fail')]
REMARK_CHOICES = [('Pass', 'Pass'), ('Fail', 'Fail'), ('Pending Review', 'Pending Review'), ('Supplementary', 'Supplementary')]
ATTENDANCE_STATUS = [('present', 'Present'), ('absent', 'Absent'), ('late', 'Late'), ('excused', 'Excused')]
DAY_CHOICES = [('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday')]
STATUS_FILTER_CHOICES = [('', 'All Statuses'), ('active', 'Active'), ('inactive', 'Inactive')]

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class LecturerFilterForm(FlaskForm):
    q = StringField('Search Lecturer', validators=[Optional(), Length(max=120)])
    department_name = StringField('Department', validators=[Optional(), Length(max=120)])
    status = SelectField('Status', choices=STATUS_FILTER_CHOICES, validators=[Optional()])
    submit = SubmitField('Filter')

class DepartmentForm(FlaskForm):
    name = StringField('Department Name', validators=[DataRequired(), Length(max=120)])
    code = StringField('Department Code', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Department')

class ProgramForm(FlaskForm):
    name = StringField('Course / Program Name', validators=[DataRequired(), Length(max=150)])
    code = StringField('Program Code', validators=[DataRequired(), Length(max=20)])
    level = SelectField('Level', choices=[('Certificate', 'Certificate'), ('Diploma', 'Diploma'), ('Short Course', 'Short Course')], validators=[DataRequired()])
    duration_years = IntegerField('Duration (Years)', validators=[DataRequired()])
    department_id = SelectField('Department', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Program')

class UnitForm(FlaskForm):
    name = StringField('Unit Name', validators=[DataRequired(), Length(max=150)])
    code = StringField('Unit Code', validators=[DataRequired(), Length(max=20)])
    credit_hours = IntegerField('Credit Hours', validators=[DataRequired()])
    program_id = SelectField('Program', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Unit')

class LecturerAssignmentForm(FlaskForm):
    lecturer_user_id = SelectField('Lecturer', coerce=int, validators=[DataRequired()])
    unit_id = SelectField('Unit', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Lecturer')

class LecturerStudentAssignmentForm(FlaskForm):
    lecturer_user_id = SelectField('Lecturer', coerce=int, validators=[DataRequired()])
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Student')

class TimetableEntryForm(FlaskForm):
    unit_id = SelectField('Unit', coerce=int, validators=[DataRequired()])
    lecturer_user_id = SelectField('Lecturer', coerce=int, validators=[Optional()])
    day_of_week = SelectField('Day of Week', choices=DAY_CHOICES, validators=[DataRequired()])
    start_time = StringField('Start Time', validators=[DataRequired(), Length(max=10)])
    end_time = StringField('End Time', validators=[DataRequired(), Length(max=10)])
    room = StringField('Room', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Save Timetable Entry')

class AssessmentSchemeForm(FlaskForm):
    name = StringField('Scheme Name', validators=[DataRequired(), Length(max=120)])
    module_count = IntegerField('Number of Modules', validators=[DataRequired()])
    raw_total = FloatField('Raw Total', validators=[DataRequired()])
    converted_total = FloatField('Converted Total', validators=[DataRequired()])
    submit = SubmitField('Save Scheme')

class AssessmentComponentForm(FlaskForm):
    name = StringField('Component Name', validators=[DataRequired(), Length(max=100)])
    max_marks = FloatField('Maximum Marks', validators=[DataRequired()])
    position = IntegerField('Display Order', validators=[DataRequired()])
    submit = SubmitField('Save Component')

class ProgramSchemeAssignForm(FlaskForm):
    program_id = SelectField('Program', coerce=int, validators=[DataRequired()])
    scheme_id = SelectField('Assessment Scheme', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Scheme')

class ApplicationForm(FlaskForm):
    application_number = StringField('Application Number', validators=[DataRequired(), Length(max=50)])
    applicant_name = StringField('Applicant Name', validators=[DataRequired(), Length(max=150)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    status = SelectField('Status', choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], validators=[DataRequired()])
    program_id = SelectField('Program', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Application')

class StudentForm(FlaskForm):
    admission_number = StringField('Admission Number', validators=[DataRequired(), Length(max=50)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=80)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=80)])
    gender = SelectField('Gender', choices=[('', 'Select'), ('Male', 'Male'), ('Female', 'Female')], validators=[Optional()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()], format='%Y-%m-%d')
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email()])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    guardian_name = StringField('Guardian Name', validators=[Optional(), Length(max=120)])
    guardian_phone = StringField('Guardian Phone', validators=[Optional(), Length(max=20)])
    status = SelectField('Status', choices=[('active', 'Active'), ('deferred', 'Deferred'), ('graduated', 'Graduated'), ('suspended', 'Suspended')], validators=[DataRequired()])
    program_id = SelectField('Program', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Student')

class AttendanceForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    unit_id = SelectField('Unit', coerce=int, validators=[DataRequired()])
    attendance_date = DateField('Attendance Date', validators=[DataRequired()], format='%Y-%m-%d')
    status = SelectField('Status', choices=ATTENDANCE_STATUS, validators=[DataRequired()])
    notes = StringField('Notes', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save Attendance')

class BulkAttendanceRowForm(FlaskForm):
    student_id = IntegerField('Student ID', validators=[Optional()])
    student_name = StringField('Student Name', validators=[Optional()])
    status = SelectField('Status', choices=ATTENDANCE_STATUS, validators=[DataRequired()])

class BulkAttendanceForm(FlaskForm):
    unit_id = SelectField('Unit', coerce=int, validators=[DataRequired()])
    attendance_date = DateField('Attendance Date', validators=[DataRequired()], format='%Y-%m-%d')
    rows = FieldList(FormField(BulkAttendanceRowForm), min_entries=0)
    submit = SubmitField('Save Bulk Attendance')

class AttendanceApprovalForm(FlaskForm):
    submit = SubmitField('Approve Attendance')

class InvoiceForm(FlaskForm):
    invoice_number = StringField('Invoice Number', validators=[DataRequired(), Length(max=50)])
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    balance = FloatField('Balance', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=255)])
    status = SelectField('Status', choices=[('unpaid', 'Unpaid'), ('partial', 'Partial'), ('paid', 'Paid')], validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Save Invoice')

class PaymentForm(FlaskForm):
    receipt_number = StringField('Receipt Number', validators=[DataRequired(), Length(max=50)])
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    method = SelectField('Method', choices=[('cash', 'Cash'), ('mpesa', 'M-Pesa'), ('bank', 'Bank')], validators=[DataRequired()])
    reference = StringField('Reference', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Record Payment')

class ResultForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    unit_id = SelectField('Unit', coerce=int, validators=[DataRequired()])
    semester_id = SelectField('Semester', coerce=int, validators=[DataRequired()])
    marks = FloatField('Marks', validators=[DataRequired()])
    grade = SelectField('Grade', choices=GRADE_CHOICES, validators=[DataRequired()])
    remarks = SelectField('Remarks', choices=REMARK_CHOICES, validators=[DataRequired()])
    submit = SubmitField('Save Result')

class ModuleScoreEntryForm(Form):
    cat = FloatField('CAT', validators=[Optional(), NumberRange(min=0, max=30)])
    group_work = FloatField('Group Work', validators=[Optional(), NumberRange(min=0, max=20)])
    final_exam = FloatField('Final Exam', validators=[Optional(), NumberRange(min=0, max=60)])

class ModuleBasedResultForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    unit_id = SelectField('Unit', coerce=int, validators=[DataRequired()])
    semester_id = SelectField('Semester', coerce=int, validators=[DataRequired()])
    module_1 = FormField(ModuleScoreEntryForm)
    module_2 = FormField(ModuleScoreEntryForm)
    module_3 = FormField(ModuleScoreEntryForm)
    submit = SubmitField('Save Module Results')

class RegisterAdminForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Super Admin')

class UserForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=ROLE_CHOICES, validators=[DataRequired()])
    password = PasswordField('Temporary Password', validators=[DataRequired(), Length(min=6)])
    is_active_user = BooleanField('Active account', default=True)
    submit = SubmitField('Create User')

class UserEditForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=ROLE_CHOICES, validators=[DataRequired()])
    is_active_user = BooleanField('Active account', default=True)
    submit = SubmitField('Save Changes')

class LecturerProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    staff_id = StringField('Staff ID', validators=[Optional(), Length(max=50)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    department_name = StringField('Department', validators=[Optional(), Length(max=120)])
    specialization = StringField('Specialization', validators=[Optional(), Length(max=120)])
    submit = SubmitField('Update Lecturer Profile')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class StudentSignupForm(FlaskForm):
    admission_number = StringField('Admission Number', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Student Account')

class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class ApproveApplicationForm(FlaskForm):
    admission_number = StringField('Admission Number', validators=[DataRequired(), Length(max=50)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=80)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=80)])
    send_portal_ready_note = BooleanField('Mark as ready for student portal', default=True)
    submit = SubmitField('Approve and Create Student')
