from django import forms

class ArticleForm(forms.Form):
    site_choices = (
        ('site1', 'Site 1'),
        ('site2', 'Site 2'),
        # Add other site choices
    )
    site = forms.ChoiceField(choices=site_choices)
    topic = forms.CharField(max_length=1000)
