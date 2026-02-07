from db.database import SessionLocal
from models import AuditLog

db = SessionLocal()

logs = (
    db.query(AuditLog)
    .order_by(AuditLog.created_at.desc())
    .limit(10)
    .all()
)

for log in logs:
    print(log.id, log.action, log.user_id, log.details, log.created_at)

db.close()
