from ckanext.ytp.request import auth
from ckan import model, new_authz
from sqlalchemy.sql.expression import or_
from ckan.lib.dictization import model_dictize
from ckan.logic import NotFound, ValidationError
from ckan.common import _


def _member_list_dictize(obj_list, context, sort_key=lambda x: x['group_id'], reverse=False):
    """ Helper to convert member list to dictionary """
    result_list = []
    for obj in obj_list:
        member_dict = model_dictize.member_dictize(obj, context)
        member_dict['group_name'] = obj.group.name
        user = model.Session.query(model.User).get(obj.table_id)
        member_dict['user_name'] = user.name
        result_list.append(member_dict)
    return sorted(result_list, key=sort_key, reverse=reverse)


def _create_member_request(context, data_dict):
    """ Helper to create member request """
    changed = False
    role = data_dict['role']
    group = model.Group.get(data_dict['group'])

    if not group or group.type != 'organization':
        raise NotFound

    user = context['user']
    userobj = model.User.get(user)

    member = model.Session.query(model.Member).filter(model.Member.table_name == "user").filter(model.Member.table_id == userobj.id) \
        .filter(model.Member.group_id == group.id).filter(or_(model.Member.state == 'active', model.Member.state == 'pending')).first()

    if member:
        if member.state == 'pending':
            message = _("You already have pending request to the organization")
        else:
            message = _("You are already part of the organization")

        raise ValidationError({"organization": _("Duplicate organization request")}, {_("Organization"): message})

    member = model.Session.query(model.Member).filter(model.Member.table_name == "user").filter(model.Member.table_id == userobj.id) \
        .filter(model.Member.group_id == group.id).first()

    if not member:
        member = model.Member(table_name="user", table_id=userobj.id, group_id=group.id, capacity=role, state='pending')
        changed = True

    if member.state != 'pending' or changed:
        member.state = 'pending'
        member.capacity = role
        revision = model.repo.new_revision()
        revision.author = user
        if 'message' in context:
            revision.message = context['message']
        elif changed:
            revision.message = _(u'Create new member request %s %s') % (user, data_dict['group'])
        else:
            revision.message = _(u'Changed member request (%s %s) state to pending') % (user, data_dict['group'])

        if changed:
            model.Session.add(member)
        else:
            member.save()
        model.repo.commit()
        changed = True

    return member, changed


def member_request_create(context, data_dict):
    ''' Create new member request. User is taken from context.

    :param group: name of the group or organization
    :type group: string
    '''
    auth.member_request_create(context, data_dict)
    member, _changed = _create_member_request(context, data_dict)
    return model_dictize.member_dictize(member, context)


def member_request_show(context, data_dict):
    ''' Create new member request. User is taken from context.

    :param member: id of the member object
    :type member: string

    :param fetch_user: fetch related user data
    :type fetch_user: boolean
    '''
    auth.member_request_show(context, data_dict)
    model = context['model']
    member_id = data_dict.get("member")
    fetch_user = data_dict.get("fetch_user", False)
    member = model.Session.query(model.Member).get(member_id)

    if not member.group.is_organization:
        raise NotFound

    data = model_dictize.member_dictize(member, context)

    if fetch_user:
        member_user = model.Session.query(model.User).get(member.table_id)
        data['user'] = model_dictize.user_dictize(member_user, context)

    return data


def member_request_list(context, data_dict):
    ''' List my member requests.

    :param group: name of the group (optional)
    :type group: string
    '''
    auth.member_request_list(context, data_dict)

    user = context['user']
    user_object = model.User.get(user)
    sysadmin = new_authz.is_sysadmin(user)

    query = model.Session.query(model.Member).filter(model.Member.table_name == "user").filter(model.Member.state == 'pending')

    if not sysadmin:
        admin_in_groups = model.Session.query(model.Member).filter(model.Member.state == "active").filter(model.Member.table_name == "user") \
            .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == user_object.id)

        if admin_in_groups.count() <= 0:
            return []

        query = query.filter(model.Member.group_id.in_(admin_in_groups.values(model.Member.group_id)))

    group = data_dict.get('group', None)
    if group:
        group_object = model.Group.get(group)
        if group_object:
            query = query.filter(model.Member.group_id == group_object.id)

    members = query.all()

    return _member_list_dictize(members, context)


def member_request_process(context, data_dict):
    ''' Approve or reject member request.

    :param member: id of the member
    :type member: string

    :param approve: approve or reject request
    :type accpet: boolean
    '''
    auth.member_request_process(context, data_dict)
    member_id = data_dict.get("member")
    approve = data_dict.get('approve')
    user = context["user"]

    state = "active" if approve else "deleted"

    member = model.Session.query(model.Member).get(member_id)
    if not member or not member.group.is_organization:
        raise NotFound

    member.state = state
    revision = model.repo.new_revision()
    revision.author = user

    if 'message' in context:
        revision.message = context['message']
    else:
        revision.message = _(u'Changed member request (%s %s) state to %s') % (user, member_id, state)

    member.save()
    model.repo.commit()
    return model_dictize.member_dictize(member, context)
