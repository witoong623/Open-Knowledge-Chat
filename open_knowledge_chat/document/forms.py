from django import forms

from document.models import Document


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']
