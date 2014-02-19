from ckan import new_authz, model
from ckan.common import _
from sqlalchemy.sql.expression import or_


def _only_registered_user():
    if not new_authz.auth_is_registered_user():
        return {'success': False, 'msg': _('User is not logged in')}
    return {'success': True}


def member_request_create(context, data_dict):
    """ Create request access check """
    if not new_authz.auth_is_registered_user():
        return {'success': False, 'msg': _('User is not logged in')}

    organization_id = None if not data_dict else data_dict.get('organization_id', None)

    if organization_id:
        user = model.User.get(context['user'])

        query = model.Session.query(model.Member).filter(or_(model.Member.state == 'active', model.Member.state == 'pending')) \
            .filter(model.Member.table_name == 'user').filter(model.Member.table_id == user.id).filter(model.Member.group_id == organization_id)

        if query.count() > 0:
            return {'success': False, 'msg': _('User has already request or active membership')}

    return {'success': True}


def member_request_show(context, data_dict):
    """ Show request access check """
    return _only_registered_user()


def member_request_list(context, data_dict):
    """ List request access check """
    return _only_registered_user()


def member_request_process(context, data_dict):
    """ Approve or reject access check """

    if new_authz.is_sysadmin(context['user']):
        return {'success': True}

    user = model.User.get(context['user'])
    member = model.Member.get(data_dict.get("member"))
    if not user or not member:
        return {'success': False}

    query = model.Session.query(model.Member).filter(model.Member.state == 'active').filter(model.Member.table_name == 'user') \
        .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == user.id).filter(model.Member.group_id == member.group_id)

    return {'success': query.count() > 0}
