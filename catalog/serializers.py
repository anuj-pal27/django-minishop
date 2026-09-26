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

BANNED_WORDS = ["fake", "replica"]


def no_banned_words(value):                               # reusable validator (a plain function)
    for word in BANNED_WORDS:
        if word in value.lower():
            raise serializers.ValidationError(f'The word "{word}" is not allowed.')
    # no return needed: no error = valid


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="slug", queryset=Category.objects.all())

    class Meta:
        model = Product                                   # read fields from this model
        fields = ["id", "name", "slug", "price", "stock", "category"]
        extra_kwargs = {
            "price": {"min_value": Decimal("0.01")},      # extra rule the model doesn't have
            "name": {"validators": [no_banned_words]},    # attach the reusable validator to "name"
        }

    def validate_name(self, value):                       # field-level: validate_<field name>
        value = value.strip()                             # remove spaces at start/end
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters.")
        return value                                      # MUST return: this value gets saved

    def validate_slug(self, value):                       # 1B-4 exercise
        if len(value) > 50:
            raise serializers.ValidationError("Slug must be 50 characters or less.")
        if "--" in value:
            raise serializers.ValidationError("Slug must not contain a double dash (--).")
        return value

    def validate(self, attrs):                            # object-level: sees ALL fields
        # On PATCH, attrs only has the sent fields -> fall back to the existing product
        category = attrs.get("category", getattr(self.instance, "category", None))
        price = attrs.get("price", getattr(self.instance, "price", None))

        if category and category.slug == "electronics" and price is not None and price < 100:
            raise serializers.ValidationError({"price": "Electronics must cost at least ₹100."})
        return attrs                                      # MUST return attrs


# ---------- Exercise ----------

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]         # name + slug get unique checks automatically

class RestockSerializer(serializers.Serializer):     # not tied to a model, just checks input
    amount = serializers.IntegerField(min_value=1)   # must be a whole number, 1 or more