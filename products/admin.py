from django.contrib import admin
from .models import (
    MedicineCategory, 
    GenericName, 
    Manufacturer, 
    MedicineProduct, 
    MedicineImage, 
    MedicineFAQ, 
    MedicineReview
)

# Inline config for product images
class MedicineImageInline(admin.TabularInline):
    model = MedicineImage
    extra = 1
    fields = ('image', 'is_primary')


# Inline config for FAQs (Tab 3)
class MedicineFAQInline(admin.TabularInline):
    model = MedicineFAQ
    extra = 1
    fields = ('question', 'answer', 'order')


# Inline config for User Reviews (Tab 4)
class MedicineReviewInline(admin.StackedInline):
    model = MedicineReview
    extra = 0  # Generally, you don't want empty review inputs by default
    readonly_fields = ('name', 'phone', 'rating', 'comment', 'attachment', 'created_at')
    fields = ('name', 'phone', 'rating', 'comment', 'attachment', 'is_approved', 'created_at')
    can_delete = True


@admin.register(MedicineCategory)
class MedicineCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(GenericName)
class GenericNameAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'contact_number', 'is_active')
    search_fields = ('name', 'contact_email', 'contact_number')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(MedicineProduct)
class MedicineProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'strength', 'category', 'manufacturer', 'mrp', 'stock_quantity', 'is_available', 'requires_prescription')
    list_filter = ('is_available', 'requires_prescription', 'category', 'manufacturer')
    search_fields = ('name', 'sku_code', 'generic_name__name', 'manufacturer__name')
    prepopulated_fields = {'slug': ('name', 'strength')}
    readonly_fields = ('created_at', 'updated_at')
    
    # Manage multiple Inlines inside Product details page (Images, FAQs, Reviews)
    inlines = [MedicineImageInline, MedicineFAQInline, MedicineReviewInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'strength')
        }),
        ('TAB 1: Description & Overview', {
            'fields': ('description', 'indications', 'ingredients')
        }),
        ('TAB 2: Dosage & Administration', {
            'fields': ('dosage_instructions', 'administration', 'side_effects')
        }),
        ('Relationships', {
            'fields': ('category', 'generic_name', 'manufacturer')
        }),
        ('Pricing & Inventory', {
            'fields': ('purchase_price', 'mrp', 'discount_percentage', 'stock_quantity', 'sku_code')
        }),
        ('Requirements & Status', {
            'fields': ('requires_prescription', 'is_available')
        }),
        ('Important Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# Optional standalone registers for managing FAQs and Reviews directly
@admin.register(MedicineFAQ)
class MedicineFAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'medicine', 'order')
    list_filter = ('medicine',)
    search_fields = ('question', 'answer', 'medicine__name')


@admin.register(MedicineReview)
class MedicineReviewAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'name', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('name', 'comment', 'medicine__name')