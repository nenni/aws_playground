#!/usr/bin/env python3

import sys
import subprocess
import boto3


SSH_BIN = '/usr/bin/ssh'
AWS_USER = 'ec2-user'
AWS_CERT = '~/Projects/AWS/nenni/n_aws_linux_micro_1.pem'
SSH_TMOUT = 20


def main():
    try:
        list_instances = get_aws_node_ip()

        if list_instances:
            user_input = int(input("Please select instance id to connect to: "))
            if 0 <= user_input < len(list_instances):
                host = list_instances[user_input]

        ssh_cmd = '{ssh_bin} -i {aws_cert} {aws_user}@{host}'.format(
            ssh_bin=SSH_BIN,
            aws_cert=AWS_CERT,
            aws_user=AWS_USER,
            host=host
        )

        print(ssh_cmd)
        subprocess.run(ssh_cmd, timeout=SSH_TMOUT, shell=True)

    except Exception as e:
        print("INVALID INPUT")
        return 1



def get_aws_node_ip():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.all()
    instance_id = 0

    list_instances_ip = []
    for instance in instances:
        list_instances_ip.append(instance.public_ip_address)

        print("{id}) {hostname} | State: {state} | Public IP/FQDN: {pub_fqdn}".format(
            id=instance_id,
            hostname=instance.tags[0].get('Value', None),
            state=str(instance.state["Name"]).upper(),
            pub_fqdn=instance.public_dns_name,
        ))

        instance_id += 1

    return list_instances_ip


if __name__ == '__main__':
    sys.exit(main())
