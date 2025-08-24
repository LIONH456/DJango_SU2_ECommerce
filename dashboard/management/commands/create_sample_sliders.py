from django.core.management.base import BaseCommand
from dashboard.models import Slider

class Command(BaseCommand):
    help = 'Create sample sliders for testing'

    def handle(self, *args, **options):
        # Clear existing sliders
        Slider.objects.all().delete()
        
        # Create sample sliders
        sliders_data = [
            {
                'title': 'Fashion\nChanging\nAlways',
                'subtitle': 'Discover the latest trends',
                'description': 'Explore our collection of trendy fashion items that will keep you ahead of the style curve.',
                'img': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80',
                'link': '',
                'status': 'active',
                'order': 1
            },
            {
                'title': 'Trendy\nStyles\nEveryday',
                'subtitle': 'Express your unique style',
                'description': 'From casual wear to elegant evening dresses, we have everything you need to express your personality.',
                'img': 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80',
                'link': '',
                'status': 'active',
                'order': 2
            },
            {
                'title': 'Elegant\nFashion\nForward',
                'subtitle': 'Premium quality fashion',
                'description': 'Step into sophistication with our premium collection of elegant fashion pieces.',
                'img': 'https://images.unsplash.com/photo-1445205170230-053b83016050?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2071&q=80',
                'link': '',
                'status': 'active',
                'order': 3
            }
        ]
        
        for data in sliders_data:
            Slider.objects.create(**data)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(sliders_data)} sample sliders')
        )
