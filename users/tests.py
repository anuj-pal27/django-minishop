"""1C-6 tests for users: register, JWT login, /me, profile permissions (6 tests)."""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from config.factories import PASSWORD, make_staff, make_user

User = get_user_model()


class AuthTests(APITestCase):                       # APITestCase = TestCase + self.client is an APIClient
    def setUp(self):                                # runs before EACH test (each test gets a clean DB)
        cache.clear()                               # reset throttle counters (they live in the cache)

    def test_register_creates_user_with_hashed_password(self):
        data = {"email": "new@example.com", "password": PASSWORD}
        res = self.client.post(reverse("users:register"), data)       # reverse() = URL from its name

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", res.data)                          # write_only: never sent back
        user = User.objects.get(email="new@example.com")
        self.assertNotEqual(user.password, PASSWORD)                    # stored hashed, not plain text
        self.assertTrue(user.check_password(PASSWORD))                  # but the password still works

    def test_register_rejects_weak_password(self):
        res = self.client.post(reverse("users:register"), {"email": "weak@example.com", "password": "123"})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", res.data)                             # error is on the password field
        self.assertFalse(User.objects.filter(email="weak@example.com").exists())

    def test_login_returns_access_and_refresh_tokens(self):
        user = make_user()
        res = self.client.post(reverse("users:token-obtain"), {"email": user.email, "password": PASSWORD})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_login_with_wrong_password_returns_401(self):
        user = make_user()
        res = self.client.post(reverse("users:token-obtain"), {"email": user.email, "password": "wrong"})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_needs_a_valid_token(self):
        user = make_user()
        url = reverse("users:me")

        self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)  # no token

        login = self.client.post(reverse("users:token-obtain"), {"email": user.email, "password": PASSWORD})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")    # real JWT header
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], user.email)


class UserDetailPermissionTests(APITestCase):
    def test_only_self_or_staff_can_view_a_profile(self):
        me, other, staff = make_user(), make_user(), make_staff()
        url = reverse("users:user-detail", args=[other.pk])

        self.client.force_authenticate(me)          # skip login: "pretend this user sent the request"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(staff)       # switch user
        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
