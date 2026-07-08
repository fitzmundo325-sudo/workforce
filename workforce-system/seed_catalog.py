from app import create_app
from models import db
from models.supply_catalog import SupplyCatalog
from catalog_data import CATALOG

app = create_app()
with app.app_context():
    if SupplyCatalog.query.first():
        print('Catalog already seeded. Skipping.')
    else:
        for category, item_name, unit in CATALOG:
            db.session.add(SupplyCatalog(category=category, item_name=item_name, unit=unit))
        db.session.commit()
        print(f'Seeded {len(CATALOG)} items into supply catalog.')
