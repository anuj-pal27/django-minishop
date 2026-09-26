from decimal import Decimal

from rest_framework import serializers

from .models import Category, Product


# ---------- 1) Written by hand: so you see what each part does ----------

class ProductManualSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)             # sent out, never accepted in
    name = serializers.CharField(max_length=200)              # required text, max 200
    slug = serializers.SlugField(max_length=200)              # NOTE: no unique check here!
    price = serializers.DecimalField(max_digits=10, decimal_places=2,
                                     min_value=Decimal("0.01"))  # must be > 0
    stock = serializers.IntegerField(min_value=0, default=0)  # whole number, 0 or more
    category = serializers.SlugRelatedField(
        slug_field="slug",                                    # client sends "clothing", not an id
        queryset=Category.objects.all(),                      # must exist, else error
    )

    def create(self, validated_data):                         # called by .save() for NEW objects
        return Product.objects.create(**validated_data)       # ** = unpack dict into arguments

    def update(self, instance, validated_data):               # called by .save() for EXISTING objects
        for field, value in validated_data.items():
            setattr(instance, field, value)                   # instance.<field> = value
        instance.save()
        return instance


# ---------- 2) ModelSerializer: reads the model and writes the fields for you ----------

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="slug", queryset=Category.objects.all())

    class Meta:
        model = Product                                         # read fields from this model
        fields = ["id", "name", "slug", "price", "stock", "category"]  # which ones to include
        extra_kwargs = {"price": {"min_value": Decimal("0.01")}}       # extra rule the model doesn't have


# ---------- Exercise ----------

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]         # name + slug get unique checks automatically

class RestockSerializer(serializers.Serializer):     # not tied to a model, just checks input
    amount = serializers.IntegerField(min_value=1)   # must be a whole number, 1 or more