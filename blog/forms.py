from django import forms
from .models import Comment

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    subject = forms.CharField(max_length=200, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
    
    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long")
        return name

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'email', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not email.endswith(('.com', '.org', '.net', '.edu')):
            # This is a simple validation, you might want to use more sophisticated checks
            pass
        return email