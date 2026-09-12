from django.contrib.auth.base_user import BaseUserManager

from .normalization import normalize_email, normalize_phone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email=None, telephone=None, password=None, **extra_fields):
        email = normalize_email(email)
        telephone = normalize_phone(telephone)
        if not email and not telephone:
            raise ValueError("Un email ou un téléphone est obligatoire.")
        user = self.model(email=email, telephone=telephone, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude={"password"}, validate_unique=False)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, telephone=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("statut", "actif")
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Un superutilisateur doit avoir is_staff et is_superuser à True.")
        return self.create_user(email=email, telephone=telephone, password=password, **extra_fields)
