from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
import uuid


class MedicineCategory(models.Model):
    """Medicines classification (e.g., Tablet, Capsule, Syrup, Injection)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Medicine Categories"


class GenericName(models.Model):
    """Chemical/Generic formulation (e.g., Paracetamol, Omeprazole)"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Pharmaceutical Company (e.g., Square, Incepta, Beximco)"""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MedicineProduct(models.Model):
    """Main Medicine Product Model featuring Structured Tab Data"""
    name = models.CharField(max_length=255, help_text="Brand name of the medicine (e.g., Renix Ginseng Syrup)")
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    strength = models.CharField(max_length=50, help_text="e.g., 500mg, 20mg, 100ml, 200ml")
    
    category = models.ForeignKey(MedicineCategory, on_delete=models.PROTECT, related_name='medicines')
    generic_name = models.ForeignKey(GenericName, on_delete=models.PROTECT, related_name='medicines')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, related_name='medicines')
    
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Buying price from manufacturer")
    mrp = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Maximum Retail Price (MRP)")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    stock_quantity = models.PositiveIntegerField(default=0)
    sku_code = models.CharField(max_length=100, unique=True, blank=True, help_text="Stock Keeping Unit / Barcode token")
    
    requires_prescription = models.BooleanField(default=False, help_text="True if it's a prescription-only drug (Schedule H)")
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TAB 1: DESCRIPTION FIELD DATA
    description = models.TextField(
        blank=True, 
        null=True, 
        help_text="General description/overview of the medicine (e.g., Renix Ginseng Syrup is an effective general tonic...)"
    )
    indications = models.TextField(
        blank=True, 
        null=True, 
        help_text="What diseases/conditions this works for"
    )
    ingredients = models.TextField(
        blank=True, 
        null=True, 
        help_text="Medicinal herbs or chemical formulas included (e.g., Jatrik, Nutmeg, Ashwagandha)"
    )

    # TAB 2: DOSAGE FORM FIELD DATA
    dosage_instructions = models.TextField(
        blank=True, 
        null=True, 
        help_text="e.g., Take 2-4 teaspoons (10-20 ml) 2-3 times daily."
    )
    administration = models.TextField(
        blank=True, 
        null=True, 
        help_text="e.g., Consume as directed, preferably before meals."
    )
    side_effects = models.TextField(
        blank=True, 
        null=True, 
        help_text="Side effects details (e.g., No significant side effects have been observed.)"
    )

    @property
    def selling_price(self):
        if self.discount_percentage > 0:
            discount_amount = (self.mrp * self.discount_percentage) / 100
            return round(self.mrp - discount_amount, 2)
        return self.mrp

    @property
    def is_low_stock(self):
        return self.stock_quantity <= 20

    @property
    def primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary.image
        first_img = self.images.first()
        return first_img.image if first_img else None

    def save(self, *args, **kwargs):
        # Automatic Slug Generation
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.strength}")
            
        # Automatic SKU Code Generation
        if not self.sku_code:
            prefix = slugify(self.name)[:3].upper() if self.name else "MED"
            unique_suffix = uuid.uuid4().hex[:8].upper()
            generated_sku = f"{prefix}-{unique_suffix}"
            
            while MedicineProduct.objects.filter(sku_code=generated_sku).exists():
                unique_suffix = uuid.uuid4().hex[:8].upper()
                generated_sku = f"{prefix}-{unique_suffix}"
                
            self.sku_code = generated_sku

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} {self.strength}"


class MedicineImage(models.Model):
    """Multiple Images for a single Medicine Product"""
    medicine = models.ForeignKey(MedicineProduct, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('image', folder='medicines/')
    is_primary = models.BooleanField(default=False, help_text="Check if this is the main image for the product.")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_primary:
            MedicineImage.objects.filter(medicine=self.medicine, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.medicine.name} (Primary: {self.is_primary})"


# TAB 3: FAQ MODEL
class MedicineFAQ(models.Model):
    """Dynamic FAQs linked to specific medicines"""
    medicine = models.ForeignKey(MedicineProduct, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=500, help_text="e.g., What are the benefits of taking ginseng syrup?")
    answer = models.TextField(help_text="Answer to the corresponding question")
    order = models.PositiveIntegerField(default=0, help_text="Used to arrange the sequence of questions")

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"FAQ Q: {self.question[:40]}... ({self.medicine.name})"


# TAB 4: REVIEWS MODEL
class MedicineReview(models.Model):
    """Product Review and Rating Architecture"""
    medicine = models.ForeignKey(MedicineProduct, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=100, help_text="Reviewer Name (e.g., Saruar)")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Optional Phone Field")
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 Stars"
    )
    comment = models.TextField(help_text="Review text (e.g., 100% effective product.)")
    attachment = CloudinaryField('review_attachment', folder='reviews/', blank=True, null=True, help_text="Optional File chosen input")
    is_approved = models.BooleanField(default=True, help_text="Toggle to hide/show reviews if moderation needed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating} Star Review by {self.name} for {self.medicine.name}"