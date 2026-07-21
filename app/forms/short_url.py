from django import forms


class ShortURLForm(forms.Form):
    original_url = forms.URLField(
        label="",
        max_length=2048,
        widget=forms.URLInput(
            attrs={
                "placeholder": "https://example.com",
                "class": "form-control",
            }
        ),
    )
