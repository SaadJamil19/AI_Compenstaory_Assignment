"""Database engine, session, and seed data."""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models so tables are registered
    from models import activity, comment, customer, notification, ticket, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _lightweight_sqlite_upgrade()
    seed_if_empty()


def _lightweight_sqlite_upgrade():
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    with engine.begin() as conn:
        if "users" in tables:
            cols = {c["name"] for c in inspector.get_columns("users")}
            if "is_active" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL"))
            if "created_at" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME"))
                conn.execute(text("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
        if "tickets" in tables:
            cols = {c["name"] for c in inspector.get_columns("tickets")}
            if "ai_suggested_reply" not in cols:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN ai_suggested_reply TEXT"))


def seed_if_empty():
    from auth.password import hash_password
    from models.activity import TicketActivity
    from models.comment import Comment
    from models.customer import Customer
    from models.ticket import Ticket
    from models.user import User

    db = SessionLocal()
    try:
        if db.query(User).first():
            return

        manager = User(
            email="admin@test.com",
            hashed_password=hash_password("admin123"),
            full_name="Admin Manager",
            role="manager",
        )
        agent = User(
            email="agent@test.com",
            hashed_password=hash_password("agent123"),
            full_name="Support Agent",
            role="agent",
        )
        db.add_all([manager, agent])
        db.commit()
        db.refresh(manager)
        db.refresh(agent)

        customers_data = [
            {"full_name": "John Smith", "email": "john@acme.com", "phone": "+1-555-0101", "company": "Acme Corp"},
            {"full_name": "Sarah Lee", "email": "sarah@tech.io", "phone": "+1-555-0102", "company": "Tech.io"},
            {"full_name": "Mike Johnson", "email": "mike@shop.com", "phone": "+1-555-0103", "company": "ShopMart"},
            {"full_name": "Emily Davis", "email": "emily@cloud.net", "phone": "+1-555-0104", "company": "CloudNet"},
        ]
        customers = [Customer(**c) for c in customers_data]
        db.add_all(customers)
        db.commit()
        for c in customers:
            db.refresh(c)

        tickets_data = [
            {
                "title": "Cannot access billing portal",
                "description": "I am unable to log into the billing section. Getting error 403.",
                "status": "open",
                "priority": "high",
                "category": "billing",
                "sentiment": "frustrated",
                "customer_id": customers[0].id,
                "assigned_agent_id": agent.id,
            },
            {
                "title": "API timeout on production",
                "description": "Our API calls are timing out after 30 seconds since yesterday.",
                "status": "in_progress",
                "priority": "critical",
                "category": "technical",
                "sentiment": "negative",
                "customer_id": customers[1].id,
                "assigned_agent_id": agent.id,
            },
            {
                "title": "Update account email address",
                "description": "Please change my account email from old@email.com to new@email.com",
                "status": "open",
                "priority": "low",
                "category": "account",
                "sentiment": "neutral",
                "customer_id": customers[2].id,
            },
            {
                "title": "Shipment delayed - order #4521",
                "description": "My order was supposed to arrive last week but tracking shows no updates.",
                "status": "in_progress",
                "priority": "medium",
                "category": "shipping",
                "sentiment": "negative",
                "customer_id": customers[2].id,
                "assigned_agent_id": agent.id,
            },
            {
                "title": "Thank you for quick support",
                "description": "The team resolved my issue quickly. Very happy with the service!",
                "status": "resolved",
                "priority": "low",
                "category": "general",
                "sentiment": "positive",
                "customer_id": customers[3].id,
                "assigned_agent_id": agent.id,
                "ai_summary": "Customer expressed satisfaction with quick resolution of their issue.",
            },
            {
                "title": "General inquiry about pricing",
                "description": "Can you send me information about enterprise pricing plans?",
                "status": "closed",
                "priority": "low",
                "category": "general",
                "sentiment": "neutral",
                "customer_id": customers[0].id,
            },
        ]
        tickets = [Ticket(**t) for t in tickets_data]
        db.add_all(tickets)
        db.commit()
        for t in tickets:
            db.refresh(t)

        comments_data = [
            {"ticket_id": tickets[1].id, "user_id": agent.id, "body": "Investigating API gateway logs."},
            {"ticket_id": tickets[1].id, "user_id": manager.id, "body": "Escalated to infrastructure team."},
            {"ticket_id": tickets[3].id, "user_id": agent.id, "body": "Contacted shipping carrier for update."},
        ]
        db.add_all([Comment(**c) for c in comments_data])
        db.add_all(
            [
                TicketActivity(ticket_id=t.id, user_id=manager.id, action_type="created", message="Seed ticket created.")
                for t in tickets
            ]
        )
        db.add(TicketActivity(ticket_id=tickets[1].id, user_id=agent.id, action_type="comment", message="Investigating API gateway logs."))
        db.add(TicketActivity(ticket_id=tickets[1].id, user_id=manager.id, action_type="comment", message="Escalated to infrastructure team."))
        db.add(TicketActivity(ticket_id=tickets[3].id, user_id=agent.id, action_type="comment", message="Contacted shipping carrier for update."))
        db.commit()
    finally:
        db.close()
