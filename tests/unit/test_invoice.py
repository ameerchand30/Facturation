import pytest
from src.api.models.invoice import Invoice, InvoiceItem

class TestInvoice:
    def test_create_invoice(self, client, test_enterprise, test_client, test_product):
        """Test invoice creation endpoint"""
        invoice_data = {
            "client_id": test_client.id,
            "enterprise_id": test_enterprise.id,
            "items": [{
                "product_id": test_product.id,
                "quantity": 2,
                "unit_price": test_product.price
            }]
        }
        
        response = client.post("/invoice/create", json=invoice_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["client_id"] == test_client.id
        assert data["enterprise_id"] == test_enterprise.id

    def test_get_invoice(self, client, db_session, test_enterprise, test_client):
        """Test get invoice endpoint"""
        invoice = Invoice(
            client_id=test_client.id,
            enterprise_id=test_enterprise.id,
            total_ht=200.00,
            total_ttc=240.00
        )
        db_session.add(invoice)
        db_session.commit()

        response = client.get(f"/invoice/{invoice.id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == invoice.id