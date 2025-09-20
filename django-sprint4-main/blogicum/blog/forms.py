from django import forms
from django.utils import timezone
from .models import Post, Comment, Category

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "text", "category", "location", "image", "pub_date"]
        widgets = {
            "text": forms.Textarea(),
            "pub_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].required = False
        self.fields["category"].queryset = Category.objects.filter(is_published=True)

    def clean_category(self):
        cat = self.cleaned_data["category"]
        if not getattr(cat, "is_published", True):
            raise forms.ValidationError("Категория должна быть опубликована.")
        return cat

    def clean_pub_date(self):
        dt = self.cleaned_data["pub_date"]
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        dt = dt.replace(microsecond=0)
        now = timezone.now().replace(microsecond=0)
        if 0 <= (dt - now).total_seconds() <= 60:
            dt = now
        return dt

    def save(self, commit=True):
        post = super().save(commit=False)
        if commit:
            post.save()
            self.save_m2m()
        return post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
