# H1 asg-suspend-resume.py:
Can suspend/resume processes for AWS AutoScaling groups according to set of tags. 

Usage:
<script name> --tag-value env:stg [--tag-value cluster:c1] --suspend/resume --region us-east-1
Required params: --tag-value - Any AWS Tag or Tags combination for match AutoScaling groups.
Optional params: --suspend   - Suspend all processes for AutoScaling groups.
                               Without this option will be showed list of match AutoScaling Groups.
                               No changes will be made
                 --resume    - Resume all processes for AutoScaling groups.
                               Without this option will be showed list of match AutoScaling Groups.
                               No changes will be made
                 --region    - AWS region for AutoScale connection. If not defined will be taken from
                               EC2 metadata from instance where script is running.

tag-value parameter may be used multiple times.
In such case action (suspen/resume) will be applied for all combinations of this params.
For example <script name> --tag-value env:prod \
                          --tag-value env:stg \
                          --tag-value cluster:c1 \
                          --tag-value cluster:c7 \
                          --tag-value role:dbsubmit1_role \
                          --region eu-west-1
will show all all staging and production AutoScaling groups
for cluster c1 and c7 with role dbsubmit1_role.

EXAMPLE OUTPUT: asg-suspend-resume.py --tag-value env:prod \
                                    --tag-value env:stg \
                                    --tag-value cluster:c1 \
                                    --tag-value cluster:c7 \
                                    --tag-value role:dbsubmit1_role \
                                    --region eu-west-1
Processed 193 AutoScaling Groups
Suspend or Resume action argument is required to perform action.
As there is no any of them will be show matching AutoScaling groups.
Group that match all creterias: prod-c7-dbsubmit1
Group that match all creterias: stg-c7-dbsubmit1

# H1
aws_auth.py:
Sample file with <API key_id> and <secret_key>
