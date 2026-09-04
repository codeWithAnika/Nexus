from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.analysis import Analysis
from app.models.case import Case
from app.models.entity import Entity
from app.models.entity_identifier import EntityIdentifier
from app.models.evidence import Evidence
from app.models.relationship import Relationship


class EntityServiceError(Exception):
    pass


class EntityNotFoundError(EntityServiceError):
    pass


class EntityCaseNotFoundError(EntityServiceError):
    pass


class EntityIdentifierNotFoundError(EntityServiceError):
    pass


class EntityIdentifierEvidenceNotFoundError(EntityServiceError):
    pass


class EntityHasDependentsError(EntityServiceError):
    pass


class EntityDatabaseError(EntityServiceError):
    pass


def create_entity(db: Session, entity_data: dict) -> Entity:
    try:
        if db.scalar(select(Case.id).where(Case.id == entity_data["case_id"])) is None:
            raise EntityCaseNotFoundError
        entity = Entity(**entity_data)
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity
    except EntityCaseNotFoundError:
        db.rollback()
        raise
    except (IntegrityError, SQLAlchemyError) as exc:
        db.rollback()
        raise EntityDatabaseError from exc


def get_entity(db: Session, entity_id: int) -> Entity:
    try:
        entity = db.get(Entity, entity_id)
    except SQLAlchemyError as exc:
        raise EntityDatabaseError from exc
    if entity is None:
        raise EntityNotFoundError
    return entity


def list_entities(db: Session, *, case_id: int | None, entity_type, normalized_name: str | None, skip: int, limit: int) -> tuple[Sequence[Entity], int]:
    try:
        filters = []
        if case_id is not None:
            filters.append(Entity.case_id == case_id)
        if entity_type is not None:
            filters.append(Entity.entity_type == entity_type)
        if normalized_name is not None:
            filters.append(Entity.normalized_name == normalized_name)
        items = db.scalars(select(Entity).where(*filters).order_by(Entity.created_at.desc(), Entity.id.desc()).offset(skip).limit(limit)).all()
        total = db.scalar(select(func.count(Entity.id)).where(*filters))
        return items, int(total or 0)
    except SQLAlchemyError as exc:
        raise EntityDatabaseError from exc


def update_entity(db: Session, entity_id: int, updates: dict) -> Entity:
    entity = get_entity(db, entity_id)
    try:
        for field, value in updates.items():
            setattr(entity, field, value)
        db.commit()
        db.refresh(entity)
        return entity
    except SQLAlchemyError as exc:
        db.rollback()
        raise EntityDatabaseError from exc


def delete_entity(db: Session, entity_id: int) -> None:
    entity = get_entity(db, entity_id)
    try:
        # Oracle does not support SELECT EXISTS (SELECT * ...) AS anon FROM DUAL.
        # Use COUNT-based checks per table — valid on Oracle, PostgreSQL, and SQLite.
        dependent = (
            (db.scalar(select(func.count(EntityIdentifier.id)).where(EntityIdentifier.entity_id == entity_id)) or 0) > 0
            or (db.scalar(select(func.count(Relationship.id)).where(Relationship.source_entity_id == entity_id)) or 0) > 0
            or (db.scalar(select(func.count(Relationship.id)).where(Relationship.target_entity_id == entity_id)) or 0) > 0
            or (db.scalar(select(func.count(Analysis.id)).where(Analysis.entity_id == entity_id)) or 0) > 0
            or (db.scalar(select(func.count(Alert.id)).where(Alert.entity_id == entity_id)) or 0) > 0
        )
        if dependent:
            raise EntityHasDependentsError
        db.delete(entity)
        db.commit()
    except EntityHasDependentsError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise EntityHasDependentsError from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise EntityDatabaseError from exc


def create_identifier(db: Session, entity_id: int, identifier_data: dict) -> EntityIdentifier:
    entity = get_entity(db, entity_id)
    try:
        source_evidence_id = identifier_data.get("source_evidence_id")
        if source_evidence_id is not None and db.scalar(
            select(Evidence.id).where(Evidence.id == source_evidence_id, Evidence.case_id == entity.case_id)
        ) is None:
            raise EntityIdentifierEvidenceNotFoundError
        identifier = EntityIdentifier(entity_id=entity_id, **identifier_data)
        db.add(identifier)
        db.commit()
        db.refresh(identifier)
        return identifier
    except EntityIdentifierEvidenceNotFoundError:
        db.rollback()
        raise
    except (IntegrityError, SQLAlchemyError) as exc:
        db.rollback()
        raise EntityDatabaseError from exc


def list_identifiers(db: Session, entity_id: int) -> Sequence[EntityIdentifier]:
    get_entity(db, entity_id)
    try:
        return db.scalars(select(EntityIdentifier).where(EntityIdentifier.entity_id == entity_id).order_by(EntityIdentifier.id)).all()
    except SQLAlchemyError as exc:
        raise EntityDatabaseError from exc


def get_identifier(db: Session, entity_id: int, identifier_id: int) -> EntityIdentifier:
    get_entity(db, entity_id)
    try:
        identifier = db.scalar(select(EntityIdentifier).where(EntityIdentifier.id == identifier_id, EntityIdentifier.entity_id == entity_id))
    except SQLAlchemyError as exc:
        raise EntityDatabaseError from exc
    if identifier is None:
        raise EntityIdentifierNotFoundError
    return identifier


def update_identifier(db: Session, entity_id: int, identifier_id: int, updates: dict) -> EntityIdentifier:
    identifier = get_identifier(db, entity_id, identifier_id)
    entity = get_entity(db, entity_id)
    try:
        source_evidence_id = updates.get("source_evidence_id", identifier.source_evidence_id)
        if source_evidence_id is not None and db.scalar(
            select(Evidence.id).where(Evidence.id == source_evidence_id, Evidence.case_id == entity.case_id)
        ) is None:
            raise EntityIdentifierEvidenceNotFoundError
        for field, value in updates.items():
            setattr(identifier, field, value)
        db.commit()
        db.refresh(identifier)
        return identifier
    except EntityIdentifierEvidenceNotFoundError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise EntityDatabaseError from exc


def delete_identifier(db: Session, entity_id: int, identifier_id: int) -> None:
    identifier = get_identifier(db, entity_id, identifier_id)
    try:
        db.delete(identifier)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise EntityDatabaseError from exc