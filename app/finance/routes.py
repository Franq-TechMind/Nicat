from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import InvoiceForm, PaymentForm
from app.models import FeeInvoice, Payment, Student
from app.utils import permission_required

finance_bp = Blueprint('finance', __name__)


def populate_students(form):
    form.student_id.choices = [(s.id, f'{s.full_name} - {s.admission_number}') for s in Student.query.order_by(Student.first_name).all()]


def recalculate_student_invoices(student_id):
    student = Student.query.get(student_id)
    if not student:
        return
    total_paid = sum(payment.amount for payment in student.payments)
    invoices = FeeInvoice.query.filter_by(student_id=student_id).order_by(FeeInvoice.created_at.asc(), FeeInvoice.id.asc()).all()
    remaining_payment = total_paid
    for invoice in invoices:
        applied = min(invoice.amount, remaining_payment)
        invoice.balance = max(invoice.amount - applied, 0)
        remaining_payment = max(remaining_payment - invoice.amount, 0)
        if invoice.balance <= 0:
            invoice.status = 'paid'
        elif invoice.balance < invoice.amount:
            invoice.status = 'partial'
        else:
            invoice.status = 'unpaid'
    db.session.commit()


@finance_bp.route('/finance')
@login_required
@permission_required('finance.view')
def index():
    q = request.args.get('q', '').strip()
    invoices_query = FeeInvoice.query
    if q:
        invoices_query = invoices_query.filter(FeeInvoice.invoice_number.ilike(f'%{q}%') | FeeInvoice.description.ilike(f'%{q}%'))
    invoices = invoices_query.order_by(FeeInvoice.id.desc()).all()
    payments = Payment.query.order_by(Payment.id.desc()).all()
    total_invoiced = sum(invoice.amount for invoice in invoices)
    total_paid = sum(payment.amount for payment in payments)
    total_balance = sum(invoice.balance for invoice in invoices)
    return render_template('finance/index.html', invoices=invoices, payments=payments, q=q, total_invoiced=total_invoiced, total_paid=total_paid, total_balance=total_balance)


@finance_bp.route('/finance/invoices/new', methods=['GET', 'POST'])
@login_required
@permission_required('finance.create')
def create_invoice():
    form = InvoiceForm()
    populate_students(form)
    if form.validate_on_submit():
        invoice = FeeInvoice()
        form.populate_obj(invoice)
        invoice.balance = invoice.amount
        db.session.add(invoice)
        db.session.commit()
        recalculate_student_invoices(invoice.student_id)
        flash('Invoice created successfully.', 'success')
        return redirect(url_for('finance.index'))
    return render_template('finance/invoice_form.html', form=form, title='New Invoice')


@finance_bp.route('/finance/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('finance.edit')
def edit_invoice(invoice_id):
    invoice = FeeInvoice.query.get_or_404(invoice_id)
    form = InvoiceForm(obj=invoice)
    populate_students(form)
    if form.validate_on_submit():
        old_student_id = invoice.student_id
        form.populate_obj(invoice)
        invoice.balance = invoice.amount
        db.session.commit()
        recalculate_student_invoices(old_student_id)
        if invoice.student_id != old_student_id:
            recalculate_student_invoices(invoice.student_id)
        flash('Invoice updated successfully.', 'success')
        return redirect(url_for('finance.index'))
    return render_template('finance/invoice_form.html', form=form, title='Edit Invoice')


@finance_bp.route('/finance/invoices/<int:invoice_id>/delete', methods=['POST'])
@login_required
@permission_required('finance.delete')
def delete_invoice(invoice_id):
    invoice = FeeInvoice.query.get_or_404(invoice_id)
    student_id = invoice.student_id
    db.session.delete(invoice)
    db.session.commit()
    recalculate_student_invoices(student_id)
    flash('Invoice deleted.', 'info')
    return redirect(url_for('finance.index'))


@finance_bp.route('/finance/payments/new', methods=['GET', 'POST'])
@login_required
@permission_required('finance.create')
def create_payment():
    form = PaymentForm()
    populate_students(form)
    if form.validate_on_submit():
        payment = Payment()
        form.populate_obj(payment)
        db.session.add(payment)
        db.session.commit()
        recalculate_student_invoices(payment.student_id)
        flash('Payment recorded successfully.', 'success')
        return redirect(url_for('finance.index'))
    return render_template('finance/payment_form.html', form=form, title='Record Payment')


@finance_bp.route('/finance/payments/<int:payment_id>/delete', methods=['POST'])
@login_required
@permission_required('finance.delete')
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    student_id = payment.student_id
    db.session.delete(payment)
    db.session.commit()
    recalculate_student_invoices(student_id)
    flash('Payment deleted.', 'info')
    return redirect(url_for('finance.index'))


@finance_bp.route('/finance/students/<int:student_id>/statement')
@login_required
@permission_required('finance.view')
def statement(student_id):
    student = Student.query.get_or_404(student_id)
    invoices = FeeInvoice.query.filter_by(student_id=student.id).order_by(FeeInvoice.created_at.asc()).all()
    payments = Payment.query.filter_by(student_id=student.id).order_by(Payment.paid_at.asc()).all()
    return render_template('finance/statement.html', student=student, invoices=invoices, payments=payments)


@finance_bp.route('/finance/payments/<int:payment_id>/receipt')
@login_required
@permission_required('finance.view')
def receipt(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    return render_template('finance/receipt.html', payment=payment, student=payment.student, current_user=current_user)
