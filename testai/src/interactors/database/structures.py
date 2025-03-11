

from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    def __repr__(self):
        ent = []
        for col in {*self.__table__.columns}:
            ent.append("{0}={1}".format(col.key, getattr(self, col.key)))
        return "<{0}(".format(self.__class__.__name__) + ", ".join(ent) + ")>"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger(), unique=True)

    mental: Mapped["Mental"] = relationship(lazy="noload", viewonly=True)
    assisstants: Mapped[list["Assisstant"]] = relationship(lazy="noload", viewonly=True)


class Assisstant(Base):
    __tablename__ = "assistants"
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    openai_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    user: Mapped[User] = relationship(foreign_keys=user_id, lazy='noload')


class Mental(Base):
    __tablename__ = "mental_data"
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    user_id: Mapped[int] = mapped_column(unique=True)

    temperament: Mapped[str]
    profession: Mapped[str]

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    user: Mapped[User] = relationship(foreign_keys=user_id, lazy='noload')
