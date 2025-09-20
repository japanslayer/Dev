from django.contrib.auth import get_user_model
from django.db import models

from blogicum.constants import (
    CATEGORY_SLUG_MAX_LENGTH,
    CATEGORY_STR_MAX_LENGTH,
    CATEGORY_TITLE_MAX_LENGTH,
    LOCATION_NAME_MAX_LENGTH,
    POST_TITLE_MAX_LENGTH,
)
from .managers import PublishedManager


User = get_user_model()


class Comment(models.Model):
    post = models.ForeignKey(
        "Post", on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Комментарий от {self.author} к {self.post}"

    class Meta:
        ordering = ("created_at",) 

class PublishedModel(models.Model):
    is_published = models.BooleanField(
        default=True,
        verbose_name="Опубликовано",
        help_text="Снимите галочку, чтобы скрыть публикацию.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлено",
        help_text="Дата и время создания объекта",
    )

    class Meta:
        abstract = True
        ordering = ("-created_at",)


class BaseNamedModel(PublishedModel):
    name = models.CharField(
        max_length=LOCATION_NAME_MAX_LENGTH,
        verbose_name="Название места",
        help_text="Введите название",
    )

    class Meta(PublishedModel.Meta):
        abstract = True

    def __str__(self):
        return self.name


class Category(PublishedModel):
    title = models.CharField(
        max_length=CATEGORY_TITLE_MAX_LENGTH,
        verbose_name="Заголовок",
        help_text="Введите название категории",
    )
    slug = models.SlugField(
        max_length=CATEGORY_SLUG_MAX_LENGTH,
        unique=True,
        verbose_name="Идентификатор",
        help_text=(
            "Идентификатор страницы для URL; "
            "разрешены символы латиницы, цифры, дефис и подчёркивание."
        ),
    )
    description = models.TextField(
        verbose_name="Описание",
        help_text="Краткое описание категории",
    )

    class Meta(PublishedModel.Meta):
        verbose_name = "категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.title[:CATEGORY_STR_MAX_LENGTH]


class Location(BaseNamedModel):
    class Meta(BaseNamedModel.Meta):
        verbose_name = "местоположение"
        verbose_name_plural = "Местоположения"


class Post(PublishedModel):
    title = models.CharField(
        max_length=POST_TITLE_MAX_LENGTH,
        verbose_name="Заголовок",
        help_text="Введите заголовок поста",
    )
    text = models.TextField(
        verbose_name="Текст",
        help_text="Введите текст поста",
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата и время публикации",
        help_text="Если установить дату и время "
                  "в будущем — можно делать отложенные публикации.",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор публикации",
        help_text="Автор публикации",
    )
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Местоположение",
        help_text="Местоположение публикации",
    )
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        verbose_name="Категория",
        help_text="Категория публикации",
    )
    image = models.ImageField(
    upload_to="posts_images/",
    blank=True,
    null=True,
    verbose_name="Изображение",
    help_text="Загрузите изображение для публикации",
    )

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        verbose_name = "публикация"
        verbose_name_plural = "Публикации"
        ordering = ["-pub_date"]

    def __str__(self):
        return self.title
