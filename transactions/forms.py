from django import forms
from .models import Transaction
from accounts.models import UserBankAccount

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields =['amount','transaction_type']

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit = True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):
    def clean_amount(self):
        min_deposite_amount = 100
        amount = self.cleaned_data.get('amount')

        if amount < min_deposite_amount:
            raise forms.ValidationError(
                f"You Need to deposite at least {min_deposite_amount} $"
            )
        return amount
    

class WithdrawForm(TransactionForm):
    def clean_amount(self):
        account  = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance
        amount = self.cleaned_data.get('amount')
        # print(balance)
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f"You Need to withdraw at least {min_withdraw_amount} $"
            )
        elif amount > max_withdraw_amount:
            raise forms.ValidationError(
                f"You Need to withdraw at most {max_withdraw_amount} $"
            )
        elif amount > balance:
            raise forms.ValidationError(
                f'You have {balance} $ in your Account.'
                'You Can not withdraw more then your Account Balance.'
            )
        return amount
    

class LoanRequestForm(TransactionForm):

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        
        return amount
    

class TransferMoneyForm(forms.Form):
    recipient_account_number = forms.IntegerField(label="Recipient Account Number")
    amount = forms.DecimalField(decimal_places=2, max_digits=12, label="Transfer Amount")

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to form fields
        self.fields['recipient_account_number'].widget.attrs.update({
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight border rounded-md border-gray-500 focus:outline-none focus:shadow-outline',
            'placeholder': 'Enter recipient account number',
            'type': 'number'
        })
        
        self.fields['amount'].widget.attrs.update({
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight border rounded-md border-gray-500 focus:outline-none focus:shadow-outline',
            'placeholder': 'Enter transfer amount',
            'type': 'number',
            'step': '0.01'
        })

    def clean_amount(self):
        account = self.account
        amount = self.cleaned_data.get('amount')

        if amount > account.balance:
            raise forms.ValidationError("Insufficient balance for transfer.")
        elif amount <=0:
            raise forms.ValidationError("Transfer amount must be greater than zero.")
        return amount
    

    def clean_recipient_account_number(self):
        recipient_account_number = self.cleaned_data.get('recipient_account_number')
        
        # Check if recipient_account_number is provided
        if not recipient_account_number:
            raise forms.ValidationError("Recipient account number is required.")
        
        # Convert to integer to ensure proper comparison
        try:
            recipient_account_number = int(recipient_account_number)
        except (ValueError, TypeError):
            raise forms.ValidationError("Please enter a valid account number.")
        
        # Check if recipient account exists
        if not UserBankAccount.objects.filter(account_no=recipient_account_number).exists():
            raise forms.ValidationError("Recipient account does not exist.")
        
        # Check if user is trying to transfer to their own account
        if recipient_account_number == self.account.account_no:
            raise forms.ValidationError("You cannot transfer money to your own account.")
        
        return recipient_account_number

