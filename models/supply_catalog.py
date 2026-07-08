from models import db


class SupplyCatalog(db.Model):
    __tablename__ = 'supply_catalog'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(50), default='pcs')

    def __repr__(self):
        return f'{self.category} - {self.item_name}'
