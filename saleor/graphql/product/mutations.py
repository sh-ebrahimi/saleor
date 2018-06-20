import graphene
from graphene.types import InputObjectType
from graphql_jwt.decorators import permission_required
from graphene_file_upload import Upload

from ...product import models
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..utils import get_attributes_dict_from_list, get_node, get_nodes
from .types import Collection, Product


class CategoryInput(graphene.InputObjectType):
    description = graphene.String(description='Category description')
    name = graphene.String(description='Category name')
    parent = graphene.ID(
        description='''
        ID of the parent category. If empty, category will be top level
        category.''')
    slug = graphene.String(description='Category slug')


class CategoryCreateMutation(ModelMutation):
    class Arguments:
        input = CategoryInput(
            required=True, description='Fields required to create a category.')

    class Meta:
        description = 'Creates a new category.'
        model = models.Category

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('category.edit_category')


class CategoryUpdateMutation(ModelMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a category to update.')
        input = CategoryInput(
            required=True, description='Fields required to update a category.')

    class Meta:
        description = 'Updates a category.'
        model = models.Category

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('category.edit_category')


class CategoryDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a category to delete.')

    class Meta:
        description = 'Deletes a category.'
        model = models.Category

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('category.edit_category')


class CollectionInput(graphene.InputObjectType):
    is_published = graphene.Boolean(
        description='Informs whether a collection is published.')
    name = graphene.String(description='Name of the collection.')
    slug = graphene.String(description='Slug of the collection.')
    products = graphene.List(
        graphene.ID,
        description='List of products to be added to the collection.')
    background_image = Upload(description='Background image file.')


class CollectionCreateMutation(ModelMutation):
    class Arguments:
        input = CollectionInput(
            required=True,
            description='Fields required to create a collection.')

    class Meta:
        description = 'Creates a new collection.'
        model = models.Collection

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('collection.edit_collection')


class CollectionUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a collection to update.')
        input = CollectionInput(
            required=True,
            description='Fields required to update a collection.')

    class Meta:
        description = 'Updates a collection.'
        model = models.Collection

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('collection.edit_collection')


class CollectionDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a collection to delete.')

    class Meta:
        description = 'Deletes a collection.'
        model = models.Collection

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('collection.edit_collection')


class CollectionAddProducts(BaseMutation):
    class Arguments:
        collection_id = graphene.Argument(
            graphene.ID, required=True,
            description='ID of a collection.')
        products = graphene.List(
            graphene.ID, required=True,
            description='List of product IDs.')

    collection = graphene.Field(
        Collection,
        description='Collection to which products will be added.')

    class Meta:
        description = 'Adds products to a collection.'

    @permission_required('collection.edit_collection')
    def mutate(self, info, collection_id, products):
        collection = get_node(info, collection_id, only_type=Collection)
        products = get_nodes(products, Product)
        collection.products.add(*products)
        return CollectionAddProducts(collection=collection)


class CollectionRemoveProducts(BaseMutation):
    class Arguments:
        collection_id = graphene.Argument(
            graphene.ID, required=True, description='ID of a collection.')
        products = graphene.List(
            graphene.ID, required=True, description='List of product IDs.')

    collection = graphene.Field(
        Collection,
        description='Collection from which products will be removed.')

    class Meta:
        description = 'Remove products from a collection.'

    @permission_required('collection.edit_collection')
    def mutate(self, info, collection_id, products):
        collection = get_node(info, collection_id, only_type=Collection)
        products = get_nodes(products, Product)
        collection.products.remove(*products)
        return CollectionRemoveProducts(collection=collection)


class AttributeValueInput(InputObjectType):
    slug = graphene.String(
        required=True, description='Slug of an attribute.')
    value = graphene.String(
        required=True, description='Value of an attribute.')


class ProductInput(graphene.InputObjectType):
    attributes = graphene.List(AttributeValueInput)
    available_on = graphene.String()
    category = graphene.ID()
    charge_taxes = graphene.Boolean()
    description = graphene.String()
    is_published = graphene.Boolean()
    is_featured = graphene.Boolean()
    name = graphene.String()
    product_type = graphene.ID()
    price = graphene.Float()
    tax_rate = graphene.String()


class ProductCreateMutation(ModelMutation):
    class Arguments:
        input = ProductInput(
            required=True, description='Fields required to create a product.')

    class Meta:
        description = 'Creates a new product.'
        model = models.Product

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)

        # Attributes are provided as list of `AttributeValueInput` objects.
        # We need to transform them into the format they're stored in the
        # `Product` model, which is HStore field that maps attribute's PK to
        # the value's PK.

        attributes = cleaned_input.pop('attributes', [])
        product_type = (
            instance.product_type
            if instance.pk else cleaned_input.get('product_type'))

        if attributes and product_type:
            slug_to_id_map = dict(
                product_type.product_attributes.values_list('slug', 'id'))
            attributes = get_attributes_dict_from_list(
                attributes, slug_to_id_map)
            cleaned_input['attributes'] = attributes
        return cleaned_input

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_product')


class ProductUpdateMutation(ProductCreateMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a product to update.')
        input = ProductInput(
            required=True, description='Fields required to update a product.')

    class Meta:
        description = 'Updates an existing product.'
        model = models.Product


class ProductDeleteMutation(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a product to delete.')

    class Meta:
        description = 'Deletes a product.'
        model = models.Product

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_product')


class ProductVariantInput(graphene.InputObjectType):
    attributes = graphene.List(AttributeValueInput)
    cost_price = graphene.Float()
    name = graphene.String()
    price_override = graphene.Float()
    product = graphene.ID()
    sku = graphene.String()
    quantity = graphene.Int()
    track_inventory = graphene.Boolean()


class ProductVariantCreateMutation(ModelMutation):
    class Arguments:
        input = ProductVariantInput(
            required=True,
            description='Fields required to create a product variant.')

    class Meta:
        description = 'Creates a new variant for a product'
        model = models.ProductVariant

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)

        # Attributes are provided as list of `AttributeValueInput` objects.
        # We need to transform them into the format they're stored in the
        # `Product` model, which is HStore field that maps attribute's PK to
        # the value's PK.

        attributes = cleaned_input.pop('attributes', [])
        product = instance.product if instance.pk else cleaned_input.get('product')
        product_type = product.product_type

        if attributes and product_type:
            slug_to_id_map = dict(
                product_type.variant_attributes.values_list('slug', 'id'))
            attributes = get_attributes_dict_from_list(
                attributes, slug_to_id_map)
            cleaned_input['attributes'] = attributes
        return cleaned_input

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_product')


class ProductVariantUpdateMutation(ProductVariantCreateMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a product variant to update.')
        input = ProductVariantInput(
            required=True,
            description='Fields required to update a product variant.')

    class Meta:
        description = 'Updates an existing variant for product'
        model = models.ProductVariant


class ProductVariantDeleteMutation(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a product variant to delete.')

    class Meta:
        description = 'Deletes a product variant.'
        model = models.ProductVariant

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_product')


class ProductTypeInput(graphene.InputObjectType):
    name = graphene.String()
    has_variants = graphene.Boolean()
    product_attributes = graphene.List(graphene.ID)
    variant_attributes = graphene.List(graphene.ID)
    is_shipping_required = graphene.Boolean()


class ProductTypeCreateMutation(ModelMutation):
    class Arguments:
        input = ProductTypeInput(
            required=True,
            description='Fields required to create a product type.')

    class Meta:
        description = 'Creates a new product type.'
        model = models.ProductType

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_properties')


class ProductTypeUpdateMutation(ModelMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a product type to update.')
        input = ProductTypeInput(
            required=True,
            description='Fields required to update a product type.')

    class Meta:
        description = 'Updates an existing product type.'
        model = models.ProductType

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_properties')


class ProductTypeDeleteMutation(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a product type to delete.')

    class Meta:
        description = 'Deletes a product type.'
        model = models.ProductType

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_properties')


class ProductImageInput(graphene.InputObjectType):
    alt = graphene.String(description='Alt text for an image.')
    image = Upload(required=True, description='Image file.')
    product = graphene.ID(description='ID of an product.')


class ProductImageCreateMutation(ModelMutation):
    class Arguments:
        input = ProductImageInput(
            required=True,
            description='Fields required to create a product image.')

    class Meta:
        description = 'Creates a product image.'
        model = models.ProductImage

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_product')