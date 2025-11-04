# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.conf import settings
try:
    # JSONField in modern Django
    from django.db.models import JSONField
except Exception:
    JSONField = models.JSONField if hasattr(models, 'JSONField') else None


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Brands(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'brands'


class Categories(models.Model):
    brand = models.ForeignKey(Brands, models.DO_NOTHING, blank=True, null=True)
    sub_brand = models.ForeignKey('SubBrands', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=1, blank=True, null=True)
    pos_uuid = models.CharField(max_length=100, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'categories'


class Channels(models.Model):
    brand = models.ForeignKey(Brands, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=1, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'channels'


class CouponSales(models.Model):
    sale = models.ForeignKey('Sales', models.DO_NOTHING, blank=True, null=True)
    coupon = models.ForeignKey('Coupons', models.DO_NOTHING, blank=True, null=True)
    value = models.FloatField(blank=True, null=True)
    target = models.CharField(max_length=100, blank=True, null=True)
    sponsorship = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'coupon_sales'


class Coupons(models.Model):
    brand = models.ForeignKey(Brands, models.DO_NOTHING, blank=True, null=True)
    code = models.CharField(max_length=50)
    discount_type = models.CharField(max_length=1, blank=True, null=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'coupons'


class Customers(models.Model):
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    cpf = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    store = models.ForeignKey('Stores', models.DO_NOTHING, blank=True, null=True)
    sub_brand = models.ForeignKey('SubBrands', models.DO_NOTHING, blank=True, null=True)
    registration_origin = models.CharField(max_length=20, blank=True, null=True)
    agree_terms = models.BooleanField(blank=True, null=True)
    receive_promotions_email = models.BooleanField(blank=True, null=True)
    receive_promotions_sms = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customers'


class DeliveryAddresses(models.Model):
    sale = models.ForeignKey('Sales', models.DO_NOTHING)
    delivery_sale = models.ForeignKey('DeliverySales', models.DO_NOTHING, blank=True, null=True)
    street = models.CharField(max_length=200, blank=True, null=True)
    number = models.CharField(max_length=20, blank=True, null=True)
    complement = models.CharField(max_length=200, blank=True, null=True)
    formatted_address = models.CharField(max_length=500, blank=True, null=True)
    neighborhood = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    reference = models.CharField(max_length=300, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'delivery_addresses'


class DeliverySales(models.Model):
    sale = models.ForeignKey('Sales', models.DO_NOTHING)
    courier_id = models.CharField(max_length=100, blank=True, null=True)
    courier_name = models.CharField(max_length=100, blank=True, null=True)
    courier_phone = models.CharField(max_length=100, blank=True, null=True)
    courier_type = models.CharField(max_length=100, blank=True, null=True)
    delivered_by = models.CharField(max_length=100, blank=True, null=True)
    delivery_type = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    delivery_fee = models.FloatField(blank=True, null=True)
    courier_fee = models.FloatField(blank=True, null=True)
    timing = models.CharField(max_length=100, blank=True, null=True)
    mode = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'delivery_sales'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class ItemItemProductSales(models.Model):
    item_product_sale = models.ForeignKey('ItemProductSales', models.DO_NOTHING)
    item = models.ForeignKey('Items', models.DO_NOTHING)
    option_group = models.ForeignKey('OptionGroups', models.DO_NOTHING, blank=True, null=True)
    quantity = models.FloatField()
    additional_price = models.FloatField()
    price = models.FloatField()
    amount = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'item_item_product_sales'


class ItemProductSales(models.Model):
    product_sale = models.ForeignKey('ProductSales', models.DO_NOTHING)
    item = models.ForeignKey('Items', models.DO_NOTHING)
    option_group = models.ForeignKey('OptionGroups', models.DO_NOTHING, blank=True, null=True)
    quantity = models.FloatField()
    additional_price = models.FloatField()
    price = models.FloatField()
    amount = models.FloatField(blank=True, null=True)
    observations = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'item_product_sales'


class Items(models.Model):
    brand = models.ForeignKey(Brands, models.DO_NOTHING, blank=True, null=True)
    sub_brand = models.ForeignKey('SubBrands', models.DO_NOTHING, blank=True, null=True)
    category = models.ForeignKey(Categories, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=500)
    pos_uuid = models.CharField(max_length=100, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'items'


class OptionGroups(models.Model):
    brand = models.ForeignKey(Brands, models.DO_NOTHING, blank=True, null=True)
    sub_brand = models.ForeignKey('SubBrands', models.DO_NOTHING, blank=True, null=True)
    category = models.ForeignKey(Categories, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=500)
    pos_uuid = models.CharField(max_length=100, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'option_groups'


class PaymentTypes(models.Model):
    brand = models.ForeignKey(Brands, models.DO_NOTHING, blank=True, null=True)
    description = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'payment_types'


class Payments(models.Model):
    sale = models.ForeignKey('Sales', models.DO_NOTHING)
    payment_type = models.ForeignKey(PaymentTypes, models.DO_NOTHING, blank=True, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    is_online = models.BooleanField(blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payments'


class ProductSales(models.Model):
    sale = models.ForeignKey('Sales', models.DO_NOTHING)
    product = models.ForeignKey('Products', models.DO_NOTHING)
    quantity = models.FloatField()
    base_price = models.FloatField()
    total_price = models.FloatField()
    observations = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_sales'


class Products(models.Model):
    brand = models.ForeignKey(Brands, models.DO_NOTHING, blank=True, null=True)
    sub_brand = models.ForeignKey('SubBrands', models.DO_NOTHING, blank=True, null=True)
    category = models.ForeignKey(Categories, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=500)
    pos_uuid = models.CharField(max_length=100, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products'


class Sales(models.Model):
    store = models.ForeignKey('Stores', models.DO_NOTHING)
    sub_brand = models.ForeignKey('SubBrands', models.DO_NOTHING, blank=True, null=True)
    customer = models.ForeignKey(Customers, models.DO_NOTHING, blank=True, null=True)
    channel = models.ForeignKey(Channels, models.DO_NOTHING)
    cod_sale1 = models.CharField(max_length=100, blank=True, null=True)
    cod_sale2 = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField()
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    sale_status_desc = models.CharField(max_length=100)
    total_amount_items = models.DecimalField(max_digits=10, decimal_places=2)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_increase = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    service_tax_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    value_paid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    production_seconds = models.IntegerField(blank=True, null=True)
    delivery_seconds = models.IntegerField(blank=True, null=True)
    people_quantity = models.IntegerField(blank=True, null=True)
    discount_reason = models.CharField(max_length=300, blank=True, null=True)
    increase_reason = models.CharField(max_length=300, blank=True, null=True)
    origin = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sales'


class Stores(models.Model):
    brand = models.ForeignKey(Brands, models.DO_NOTHING, blank=True, null=True)
    sub_brand = models.ForeignKey('SubBrands', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    address_street = models.CharField(max_length=200, blank=True, null=True)
    address_number = models.IntegerField(blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    is_own = models.BooleanField(blank=True, null=True)
    is_holding = models.BooleanField(blank=True, null=True)
    creation_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stores'


class SubBrands(models.Model):
    brand = models.ForeignKey(Brands, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sub_brands'


class DashboardLayout(models.Model):
    """Per-user (or per-session) saved dashboard layout (order and visibility).

    Note: after adding this model you should create and apply a migration to
    persist this table. For local-first behaviour the frontend continues to
    write to localStorage; this model provides optional server-side persistence.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    layout = JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dashboard_layouts'
