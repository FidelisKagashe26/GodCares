from django import forms
from .models import Order

class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)
    size = forms.CharField(required=False)
    color = forms.CharField(required=False)

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["full_name", "phone", "email", "address", "notes"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
