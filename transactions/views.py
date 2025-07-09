from django.shortcuts import render,redirect,get_object_or_404
from django.views.generic import CreateView,ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Transaction
from .forms import DepositForm,LoanRequestForm,WithdrawForm,TransferMoneyForm
from .constants import DEPOSIT,WITHDRAWAL,LOAN,LOAN_PAID,TRANSFER_SENT,TRANSFER_RECEIVED
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Sum
from django.views import View
from django.urls import reverse_lazy
from accounts.models import UserBankAccount

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
# Create your views here.


def send_transaction_email(user, amount, subject, template):
    message = render_to_string(template, {
        'user': user,
        'amount': amount,

    })
    send_email = EmailMultiAlternatives(subject,'',to=[user.email])

    send_email.attach_alternative(message, "text/html")
    send_email.send()


def send_moneytransfer_email(user,recipient,recipient_account_number, amount, subject, template1,template2):
    message1 = render_to_string(template1, {
        'user': user,
        'recipient': recipient,
        'amount': amount,
        'recipient_account_number': recipient_account_number,
    })
    message2 = render_to_string(template2, {
        'user': recipient,
        'sender': user,
        'amount': amount,
        'sender_account_number': user.account.account_no,
    })
    send_email = EmailMultiAlternatives(subject,'',to=[user.email])

    send_email.attach_alternative(message1, "text/html")
    send_email.send()

    send_email2 = EmailMultiAlternatives(subject,'',to=[recipient.email])
    send_email2.attach_alternative(message2, "text/html")
    send_email2.send()



class TransactionCreateMixin(LoginRequiredMixin,CreateView):
    template_name= 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account':self.request.user.account,
            })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context.update({
            'title':self.title
        })

        return context
    
class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = "Deposit"


    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial
    
    def form_valid(self, form):
        amount  = form.cleaned_data.get('amount') 
        account = self.request.user.account
        account.balance += amount
        account.save(
            update_fields = ['balance']
        )
        messages.success(self.request, f"{amount}$ was deposited to your account Successfully ")

        # Send email notification
        send_transaction_email(self.request.user,amount,"Deposit Message",'transactions/deposit_email.html' )

        return super().form_valid(form)

class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = "Withdraw Money"

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        amount  = form.cleaned_data.get('amount') 
        account = self.request.user.account

        if account.is_bankrupt:
            form.add_error(None, "You are bankrupt and cannot withdraw money.")
            return self.form_invalid(form)
        
        account.balance -= amount
        account.save(
            update_fields = ['balance']
        )
        messages.success(self.request, f"{amount}$ was withdrawn from your account Successfully ")

        send_transaction_email(self.request.user,amount,"Withdrawal Message",'transactions/withdraw_email.html' )
        return super().form_valid(form)
        

class LoanRequestMoneyView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = "Request For Loan"


    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial
    
    def form_valid(self, form):
        amount  = form.cleaned_data.get('amount') 
        current_loan_count = Transaction.objects.filter(account = self.request.user.account, transaction_type = LOAN, loan_approve = True).count()

        if current_loan_count >= 3:
            return HttpResponse("You have crossed the limit of 3 loans")

        messages.success(self.request, f"{amount}$ was requested as a loan Successfully ")

        send_transaction_email(self.request.user,amount,"Loan Request Message",'transactions/loan_request_email.html' )

        return super().form_valid(form)
        
class TransactionReportView(LoginRequiredMixin,ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0
    context_object_name = 'report_list'

    def get_queryset(self):
        queryset = super().get_queryset().filter(account=self.request.user.account)

        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)

            self.balance = Transaction.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date).aggregate(Sum('amount'))['amount__sum']
        
        else:
            self.balance = self.request.user.account.balance
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account,
            'balance': self.balance,
        })
        return context
    
     
class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        print(loan)
        if loan.loan_approve:
            user_account = loan.account
                # Reduce the loan amount from the user's balance
                # 5000, 500 + 5000 = 5500
                # balance = 3000, loan = 5000
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approve = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(
            self.request,
            f'Loan amount is greater than available balance'
        )

        return redirect('loan_list')


class LoanListView(LoginRequiredMixin,ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans' # loan list ta ei loans context er moddhe thakbe
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account=user_account,transaction_type=LOAN)
        print(queryset)
        return queryset


class TransferMoneyView(LoginRequiredMixin,View):
    template_name = 'transactions/transfer_money.html'
    title = 'Transfer Money'
    success_url = reverse_lazy('transaction_report')

    def get(self, request):
        form = TransferMoneyForm(account = request.user.account)
        return render(request, self.template_name, {'form':form, 'title':self.title})
    
    def post(self, request):
        form = TransferMoneyForm(request.POST, account=request.user.account)

        if form.is_valid():
            try:
                recipient_account_number = form.cleaned_data['recipient_account_number']
                amount = form.cleaned_data['amount']
                
                # Get recipient account
                recipient_account = UserBankAccount.objects.get(account_no=recipient_account_number)
                sender_account = request.user.account

                # Check if sender has sufficient balance (this should also be checked in form validation)
                if sender_account.balance < amount:
                    messages.error(request, "Insufficient balance for this transfer.")
                    return render(request, self.template_name, {'form':form, 'title':self.title})

                # Update balances
                recipient_account.balance += amount
                sender_account.balance -= amount

                # Save accounts
                sender_account.save()
                recipient_account.save()

                # Create transaction records
                # For sender (money going out)
                Transaction.objects.create(
                    account = sender_account,
                    amount = amount,
                    balance_after_transaction = sender_account.balance,
                    transaction_type = TRANSFER_SENT
                )

                # For recipient (money coming in)
                Transaction.objects.create(
                    account = recipient_account,
                    amount = amount,
                    balance_after_transaction = recipient_account.balance,
                    transaction_type = TRANSFER_RECEIVED
                )

                messages.success(request, f"${amount} was transferred to account {recipient_account_number} successfully.")

                send_moneytransfer_email(self.request.user,recipient_account.user,recipient_account_number,amount,"Money Transfer Message",'transactions/transfer_email_sender.html', 'transactions/transfer_email_reciver.html')
                return redirect(self.success_url)
                
            except UserBankAccount.DoesNotExist:
                form.error(request, "Recipient account not found.")
                return render(request, self.template_name, {'form':form, 'title':self.title})
            except Exception as e:
                messages.error(request, f"Transfer failed: {str(e)}")
                return render(request, self.template_name, {'form':form, 'title':self.title})
        
        return render(request, self.template_name, {'form':form, 'title':self.title})