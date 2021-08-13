import logging

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

_session = None

log = logging.getLogger(__name__)


def get_session(db_uri):
    assert db_uri
    global _session
    if not _session:
        # TODO remove passwords if present
        log.info("Connection to database: %s" % db_uri)
        engine = create_engine(db_uri)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        _session = Session()
    return _session


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    submitter_email = Column(String)
    submission_date = Column(DateTime)
    cracking_date = Column(DateTime)

    wordlist = Column(String)
    rule_set = Column(String)
    hashcathelper_version = Column(String)
    hashcat_version = Column(String)

    accounts = Column(Integer)
    cracked = Column(Integer)
    nonunique = Column(Integer)
    user_equals_password = Column(Integer)
    lm_hash_count = Column(Integer)
    empty_password = Column(Integer)
    average_password_length = Column(Float)
    largest_baseword_cluster = Column(Integer)


def submit(session,
           submitter_email,
           wordlist,
           rule_set,
           hashcat_version,
           data):
    from datetime import datetime as dt
    from hashcathelper._meta import __version__
    try:
        timestamp = data['meta']['timestamp']
        cracking_date = dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
    except (KeyError, ValueError):
        log.error("Failed to parse cracking date")
        cracking_date = None

    def get_value(item):
        # for values with percentage
        val = data['report'][item]
        if isinstance(val, list) and len(val) == 2:
            return val[0]
        return val

    largest_cluster = max(data['sensitive']['top10_basewords'].values())
    r = Report(
        submitter_email=submitter_email,
        submission_date=dt.now(),
        cracking_date=cracking_date,
        wordlist=wordlist,
        rule_set=rule_set,
        hashcathelper_version=__version__,
        hashcat_version=hashcat_version,
        accounts=data['report']['accounts'],
        cracked=get_value('cracked'),
        nonunique=get_value('nonunique'),
        user_equals_password=get_value('user_equals_password'),
        lm_hash_count=get_value('lm_hash_count'),
        empty_password=get_value('empty_password'),
        average_password_length=data['report']['average_password_length'],
        largest_baseword_cluster=largest_cluster,
    )

    session.add(r)
    session.commit()
    return r.id
