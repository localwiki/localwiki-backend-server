from django import forms

class CommentForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea())
