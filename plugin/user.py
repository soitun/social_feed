import json
import sqlalchemy as sa
import skygear
from skygear import (
    op,
)
from skygear.utils import db

from .options import (
    DB_NAME,
    SOCIAL_FEED_FANOUT_POLICY,
)


def should_record_be_indexed(db_name, default_fanout_policy,
                             db, user_id, relation):
    get_user_fanout_policy_sql = sa.text('''
        SELECT social_feed_fanout_policy as fanout_policy
        FROM {db_name}.user
        WHERE _id=:user_id
    '''.format(db_name=db_name))
    user_fanout_policy = db.execute(
        get_user_fanout_policy_sql,
        user_id=user_id
    ).scalar()

    if user_fanout_policy is not None:
        if relation in user_fanout_policy:
            return user_fanout_policy[relation]
        return False

    if relation in default_fanout_policy:
        return default_fanout_policy[relation]

    return False


def register_set_enable_fanout_to_relation():
    @op('social_feed:setEnableFanoutToRelation', user_required=True)
    def set_enable_fanout_to_relation(relation, enable):
        with db.conn() as conn:
            my_user_id = skygear.utils.context.current_user_id()

            get_user_fanout_policy_sql = sa.text('''
                SELECT social_feed_fanout_policy as fanout_policy
                FROM {db_name}.user
                WHERE _id=:user_id
            '''.format(db_name=DB_NAME))
            fanout_policy = conn.execute(
                get_user_fanout_policy_sql,
                user_id=my_user_id
            ).scalar() or {}
            fanout_policy[relation] = enable

            update_user_fanout_policy_sql = sa.text('''
                UPDATE {db_name}.user
                SET social_feed_fanout_policy_is_dirty = TRUE,
                social_feed_fanout_policy = :fanout_policy ::jsonb
                WHERE _id = :user_id
            '''.format(db_name=DB_NAME))
            conn.execute(
                update_user_fanout_policy_sql,
                fanout_policy=json.dumps(fanout_policy),
                user_id=my_user_id
            )


def register_get_user_fanout_policy():
    @op('social_feed:getUserFanoutPolicy', user_required=True)
    def get_user_fanout_policy():
        with db.conn() as conn:
            my_user_id = skygear.utils.context.current_user_id()
            get_user_fanout_policy_sql = sa.text('''
                SELECT social_feed_fanout_policy as fanout_policy
                FROM {db_name}.user
                WHERE _id=:user_id
            '''.format(db_name=DB_NAME))
            fanout_policy = conn.execute(
                get_user_fanout_policy_sql,
                user_id=my_user_id
            ).scalar() or SOCIAL_FEED_FANOUT_POLICY

        return {
            'fanout_policy': fanout_policy,
        }
