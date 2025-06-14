from flask_login import UserMixin
from sqlalchemy import create_engine, MetaData, Table, text, select,String, Boolean,LargeBinary,ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase,Session,Relationship
import pyotp

class Auth:
    def __init__(self, connectionString):
        self.engine = create_engine(connectionString,pool_size=20, max_overflow=0)
        metadata = MetaData()
        self.users = Table("usuarios", metadata, autoload_with=self.engine)

    def get_user(self, email):
        with Session(self.engine) as session:
            stmt = select(User).where(User.email == email)
            return session.scalars(stmt).one()

    def get_user_by_id(self, user_id):
        with Session(self.engine) as session:
            stmt = select(User).where(User.id == user_id)
            return session.scalars(stmt).one()

    def get_tenant(self, user_id):
        with Session(self.engine) as session:
            stmt = select(User).join(User.company).where(User.id == user_id)
            user = session.scalars(stmt).first()
            if (user != None):
                return user.company.tenant
        return ""

class Base(DeclarativeBase):
    pass

class Company(Base):
    __tablename__ = "empresas"
    id: Mapped[int] = mapped_column("codemp_emp", primary_key = True)
    name: Mapped[str] = mapped_column("nomemp_emp", String(70))
    nit: Mapped[str] = mapped_column("nit_emp", String(15))
    nname: Mapped[str] = mapped_column("nickname_emp", String(45))
    tenant: Mapped[str] = mapped_column("basedd_emp", String(45))

#    def check_idempr(self, id):
#        return self.id == id        

    def check_idempr(self, id, session):
    # Busca en la base de datos si el ID coincide
        return session.query(Company).filter(Company.id == id).first()
        
class User(Base, UserMixin):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column("cod_usu", primary_key = True)
    name: Mapped[str] = mapped_column("nom_usu", String(30))
    lastname: Mapped[str] = mapped_column("ape_usu", String(30))
    password: Mapped[str] = mapped_column("passwd_usu", String(50))
    email: Mapped[str] = mapped_column("email_usu", String(40))
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean)
    secret_key: Mapped[str] = mapped_column("secret_key", String(32))
    avatar: Mapped[bytes] = mapped_column("avatar_usu", LargeBinary)
    company_id: Mapped[int] = mapped_column("empr_usu", ForeignKey("empresas.codemp_emp"))
    company = Relationship("Company")

    def check_password(self, password):
        return self.password == password

    def check_2FA(self, token):
        totp = pyotp.TOTP(self.secret_key)
        return totp.verify(token)

