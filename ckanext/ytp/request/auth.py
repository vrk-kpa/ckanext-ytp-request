from ckan import new_authz
from ckan.common import _


def member_request_create(context, data_dict):
    if not new_authz.auth_is_registered_user():
        return {'success': False, 'msg': _('User is not logged in')}
    return {'success': True}


def member_request_show(context, data_dict):
    return {'success': True}


def member_request_list(context, data_dict):
    return {'success': True}


def member_request_process(context, data_dict):
    """ Approve or reject """
    return {'success': False}
