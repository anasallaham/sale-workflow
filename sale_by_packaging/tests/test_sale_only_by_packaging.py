# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.exceptions import ValidationError
from odoo.tests import SavepointCase


class TestSaleProductByPackagingOnly(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.product = cls.env.ref("product.product_product_9")
        cls.packaging = cls.env["product.packaging"].create(
            {"name": "Test packaging", "product_id": cls.product.id, "qty": 5.0}
        )
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})

    def test_onchange_qty_is_pack_multiple(self):
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
            }
        )
        self.assertFalse(order_line._onchange_product_uom_qty())

        self.product.write({"sell_only_by_packaging": True})
        self.assertTrue(order_line._onchange_product_uom_qty())

        order_line.product_id_change()
        self.assertFalse(order_line._onchange_product_uom_qty())

        order_line.write({"product_uom_qty": 3.0})
        self.assertTrue(order_line._onchange_product_uom_qty())

        order_line.write({"product_uom_qty": self.packaging.qty * 2})
        self.assertFalse(order_line._onchange_product_uom_qty())

    def test_write_auto_fill_packaging(self):
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
            }
        )
        self.assertFalse(order_line.product_packaging)
        self.assertFalse(order_line.product_packaging_qty)

        order_line.write({"product_uom_qty": 3.0})
        self.assertFalse(order_line.product_packaging)
        self.assertFalse(order_line.product_packaging_qty)

        self.product.write({"sell_only_by_packaging": True})
        self.assertFalse(order_line.product_packaging)
        self.assertFalse(order_line.product_packaging_qty)

        order_line.write({"product_uom_qty": self.packaging.qty * 2})
        self.assertTrue(order_line.product_packaging)
        self.assertTrue(order_line.product_packaging_qty)
        self.assertEqual(order_line.product_packaging.name, "Test packaging")
        self.assertEqual(order_line.product_packaging_qty, 2)

        packaging_10 = self.env["product.packaging"].create(
            {"name": "Test packaging 10", "product_id": self.product.id, "qty": 15.0}
        )
        order_line.write({"product_uom_qty": packaging_10.qty * 2})
        self.assertEqual(order_line.product_packaging.name, "Test packaging 10")

        with self.assertRaises(ValidationError):
            order_line.write({"product_packaging": False})

    def test_create_auto_fill_packaging(self):
        # sell_only_by_packaging is default False
        order_line_1 = self.env["sale.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": self.packaging.qty * 2,
            }
        )
        self.assertFalse(order_line_1.product_packaging)
        self.assertFalse(order_line_1.product_packaging_qty)

        self.product.write({"sell_only_by_packaging": True})
        order_line_1 = self.env["sale.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": self.packaging.qty * 2,
            }
        )
        self.assertTrue(order_line_1.product_packaging)
        self.assertTrue(order_line_1.product_packaging_qty)
        self.assertEqual(order_line_1.product_packaging.name, "Test packaging")
        self.assertEqual(order_line_1.product_packaging_qty, 2)

        with self.assertRaises(ValidationError):
            self.env["sale.order.line"].create(
                {
                    "order_id": self.order.id,
                    "product_id": self.product.id,
                    "product_uom": self.product.uom_id.id,
                    "product_uom_qty": 2,
                }
            )
