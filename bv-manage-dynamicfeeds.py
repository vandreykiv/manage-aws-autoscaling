# !/usr/bin/python26
#######################################################################
## Script for decrease/restore capacity for all AutoScaling group
## that match criteria
## Usage:
## <script name> --tag-value env:stg [--tag-value cluster:c1] \
##               --restore/decrease --wait --capacity 100 --region us-east-1
##
## Required params: --tag-value - Any AWS Tag or Tags combination
##                                for match AutoScaling groups.
##
## Optional params: --restore   - Restore max instances count for
##                                AutoScaling groups.
##                                If capacity didn't set then max=100.
##                                Without this option will be showed
##                                list of match AutoScaling Groups.
##                                No changes will be made
##                  --decrease  - Decrease max/min/desired capacity to zero
##                                for all AutoScaling groups.
##                                Without this option will be showed
##                                list of match AutoScaling Groups.
##                                No changes will be made
##                  --region    - AWS region for AutoScale connection.
##                                If not defined will be taken from
##                                EC2 metadata from instance
##                                where script is running.
##                  --wait      - Script waits while all instances
##                                terminates before exit.
##                  --capacity  - Value for max instances count during
##                                restore capacity job.
##                                Default value 100.
##
## tag-value parameter may be used multiple times.
## In such case action (restore/decrease) will be applied
## for all combinations of this params.
#######################################################################
## Date: 05/30/2014
## vandreykiv (email@andreykiv.com)
#######################################################################

import aws_auth
import boto.ec2.autoscale
import argparse
import sys
import time
import utils.asgutils


def as_decrease(as_connection, as_groups, capacity=0):
    """ Decrease Auto Scaling processes for an Auto Scaling group. """
    as_action(as_connection, as_groups, "decrease", capacity)


def as_restore(as_connection, as_groups, capacity):
    """ Restore capacity for Auto Scaling group. """
    as_action(as_connection, as_groups, "restore", capacity)


def as_action(as_connection, as_groups, action, capacity):
    """ Suspend/Resume AutoScaling Groups according to action parameter"""
    for as_group in as_groups:
        try:
            if action is "decrease":
                as_group = as_connection. \
                    get_all_groups(names=[as_group.name])[0]
                setattr(as_group, 'max_size', 0)
                setattr(as_group, 'min_size', 0)
                setattr(as_group, 'desired_capacity', 0)
                as_group.update()
            elif action is "restore":
                as_group = as_connection. \
                    get_all_groups(names=[as_group.name])[0]
                setattr(as_group, 'max_size', capacity)
                as_group.update()
            print "Auto scaling group {0} capacity finished. Group {1}" \
                .format(action, as_group.name)
        except Exception, err:
            print "Can't {0} capacity for auto scaling group {1}" \
                .format(action, as_group.name)
            print "Error: {0}".format(err)
            sys.exit(1)


def main():
    """ Main program """
    # Parse arguments
    description = 'Tool to terminate/restore capacity of feeds ' \
                  'autoscaling groups.'
    epilog = "EXAMPLE: %(prog)s --env dev --cluster c1 " \
             "--terminate/restore --region us-east-1 --wait"

    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--decrease', action="store_true",
                       help="Decrease capacity to zero for "
                            "feeds autoscaling groups")
    group.add_argument('--restore', action="store_true",
                       help="Restore default capacity of feeds"
                            "autoscaling groups")
    parser.add_argument('--wait', action="store_true",
                       help="Wait while all dynamic feeds instances terminated")
    parser.add_argument('--region', type=str,
                        help="Define AWS region for create AutoScaling "
                             "connection")
    parser.add_argument('--capacity', type=int, default=100,
                        help="Define max instances value for AutoScaling group")
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
        meta_data = utils.asgutils.get_metadata()
        region = meta_data['placement/availability-zone'][:-1]

    if args.restore and args.wait:
        print "Restore action can't be used with wait option."
        parser.print_help()
        sys.exit(1)

    # Open connection to AWS AutoScale service.
    as_connection = boto.ec2.autoscale.connect_to_region(region,
                                                         aws_access_key_id=aws_auth.AWS_ID,
                                                         aws_secret_access_key=aws_auth.AWS_SECRET)
    try:
        tags = utils.asgutils.params_to_dict(args.tags)
        list_as_groups = utils.asgutils.as_group_match(as_connection, tags)
    except Exception, err:
        raise Exception("Unable to connect to EC2. Error {0}".format(err))

    if len(list_as_groups):
        group_names = [group.name for group in list_as_groups]
        print "List of AutoScaling groups: {0}".format(group_names)
    else:
        print "No AutoScaling groups found. Continue"
        sys.exit(0)

    # Decrease or increase capacity for necessary AutoScaling groups.
    if args.decrease:
        print "Try to decrease capacity for dynamic feeds AutoScaling groups."
        as_decrease(as_connection, list_as_groups, args.capacity)
    elif args.restore and not args.wait:
        print "Try to restore capacity for dynamic feeds AutoScaling groups."
        as_restore(as_connection, list_as_groups, args.capacity)
    else:
        print "Decrease or Restore action " \
              "argument is required to perform action."
        print "As there is no any of them " \
              "will be show matching AutoScaling groups."
        for as_group in list_as_groups:
            print "Group that match all criteria: " + as_group
        sys.exit(1)

    if args.wait:
        for as_group_name in list_as_groups:
            running_instances_list = utils.asgutils.get_as_instances(
                as_connection,
                as_group_name)
            while len(running_instances_list):
                print "Not all dynamic feeds instances terminated. " \
                      "Sleeping for 30s"
                time.sleep(30)
                running_instances_list = utils.asgutils.get_as_instances(
                    as_connection,
                    as_group_name)
            print "All instances for AutoScaling group {0} terminated.".\
                format(as_group_name)


if __name__ == "__main__":
    main()
    sys.exit(0)
