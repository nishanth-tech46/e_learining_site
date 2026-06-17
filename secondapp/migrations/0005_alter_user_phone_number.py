# Generated migration for phone_number field changes

from django.db import migrations, models
import time


def populate_phone_numbers(apps, schema_editor):
    """Populate phone_number for existing users that don't have one"""
    User = apps.get_model('secondapp', 'User')
    used_numbers = set()
    
    for user in User.objects.all():
        if not user.phone_number:
            # Generate a unique placeholder phone number
            # Use timestamp + user ID to ensure uniqueness
            timestamp = int(time.time() * 1000)
            phone_num = f"{timestamp}{user.id}"[-15:]  # Last 15 digits
            
            # Ensure uniqueness
            while phone_num in used_numbers:
                timestamp += 1
                phone_num = f"{timestamp}{user.id}"[-15:]
            
            used_numbers.add(phone_num)
            user.phone_number = phone_num
            user.save()
        else:
            # Check for duplicates and fix them
            if user.phone_number in used_numbers:
                timestamp = int(time.time() * 1000)
                phone_num = f"{timestamp}{user.id}"[-15:]
                while phone_num in used_numbers:
                    timestamp += 1
                    phone_num = f"{timestamp}{user.id}"[-15:]
                used_numbers.add(phone_num)
                user.phone_number = phone_num
                user.save()
            else:
                used_numbers.add(user.phone_number)


class Migration(migrations.Migration):

    dependencies = [
        ('secondapp', '0004_user_account_locked_user_failed_login_attempts_and_more'),
    ]

    operations = [
        # First, populate phone_number for existing users and ensure uniqueness
        migrations.RunPython(populate_phone_numbers, migrations.RunPython.noop),
        
        # Then make the field not nullable and unique
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=False, max_length=15, null=False, unique=True),
        ),
    ]
