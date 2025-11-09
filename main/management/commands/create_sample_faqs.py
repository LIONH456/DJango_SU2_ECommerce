"""
Management command to create sample FAQs for the ecommerce site
Run with: python manage.py create_sample_faqs
"""
from django.core.management.base import BaseCommand
from main.mongodb_utils import mongodb_manager


class Command(BaseCommand):
    help = 'Create sample FAQs for the ecommerce site'

    def handle(self, *args, **options):
        sample_faqs = [
            {
                'question': 'What is the store name?',
                'answer': 'Our store name is SU12-Ecommerce. We are a leading online marketplace offering a wide range of products including clothing, accessories, electronics, and more.',
                'category': 'general',
                'keywords': ['store name', 'company', 'brand', 'who are you'],
                'order': 1,
                'is_active': True
            },
            {
                'question': 'What products do you sell?',
                'answer': 'We sell a wide variety of products including shoes, shirts, clothes, bags, accessories, electronics, and much more. Browse our categories to see our full product range.',
                'category': 'products',
                'keywords': ['products', 'what do you sell', 'items', 'merchandise', 'shoes', 'shirts', 'clothes', 'bags'],
                'order': 2,
                'is_active': True
            },
            {
                'question': 'How do I place an order?',
                'answer': 'To place an order, simply browse our products, add items to your cart, and proceed to checkout. You will need to create an account or log in, provide your shipping address, and complete the payment.',
                'category': 'orders',
                'keywords': ['order', 'purchase', 'buy', 'checkout', 'how to order'],
                'order': 3,
                'is_active': True
            },
            {
                'question': 'What payment methods do you accept?',
                'answer': 'We accept various payment methods including credit cards, debit cards, PayPal, and Bakong (KHQR). All payments are processed securely.',
                'category': 'payment',
                'keywords': ['payment', 'pay', 'payment methods', 'credit card', 'paypal', 'bakong', 'khqr'],
                'order': 4,
                'is_active': True
            },
            {
                'question': 'How long does shipping take?',
                'answer': 'Shipping times vary depending on your location. Typically, orders are processed within 1-2 business days and delivered within 5-7 business days. Express shipping options are available for faster delivery.',
                'category': 'shipping',
                'keywords': ['shipping', 'delivery', 'how long', 'when will I receive', 'delivery time'],
                'order': 5,
                'is_active': True
            },
            {
                'question': 'Do you offer free shipping?',
                'answer': 'Yes, we offer free shipping on orders above a certain amount. Please check our shipping policy page for current promotions and free shipping thresholds.',
                'category': 'shipping',
                'keywords': ['free shipping', 'shipping cost', 'delivery fee'],
                'order': 6,
                'is_active': True
            },
            {
                'question': 'Can I return or exchange items?',
                'answer': 'Yes, we have a return and exchange policy. Items can be returned within 30 days of purchase if they are unused and in their original packaging. Please contact our support team for return authorization.',
                'category': 'returns',
                'keywords': ['return', 'exchange', 'refund', 'return policy'],
                'order': 7,
                'is_active': True
            },
            {
                'question': 'How do I track my order?',
                'answer': 'Once your order is shipped, you will receive a tracking number via email. You can use this tracking number on our website or the carrier\'s website to track your package.',
                'category': 'orders',
                'keywords': ['track', 'tracking', 'order status', 'where is my order'],
                'order': 8,
                'is_active': True
            },
            {
                'question': 'Do you ship internationally?',
                'answer': 'Currently, we ship to select countries. Please check our shipping policy or contact our support team to see if we deliver to your location.',
                'category': 'shipping',
                'keywords': ['international', 'overseas', 'abroad', 'other countries'],
                'order': 9,
                'is_active': True
            },
            {
                'question': 'How can I contact customer support?',
                'answer': 'You can contact our customer support team through email at support@su12ecommerce.com, or use the contact form on our website. Our support team is available Monday to Friday, 9 AM to 6 PM.',
                'category': 'support',
                'keywords': ['contact', 'support', 'help', 'customer service', 'email'],
                'order': 10,
                'is_active': True
            },
            {
                'question': 'Is my personal information secure?',
                'answer': 'Yes, we take your privacy and security seriously. All personal information is encrypted and stored securely. We never share your information with third parties without your consent.',
                'category': 'privacy',
                'keywords': ['privacy', 'security', 'personal information', 'data protection'],
                'order': 11,
                'is_active': True
            },
            {
                'question': 'Do you have a mobile app?',
                'answer': 'Currently, we have a responsive website that works great on mobile devices. We are working on a mobile app that will be available soon. Stay tuned for updates!',
                'category': 'general',
                'keywords': ['mobile app', 'app', 'mobile', 'smartphone'],
                'order': 12,
                'is_active': True
            },
            {
                'question': 'How do I create an account?',
                'answer': 'To create an account, click on the "Sign Up" or "Register" button on our website. You will need to provide your email address, username, and create a password. Registration is free and takes just a few minutes.',
                'category': 'account',
                'keywords': ['account', 'register', 'sign up', 'create account', 'registration'],
                'order': 13,
                'is_active': True
            },
            {
                'question': 'Can I change my order after placing it?',
                'answer': 'If you need to change your order, please contact our support team as soon as possible. We can modify or cancel orders that have not yet been processed or shipped.',
                'category': 'orders',
                'keywords': ['change order', 'modify order', 'cancel order', 'edit order'],
                'order': 14,
                'is_active': True
            },
            {
                'question': 'What sizes are available?',
                'answer': 'Product sizes vary by item. Each product page displays available sizes. If a size is out of stock, you can sign up to be notified when it becomes available again.',
                'category': 'products',
                'keywords': ['sizes', 'size chart', 'what sizes', 'available sizes'],
                'order': 15,
                'is_active': True
            }
        ]

        self.stdout.write('Creating sample FAQs...')
        
        created_count = 0
        for faq_data in sample_faqs:
            try:
                faq_id = mongodb_manager.create_faq(faq_data)
                if faq_id:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created FAQ: {faq_data["question"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'✗ Failed to create FAQ: {faq_data["question"]}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error creating FAQ "{faq_data["question"]}": {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} out of {len(sample_faqs)} FAQs!')
        )

