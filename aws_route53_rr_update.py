#!/usr/bin/env python3

import sys
import boto3
from pprint import pprint
import requests
import socket


DNS_RR_TYPE = 'A'
DNS_RR = 'neniko.eu.'
DNS_ZONE = DNS_RR
URL_META = 'http://169.254.169.254/latest/meta-data/public-ipv4'
URL_TMOUT = 5


def main():
    try:

        local_pub_ip = ec2_local_pub_ip()
        client = boto3.client('route53')
        hosted_zone_id, dns_rrs = get_dns_rrs(client)
        change_dns_rr(client, hosted_zone_id, dns_rrs, local_pub_ip)

    except Exception as e:
        print("INVALID INPUT", str(e))
        return 1


def change_dns_rr(client, hostedzoneid, dns_rrs, local_pub_ip):
    """

    :param client:
    :param hostedzoneid:
    :param dns_rrs:
    :return:
    """
    if dns_rrs['ResourceRecordSets']:
        for dns_rr in dns_rrs['ResourceRecordSets']:
            if dns_rr['Type'] == DNS_RR_TYPE and dns_rr['Name'] == DNS_RR:
                rr_ip = dns_rr['ResourceRecords'][0]['Value']
                print("Current Host zone RR: " + str(dns_rr))

                if rr_ip != local_pub_ip:
                    dns_rr['ResourceRecords'][0]['Value'] = local_pub_ip
                    # pprint(dns_rr)
                    response = client.change_resource_record_sets(
                        HostedZoneId=hostedzoneid,
                        ChangeBatch={'Changes': [
                            {'Action': 'UPSERT',
                             'ResourceRecordSet': dns_rr
                             }
                        ]})
                    # print("Response code: " + str(response['ResponseMetadata']['HTTPStatusCode']))
                    # print("Response status: " + response['ChangeInfo']['Status'])
                    pprint(response)
                else:
                    print("DNS address is the same as the local public ipv4 address. Change is not required.")


def get_dns_rrs(client):
    """

    :param client:
    :return:
    """
    response_hosted_zone = client.list_hosted_zones_by_name(DNSName=DNS_ZONE)
    hosted_zone_id = str(response_hosted_zone['HostedZones'][0]['Id'])
    print("Hosted Zone id: " + hosted_zone_id)

    dns_rrs = client.list_resource_record_sets(HostedZoneId=hosted_zone_id,
                                               StartRecordName=DNS_RR,
                                               StartRecordType=DNS_RR_TYPE,
                                               MaxItems='1')
    return hosted_zone_id, dns_rrs


def ec2_local_pub_ip():
    """

    :return:
    """
    try:
        response = requests.get(URL_META, timeout=URL_TMOUT)
        ipaddress = response.content.decode("utf-8")
        print("Local Public IPv4 address: " + ipaddress)

        socket.inet_aton(ipaddress)
        return ipaddress

    except socket.error as e:
        raise ValueError(e)

if __name__ == '__main__':
    sys.exit(main())
