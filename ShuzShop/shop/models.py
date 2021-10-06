from PIL import Image
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_yrl(obj, viewname):
    ct_model = obj.__class__._meeta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


class MinResolutionErrorException(Exception):
    pass


class MaxResolutionErrorException(Exception):
    pass


class LatestProductsManager:

    @staticmethod
    def get_products_for_page(*args, **kwargs):
        with_respect_to = kwargs.get("with_respect_to")
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products, key=lambda x: x.__class__._meta.model_name.startwith(with_respect_to), reverse=True
                    )
        return products


class LatestProducts:
    objects = LatestProductsManager()


class CategoryManager(models.Manager):

    CATEGORY_NAME_COUNT_NAME = {
        'Ноутбуки': 'notebook__count',
        'Смaртфоны': 'smartphone__count'
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        models = get_models_for_count('notebook', 'smartphone')
        qs = list(self.get_queryset().annotate(*models))
        deta=[
            dict(name=c.name, url=c.get_absolute_url())
            for c in qs
        ]
        return deta


class Category(models.Model):

    name = models.CharField(max_length=255, verbose_name="Имя котегории")
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug':self.slug})


class Prodyct(models.Model):
    MIN_RESOLUTION = (100, 100)
    MAX_RESOLUTION = (3000, 3000)
    MAX_IMAGE_SIZE = 5145728

    class Meta:
        abstract = True

    category = models.ForeignKey(Category, verbose_name="Категории", on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name="Наименование")
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name="изображение")
    description = models.TextField(verbose_name="Описание", null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="Цена")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        image = self.image
        img = Image.open(image)
        min_height, min_width = self.MIN_RESOLUTION
        max_height, max_width = self.MAX_RESOLUTION
        if img.height < min_height or img.width < min_width:
            raise MinResolutionErrorException('Разрешение изображения меньше минимального!')
        if img.height > max_height or img.width > max_width:
            raise MaxResolutionErrorException('Разрешение изображения больше максимального')
        super().save(*args, **kwargs)


class Notebook(Prodyct):
    diagonal = models.CharField(max_length=255, verbose_name='Диоганаль')
    display_type = models.CharField(max_length=255, verbose_name='тип дисплея')
    processor_freq = models.CharField(max_length=255, verbose_name='частота процессора')
    ram = models.CharField(max_length=255, verbose_name='оперативная память ')
    video = models.CharField(max_length=255, verbose_name='видеокарта')
    time_without_charge = models.CharField(max_length=255, verbose_name='время автономной работы')
    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_yrl(self, 'product_detail')


class Smartphone(Prodyct):
    diagonal = models.CharField(max_length=255, verbose_name='Диоганаль')
    display_type = models.CharField(max_length=255, verbose_name='тип дисплее')
    resulution = models.CharField(max_length=255, verbose_name='разрешение экрана')
    accum_volume = models.CharField(max_length=255, verbose_name='обьем батареи')
    ram = models.CharField(max_length=255, verbose_name='оперативная память ')
    sd = models.BooleanField(default=True)
    main_cam_mp = models.CharField(max_length=255, verbose_name='главная камера ')
    frontal_cam_mp = models.CharField(max_length=255, verbose_name='фронтальная камера')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_yrl(self, 'product_detail')


class CardProduct(models.Model):
    user = models.ForeignKey("Custoner", verbose_name="Покупатель", on_delete=models.CASCADE)
    card = models.ForeignKey("Cart", verbose_name="Корзина", on_delete=models.CASCADE, related_name="related_products")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="Общая цена")


    def __str__(self):
        return "Продукт: {} (для корзины)".format(self.content_object.title)


class Cart(models.Model):
    owner = models.ForeignKey("Custoner", verbose_name="Владелец", on_delete=models.CASCADE)
    products = models.ManyToManyField(CardProduct, blank=True, related_name="related_card")
    total_products = models.PositiveIntegerField(default=8)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="Общая цена")
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Custoner(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name="Номер телефона")
    address = models.CharField(max_length=255, verbose_name="Адрес")

    def __str__(self):
        return "Покупатель: {} {}".format(self.user.first_name, self.user.last_name)
