from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from decouple import config
import pymongo
from bson import ObjectId

# Create your models here.

class Slider(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    title = models.TextField(blank=True, null=True, help_text="Enter title with line breaks using Enter key")
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    img = models.URLField(blank=True, null=True, help_text="Image URL for the slider")
    link = models.URLField(blank=True, null=True, help_text="Link URL when slider is clicked")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Slider'
        verbose_name_plural = 'Sliders'
        unique_together = ['order']  # Re-enabled unique constraint
    
    def __str__(self):
        return self.title or f"Slider {self.id}"
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    def clean(self):
        """Validate the model"""
        super().clean()
        
        # Check if order number is unique (excluding self)
        if self.order:
            existing = Slider.objects.filter(order=self.order)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError({
                    'order': f'Order number {self.order} is already taken. Please choose a different order number.'
                })
    
    @classmethod
    def get_next_order(cls):
        """Get the next available order number"""
        max_order = cls.objects.aggregate(models.Max('order'))['order__max'] or 0
        return max_order + 1
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()  # Re-enabled validation
        super().save(*args, **kwargs)
        
        # Also save to MongoDB if configured
        self.save_to_mongodb()
    
    def save_to_mongodb(self):
        """Save slider data to MongoDB"""
        try:
            # Connect to MongoDB using connection string
            connection_string = config('MONGODB_CONNECTION_STRING', default='')
            if connection_string:
                client = pymongo.MongoClient(connection_string)
            else:
                # Fallback to individual settings
                client = pymongo.MongoClient(
                    host=settings.MONGODB_CONFIG['host'],
                    port=settings.MONGODB_CONFIG['port']
                )
            db = client[settings.MONGODB_CONFIG['database']]
            collection = db['sliders']  # Use 'sliders' collection
            
            # Prepare data for MongoDB
            slider_data = {
                'title': self.title,
                'subtitle': self.subtitle,
                'description': self.description,
                'img': self.img,
                'link': self.link,
                'status': self.status,
                'order': self.order,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'django_id': self.id  # Keep reference to Django ID
            }
            
            # Update or insert in MongoDB
            collection.update_one(
                {'django_id': self.id},
                {'$set': slider_data},
                upsert=True
            )
            
            client.close()
        except Exception as e:
            print(f"Error saving to MongoDB: {e}")
    
    def delete(self, *args, **kwargs):
        """Delete from both Django and MongoDB"""
        # Delete from MongoDB first
        try:
            connection_string = config('MONGODB_CONNECTION_STRING', default='')
            if connection_string:
                client = pymongo.MongoClient(connection_string)
            else:
                # Fallback to individual settings
                client = pymongo.MongoClient(
                    host=settings.MONGODB_CONFIG['host'],
                    port=settings.MONGODB_CONFIG['port']
                )
            db = client[settings.MONGODB_CONFIG['database']]
            collection = db['sliders']
            collection.delete_one({'django_id': self.id})
            client.close()
        except Exception as e:
            print(f"Error deleting from MongoDB: {e}")
        
        # Delete from Django
        super().delete(*args, **kwargs)
