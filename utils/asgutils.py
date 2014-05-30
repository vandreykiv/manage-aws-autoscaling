import urllib


def get_metadata():
    """ Grabs Amazon supplied meta_data """
    meta_data = {}
    keys = ['ami-id', 'placement/availability-zone', 'instance-id',
            'instance-type', 'local-hostname', 'local-ipv4',
            'public-hostname', 'public-ipv4', 'security-groups', 'user-data']
    for key in keys:
        url = "http://169.254.169.254/latest/meta-data/" + key
        meta_data[key] = urllib.urlopen(url).read()
    meta_data['security-groups'] = meta_data['security-groups'].split('\n')
    return meta_data


def get_all_as_groups(as_connection):
    """ Get all AutoScaling Groups in current region. """
    as_groups_list = []
    get_as_groups = as_connection.get_all_groups()
    as_groups_list.extend(get_as_groups)

    token = get_as_groups.next_token
    while token is not None:
        get_as_groups = as_connection.get_all_groups(
            next_token=token)
        as_groups_list.extend(get_as_groups)
        token = get_as_groups.next_token
    print "Processed {0} AutoScaling Group"\
        .format(len(as_groups_list))
    return as_groups_list


def get_as_name(as_connection, environment, cluster):
    """
    Returns AutoScaling group name for given environment and cluster.
    """
    list_as_groups = []
    config = {'env': environment,
              'cluster': cluster,
              'role': 'feeds'}
    for as_group in get_all_as_groups(as_connection):
        result = 0
        for tag in as_group.tags:
            if tag.key in config:
                if tag.value in config[tag.key]:
                    result += 1
        if result == len(config):
            list_as_groups.append(as_group.name)
    return list_as_groups


def as_group_match(as_connection, match_tags):
    """ Check if AutoScaling group tags is the same as given.
    Returns list of groups with the same set of tags.
    """
    match_groups = []
    as_groups_list = get_all_as_groups(as_connection)
    for as_group in as_groups_list:
        result = 0
        for tag in as_group.tags:
            if tag.key in match_tags:
                if tag.value in match_tags[tag.key]:
                    result += 1
        if result == len(match_tags):
            match_groups.append(as_group)
    return match_groups


def get_as_instances(as_connection, as_group_name):
    """ Returns all instances running in given AutoScaling group"""
    as_all_instances_list = []
    as_instances_list = []
    get_as_instances = as_connection.get_all_autoscaling_instances()
    as_all_instances_list.extend(get_as_instances)

    token = get_as_instances.next_token
    while token is not None:
        get_as_groups = as_connection.get_all_autoscaling_instances(
            next_token=token)
        as_all_instances_list.extend(get_as_groups)
        token = get_as_groups.next_token

    for instance in as_all_instances_list:
        if instance.group_name in as_group_name:
            as_instances_list.append(instance.instance_id)
    return as_instances_list


def params_to_dict(tags):
    """ Reformat tag-value params into dictionary. """
    tags_dict = {}
    tags_name_value_list = [tag[0].split(':') for tag in tags]
    for tag_name, tag_value in tags_name_value_list:
        tags_dict.setdefault(tag_name, []).append(tag_value)
    return tags_dict
