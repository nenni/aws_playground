#!/usr/bin/env python3

import sys
import subprocess
import boto3
from argparse import RawTextHelpFormatter, ArgumentParser

SSH_BIN = '/usr/bin/ssh'
SSH_TMOUT = 20000


def main():
    try:
        pem_file, ec2_user = arg_params()
        list_instances = get_aws_node_ip()

        if list_instances:
            user_input = int(input("Please select instance id to connect to (0 to quit): "))
            if user_input == 0:
                exit(2)

            # print(list_instances)
            if 1 <= user_input < (len(list_instances)+1):
                host = list_instances[user_input-1]
                # print(host)
                ssh_cmd = '{ssh_bin} -i {aws_cert} {aws_user}@{host}'.format(
                    ssh_bin=SSH_BIN,
                    aws_cert=pem_file,
                    aws_user=ec2_user,
                    host=host
                )
                print(ssh_cmd)
                subprocess.run(ssh_cmd, timeout=SSH_TMOUT, shell=True)
    except Exception as e:
        print("INVALID INPUT", str(e))
        return 1


def arg_params():
    parser = ArgumentParser(description="AWS EC2 SSH connection script",
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('-p', dest="pem_file", help='ssh PEM file', required=True)
    parser.add_argument('-u', dest="user", help='AWS EC2 instance user', required=True)
    args = parser.parse_args()
    pem_file = args.pem_file
    ec2_user = args.user

    return pem_file, ec2_user


def get_aws_node_ip():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.all()
    local_index = 1

    list_instances_ip = []
    for instance in instances:
        list_instances_ip.append(instance.public_ip_address)

        tags = instance.tags
        for tag in tags:
            if tag['Key'] == 'Name':
                tag_name = tag.get("Value", None)

        print("{id}) {hostname} | State: {state} | Public FQDN: {pub_fqdn}".format(
            id=local_index,
            hostname=tag_name,
            state=str(instance.state["Name"]).upper(),
            pub_fqdn=instance.public_dns_name,
        ))
        local_index += 1
    return list_instances_ip


if __name__ == '__main__':
    sys.exit(main())
