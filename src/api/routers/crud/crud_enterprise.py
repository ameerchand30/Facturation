from sqlalchemy.orm import Session
from src.api.models.enterprise import Enterprise
from src.api.schemas.enterprise import EnterpriseCreate, EnterpriseUpdate
# to get one enterprise
def get_enterprise(db: Session, enterprise_id: int):
    return db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
# to show all enterprises
def get_enterprises(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Enterprise).offset(skip).limit(limit).all()

def create_enterprise(db: Session, enterprise: EnterpriseCreate):
    db_enterprise = enterprise
    db.add(db_enterprise)
    db.commit()
    db.refresh(db_enterprise)
    return db_enterprise

def update_enterprise(db: Session, enterprise_id: int, enterprise: EnterpriseUpdate):
    db.query(Enterprise).filter(Enterprise.id == enterprise_id).update(enterprise)
    db.commit()

def delete_enterprise(db: Session, enterprise_id: int):
    db.query(Enterprise).filter(Enterprise.id == enterprise_id).delete()
    db.commit()