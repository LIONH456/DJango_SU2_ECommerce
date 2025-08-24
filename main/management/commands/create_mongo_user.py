from django.core.management.base import BaseCommand
from main.mongodb_utils import mongodb_manager

class Command(BaseCommand):
    help = 'Create a new user in MongoDB'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the new user')
        parser.add_argument('email', type=str, help='Email for the new user')
        parser.add_argument('password', type=str, help='Password for the new user')
        parser.add_argument('--first-name', type=str, default='', help='First name')
        parser.add_argument('--last-name', type=str, default='', help='Last name')
        parser.add_argument('--phone', type=str, default='', help='Phone number')
        parser.add_argument('--staff', action='store_true', help='Make user staff')
        parser.add_argument('--superuser', action='store_true', help='Make user superuser')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        # Check if user already exists
        if mongodb_manager.get_user_by_username(username):
            self.stdout.write(
                self.style.ERROR(f'User with username "{username}" already exists!')
            )
            return
        
        if mongodb_manager.get_user_by_email(email):
            self.stdout.write(
                self.style.ERROR(f'User with email "{email}" already exists!')
            )
            return
        
        # Create user data
        user_data = {
            'username': username,
            'email': email,
            'password': password,  # Will be hashed automatically
            'first_name': options['first_name'],
            'last_name': options['last_name'],
            'phone': options['phone'],
            'is_active': True,
            'is_staff': options['staff'],
            'is_superuser': options['superuser']
        }
        
        try:
            user_id = mongodb_manager.create_user(user_data)
            if user_id:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created user "{username}" with ID: {user_id}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to create user')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {str(e)}')
            )
