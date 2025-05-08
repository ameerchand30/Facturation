from sqlalchemy import Column, Integer, String, Boolean, Table, ForeignKey, Enum, event
import enum
from sqlalchemy.orm import relationship
from src.database import Base



class UserType(str, enum.Enum):
    CLIENT = "client"
    ENTERPRISE = "enterprise"
# User-Role Association Table
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id')),
    extend_existing=True
)

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    users = relationship("User", secondary=user_roles, back_populates="roles")

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    picture = Column(String, nullable=True)
    auth_provider = Column(String)
    provider_user_id = Column(String)
    user_type = Column(Enum(UserType))
    is_active = Column(Boolean, default=True)

    
    # Add the roles relationship
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    # One-to-One relationship with profiles
    enterprise_profile = relationship("EnterpriseProfile", back_populates="user", uselist=False)
    client_profile = relationship("ClientProfile", back_populates="user", uselist=False)

class ClientProfile(Base):
    __tablename__ = "client_profiles"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    phone = Column(String)
    address = Column(String)
    preferred_payment = Column(String)
    
    user = relationship("User", back_populates="client_profile")

class EnterpriseProfile(Base):
    __tablename__ = "enterprise_profiles"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    company_name = Column(String)
    registration_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    city = Column(String, nullable=True)
    logo = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    website = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
     # Relationship with User
    user = relationship("User", back_populates="enterprise_profile")

    # Enterprise-specific relationships
    clients = relationship("Clients", back_populates="enterprise")
    enterprises = relationship("Enterprise", back_populates="enterprise_profile")
    invoices = relationship("Invoice", back_populates="enterprise_profile")
    products = relationship("ProductModel", back_populates="enterprise_profile")

@event.listens_for(User, 'after_insert')
def create_enterprise_profile(mapper, connection, user):
    if user.user_type == UserType.ENTERPRISE:
        # Create enterprise profile with default values
        enterprise_profile = {
            'user_id': user.id,
            'company_name': f"{user.name}'s Company",  # Default company name
            'email': user.email,  # Use user's email
            'logo': user.picture,  # Use user's picture if available
            'registration_number': None,
            'address': None,
            'state': None,
            'postal_code': None,
            'city': None,
            'notes': None,
            'website': None,
            'phone': None,
            'business_type': None,
            'tax_id': None
        }
        
        connection.execute(
            EnterpriseProfile.__table__.insert(),
            [enterprise_profile]
        )