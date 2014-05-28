#!/usr/bin/python26
#######################################################################
## Script for suspend/resume all processes for all AutoScaling group
## that match criteria
## Usage:
## <script name> --tag-value env:stg [--tag-value cluster:c1] \
##               --suspend/resume --region us-east-1
##
## Required params: --tag-value - Any AWS Tag or Tags combination
##                                for match AutoScaling groups.
##
## Optional params: --suspend   - Suspend all processes for
##                                AutoScaling groups.
##                                Without this option will be showed
##                                list of match AutoScaling Groups.
##                                No changes will be made
##                  --resume    - Resume all processes
##                                for AutoScaling groups.
##                                Without this option will be showed
##                                list of match AutoScaling Groups.
##                                No changes will be made
##                  --region    - AWS region for AutoScale connection.
##                                If not defined will be taken from
##                                EC2 metadata from instance
##                                where script is running.
##
## tag-value parameter may be used multiple times.
## In such case action (suspen/resume) will be applied
## for all combinations of this params.
## For example <script name> --tag-value env:prod \
##                           --tag-value env:stg \
##                           --tag-value cluster:c1 \
##                           --tag-value cluster:c7 \
##                           --tag-value role:dbsubmit1_role \
##                           --region eu-west-1
## will show all all staging and production AutoScaling groups
## for cluster c1 and c7 with role dbsubmit1_role.
##
## EXAMPLE OUTPUT: asg-suspend-resume.py --tag-value env:prod \
##                                       --tag-value env:stg \
##                                       --tag-value cluster:c1 \
##                                       --tag-value cluster:c7 \
##                                       --tag-value role:dbsubmit1_role \
##                                       --region eu-west-1
## Finishing processing next 50 AutoScaling Groups
## Finishing processing next 50 AutoScaling Groups
## Finishing processing next 50 AutoScaling Groups
## Processed 193 AutoScaling Groups
## Suspend or Resume action argument is required to perform action.
## As there is no any of them will be show matching AutoScaling groups.
## Group that match all creterias: prod-c7-dbsubmit1
## Group that match all creterias: stg-c7-dbsubmit1
##
#######################################################################
## Date: 09/30/2013
## vandreykiv (vyacheslav.andreykiv@bazaarvoice.com)
## For details see AVI-1959
#######################################################################

import aws_auth
import boto.ec2.autoscale
import argparse
import sys
import urllib


def get_meta():
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


def params_to_dict(tags):
    """ Reformat tag-value params into dictionary. """
    tags_dict = {}
    tags_name_value_list = [tag[0].split(':') for tag in tags]
    for tag_name, tag_value in tags_name_value_list:
        tags_dict.setdefault(tag_name, []).append(tag_value)
    return tags_dict


def as_group_match(as_group, match_tags):
    result = 0
    for tag in as_group.tags:
        if tag.key in match_tags:
            if tag.value in match_tags[tag.key]:
                result += 1
    if result == len(match_tags):
            return as_group


def as_suspend(as_connection, match_as_groups):
    """ Suspends Auto Scaling processes for an Auto Scaling group. """
    as_action(as_connection, match_as_groups, "suspend")


def as_resume(as_connection, match_as_groups):
    """ Resumes Auto Scaling processes for an Auto Scaling group. """
    as_action(as_connection, match_as_groups, "resume")


def as_action(as_connection, match_as_groups, action):
    """ Suspend/Resume AutoScaling Groups according to action parameter"""
    for as_group in match_as_groups:
        try:
            if action is "suspend":
                as_connection.suspend_processes(as_group.name)
            elif action is "resume":
                as_connection.resume_processes(as_group.name)
            print "All processes {0} for auto scaling " \
                  "group {1} finished".format(action, as_group.name)
        except:
            print "Can't {0} processes for auto scaling " \
                  "group {1}".format(action, as_group.name)
            sys.exit(1)


def main():
    """ Main program """
    # Parse arguments
    description = 'Tool to suspend/resume autoscaling groups.'
    epilog = "EXAMPLE: %(prog)s --tag-value env:stg --tag-value cluster:c1 " \
             "--suspend/resume --region us-east-1"

    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--resume', action="store_true",
                       help="Resume autoscaling actions")
    group.add_argument('--suspend', action="store_true",
                       help="Suspend autoscaling actions")
    parser.add_argument('--region', type=str,
                        help="Define AWS region for create AutoScaling connection")
    parser.add_argument('--tag-value', nargs='*', dest="tags", action='append',
                        required=True,
                        help="List of tags with value to find ASGs")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    if args.region:
        region = args.region
    else:
        meta_data = get_meta()
        region = meta_data['placement/availability-zone'][:-1]

    # Open connection to AWS AutoScale service.
    as_connection = boto.ec2.autoscale.connect_to_region(region,
                                     aws_access_key_id=aws_auth.AWS_ID,
                                     aws_secret_access_key=aws_auth.AWS_SECRET)
    tags_dict = params_to_dict(args.tags)
    # Find all AutoScaling groups that match tags from input arguments pattern
    match_as_groups = []
    for as_group in get_all_as_groups(as_connection):
        match_as_group = as_group_match(as_group, tags_dict)
        if match_as_group is not None:
            match_as_groups.append(match_as_group)

    # Suspend or resume all processes for necessary AutoScaling groups.
    if args.resume:
        as_resume(as_connection,
                                  match_as_groups)
    elif args.suspend:
        as_suspend(as_connection,
                                   match_as_groups)
    else:
        print "Suspend or Resume action " \
              "argument is required to perform action."
        print "As there is no any of them " \
              "will be show matching AutoScaling groups."
        for as_group in match_as_groups:
            print "Group that match all criteria: " + as_group.name
        sys.exit(1)


if __name__ == "__main__":
    main()
    sys.exit(0)

