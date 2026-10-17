from django import forms

from document.models import Document


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']


class WebsiteURLForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['url'].required = True
