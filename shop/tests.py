import zoneinfo
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from shop.models import Product, Order, OrderItem, Payment


class TestDataBase(TestCase):
    fixtures = [
        "shop/fixtures/data.json"
    ]

    def setUp(self):
        self.user = User.objects.get(username='root')
        self.p = Product.objects.all().first()

    def test_user_exists(self):
        users = User.objects.all()
        users_number = users.count()
        user = users.first()
        self.assertEquals(users_number, 3)
        self.assertEquals(user.username, 'root')
        self.assertTrue(user.is_superuser)

    def test_user_check_password(self):
        self.assertTrue(self.user.check_password('1234'))

    def test_all_data(self):
        self.assertEquals(Product.objects.all().count(), 1)
        self.assertEquals(Order.objects.all().count(), 0)
        self.assertEquals(OrderItem.objects.all().count(), 0)
        self.assertEquals(Payment.objects.all().count(), 0)

    def find_cart_number(self):
        cart_number = Order.objects.filter(user=self.user,
                                           status=Order.STATUS_CART,
                                           ).count()
        return cart_number

    def test_function_get_cart(self):
        self.assertEqual(self.find_cart_number(), 0)

        Order.get_cart(self.user)
        self.assertEqual(self.find_cart_number(), 1)

        Order.get_cart(self.user)
        self.assertEqual(self.find_cart_number(), 1)

    def test_cart_older_7_days(self):
        cart = Order.get_cart(self.user)
        cart.creation_time = timezone.datetime(2000, 1, 1, tzinfo=zoneinfo.ZoneInfo('UTC'))
        cart.save()
        cart = Order.get_cart(self.user)
        self.assertEqual((timezone.now()-cart.creation_time).days, 0)

    def test_recalculate_order_amount_after_changing_orderitem(self):
        cart = Order.get_cart(self.user)
        self.assertEqual(cart.amount, Decimal(0))

        i = OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        i = OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=3)
        cart = Order.get_cart(self.user)
        self.assertEqual(cart.amount, Decimal(10))

        i.delete()
        cart = Order.get_cart(self.user)
        self.assertEqual(cart.amount, Decimal(4))

    def test_cart_status_changing_after_applying_make_order(self):
        cart = Order.get_cart(self.user)
        cart.make_order()
        self.assertEqual(cart.status, Order.STATUS_CART)

        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        cart.make_order()
        self.assertEqual(cart.status, Order.STATUS_WAITING_FOR_PAYMENT)

    def test_method_get_amount_of_unpaid_orders(self):
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

        cart.make_order()
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(4))

        cart.status = Order.STATUS_PAID
        cart.save()
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

        Order.objects.all().delete()
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

    def test_method_get_balance(self):
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(0))

        Payment.objects.create(user=self.user, amount=100)
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(100))

        Payment.objects.create(user=self.user, amount=-50)
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(50))

        Payment.objects.all().delete()
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(0))

    def test_auto_payment_after_apply_make_order_true(self):
        Payment.objects.create(user=self.user, amount=100)
        Order.objects.all().delete()
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        self.assertEqual(Payment.get_balance(self.user), Decimal(100))
        cart.make_order()
        self.assertEqual(Payment.get_balance(self.user), Decimal(96))

    def test_auto_payment_after_apply_make_order_false(self):
        Payment.objects.create(user=self.user, amount=100)
        Order.objects.all().delete()
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=100)
        self.assertEqual(Payment.get_balance(self.user), Decimal(100))
        cart.make_order()
        self.assertEqual(Payment.get_balance(self.user), Decimal(100))

    def test_auto_payment_after_add_required_payment(self):
        Payment.objects.create(user=self.user, amount=556)
        self.assertEqual(Payment.get_balance(self.user), Decimal(556))
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEquals(amount, Decimal(0))

    def test_auto_payment_for_earlier_order(self):
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=500)
        Payment.objects.create(user=self.user, amount=1000)
        self.assertEqual(Payment.get_balance(self.user), Decimal(1000))
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEquals(amount, Decimal(0))

    def test_auto_payment_for_all_order(self):
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=500)
        Payment.objects.create(user=self.user, amount=10000)
        self.assertEqual(Payment.get_balance(self.user), Decimal(10000))
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEquals(amount, Decimal(0))

