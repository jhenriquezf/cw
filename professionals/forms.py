# professionals/forms.py
from django import forms
from .models import Certification

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name', 'institution', 'year', 'document']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g. TRX Certification Level 2',
                'class': 'form-input w-full rounded-lg border border-primary/30 bg-background-light dark:bg-background-dark focus:ring-primary focus:border-primary placeholder:text-black/50 dark:placeholder:text-white/50'
            }),
            'institution': forms.TextInput(attrs={
                'placeholder': 'e.g. Fitness Training Institute',
                'class': 'form-input w-full rounded-lg border border-primary/30 bg-background-light dark:bg-background-dark focus:ring-primary focus:border-primary placeholder:text-black/50 dark:placeholder:text-white/50'
            }),
            'year': forms.NumberInput(attrs={
                'placeholder': 'e.g. 2022', 'min': '1950', 'max': '2100',
                'class': 'form-input w-full rounded-lg border border-primary/30 bg-background-light dark:bg-background-dark focus:ring-primary focus:border-primary placeholder:text-black/50 dark:placeholder:text-white/50'
            }),
        }
