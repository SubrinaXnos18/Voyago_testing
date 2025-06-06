from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Package, Booking, Diary, Contact


class VoyagoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            password='adminpass123',
            email='admin@example.com',
            is_staff=True,
            is_superuser=True
        )
        self.package = Package.objects.create(
            name='Test Package',
            destination='Test Destination',
            description='A test package',
            price=100.00,
            days=5,
        )

    # Model Tests
    def test_package_model_str(self):
        self.assertEqual(str(self.package), 'Test Package')

    def test_booking_model_str(self):
        booking = Booking.objects.create(user=self.user, package=self.package)
        self.assertEqual(str(booking), 'testuser - Test Package')
    
    def test_diary_model_str(self):
        diary = Diary.objects.create(user=self.user, text='Test diary entry')
        self.assertTrue(str(diary).startswith("testuser's Entry -"))

    def test_contact_model_str(self):
        contact = Contact.objects.create(
            name='Test Contact',
            email='test@example.com',
            contact_number='1234567890',
            comments='Test comment'
        )
        self.assertTrue(str(contact).startswith('Contact from Test Contact -'))


    # View Tests
    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/index.html')

    def test_bookings_view(self):
        response = self.client.get(reverse('bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/bookings.html')
        self.assertContains(response, self.package.name)

    def test_payment_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('payment', args=[self.package.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/payment.html')

    def test_payment_view_unauthenticated(self):
        response = self.client.get(reverse('payment', args=[self.package.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_payment_post(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('payment', args=[self.package.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/thank_you.html')
        self.assertTrue(Booking.objects.filter(user=self.user, package=self.package).exists())

    def test_my_diary_view(self):
        response = self.client.get(reverse('my_diary'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/my_diary.html')

    def test_my_diary_post_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('my_diary'), {'text': 'New diary entry'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Diary.objects.filter(user=self.user, text='New diary entry').exists())

    def test_my_diary_post_unauthenticated(self):
        response = self.client.post(reverse('my_diary'), {'text': 'New diary entry'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_admin_panel_view(self):
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/admin_panel.html')

    def test_admin_panel_view_non_admin(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 302)
        print(f"Redirect URL: {response.url}")
        self.assertTrue(response.url.startswith('/admin/login/'))


    def test_add_package(self):
        self.client.login(username='adminuser', password='adminpass123')
        form_data = {
            'name': 'New Package',
            'destination': 'New Destination',
            'description': 'A new package',
            'price': '200.00',
            'days': '7',
        }
        response = self.client.post(reverse('add_package'), form_data)
        if response.status_code != 302:
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
            if response.context is not None and 'form' in response.context:
                print(f"Add Package Form Errors: {response.context['form'].errors}")
            else:
                print("No form in response context. Possible redirect or authentication issue.")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Package.objects.filter(name='New Package').exists())

    def test_edit_package(self):
        self.client.login(username='adminuser', password='adminpass123')
        form_data = {
            'name': 'Updated Package',
            'destination': self.package.destination,
            'description': self.package.description,
            'price': '100.00',
            'days': '5',
        }
        response = self.client.post(reverse('edit_package', args=[self.package.id]), form_data)
        if response.status_code != 302:
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
            if response.context is not None and 'form' in response.context:
                print(f"Edit Package Form Errors: {response.context['form'].errors}")
            else:
                print("No form in response context. Possible redirect or authentication issue.")
        self.assertEqual(response.status_code, 302)
        self.package.refresh_from_db()
        self.assertEqual(self.package.name, 'Updated Package')

    def test_delete_package(self):
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('delete_package', args=[self.package.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Package.objects.filter(id=self.package.id).exists())


 def test_contact_us_view(self):
        response = self.client.get(reverse('contact_us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/contact_us.html')

    def test_contact_us_post(self):
        form_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'contact_number': '1234567890',
            'comments': 'Test comment'
        }
        response = self.client.post(reverse('contact_us'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Contact.objects.filter(email='john@example.com').exists())


    def test_login_view(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('bookings')))

 def test_register_view(self):
        form_data = {
            'username': 'newuser',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        response = self.client.post(reverse('register'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

 def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('index')))






    # Integration Test: User Journey
    def test_user_journey(self):
        # Register
        self.client.post(reverse('register'), {
            'username': 'journeyuser',
            'password1': 'journeypass123',
            'password2': 'journeypass123'
        })
        # Login
        self.client.post(reverse('login'), {
            'username': 'journeyuser',
            'password': 'journeypass123'
        })
        # Book a package
        response = self.client.post(reverse('payment', args=[self.package.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/thank_you.html')
        # Post to diary
        response = self.client.post(reverse('my_diary'), {'text': 'My travel story'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Diary.objects.filter(text='My travel story').exists())
        # Contact form
        response = self.client.post(reverse('contact_us'), {
            'name': 'Journey User',
            'email': 'journey@example.com',
            'contact_number': '1234567890',
            'comments': 'Great service'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Contact.objects.filter(email='journey@example.com').exists())
