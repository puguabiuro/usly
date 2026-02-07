from logger import get_logger, log_exception

log = get_logger(__name__)

log.debug("To jest DEBUG")
log.info("To jest INFO")
log.warning("To jest WARNING")
log.error("To jest ERROR")

log.info("login=aga password=SuperTajne123 token: abcdef")
log.info('{"authorization":"Bearer XYZ","api_key":"k123"}')
from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
print(inspector.get_table_names())
