from . import db


class Product(db.Model):
    __tablename__ = 'models'
    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String(128), index=True)
    model_name = db.Column(db.String(255), unique=True, index=True)
    priority = db.Column(db.Integer)
    product_type = db.Column(db.String(32))

    def __repr__(self):
        return self.manufacturer + self.model_name