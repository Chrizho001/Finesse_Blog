from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email,  first_name, last_name, username, password, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not first_name:
            raise ValueError("The first name field must be set")
        if not last_name:
            raise ValueError("The last name field must be set")
        if not username:
            raise ValueError("The username field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email,  first_name, last_name, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)


        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self.create_user(email, first_name, last_name, username, password, **extra_fields)
        user.save(using=self._db)
        return user
