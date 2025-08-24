from django.core.management.base import BaseCommand
from main.mongodb_utils import mongodb_manager
import bcrypt

class Command(BaseCommand):
    help = 'Update all users passwords to "123"'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help='Confirm the password update')

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING('This will update ALL users passwords to "123". Use --confirm to proceed.')
            )
            return

        # Hash the password "123"
        password = "123".encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        hashed_password_str = hashed_password.decode('utf-8')

        # Get all users
        users = mongodb_manager.get_all_users()
        
        if not users:
            self.stdout.write(
                self.style.WARNING('No users found in the database.')
            )
            return

        updated_count = 0
        for user in users:
            try:
                # Update the password
                result = mongodb_manager.users_collection.update_one(
                    {'_id': user['_id']},
                    {'$set': {'password': hashed_password_str}}
                )
                if result.modified_count > 0:
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated password for user: {user.get("username", "Unknown")}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating user {user.get("username", "Unknown")}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} out of {len(users)} users.')
        )







