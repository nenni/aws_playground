#!/usr/bin/env python3

import sys
import logging
from argparse import ArgumentParser, RawTextHelpFormatter
import requests
import socket
import boto3


DNS_RR_TYPE = 'A'
URL_META = 'http://169.254.169.254/latest/meta-data/public-ipv4'
URL_TMOUT = 5


def main():
    try:

        logging.basicConfig(filename='route53_update.log', format='%(asctime)s %(message)s', level=logging.INFO)
        zone, a_rr = arg_params()
        local_pub_ip = ec2_local_pub_ip()
        client = boto3.client('route53')
        hosted_zone_id, dns_rrs = get_dns_rrs(client, zone, a_rr)
        change_dns_rr(client, hosted_zone_id, dns_rrs, local_pub_ip, a_rr)

    except Exception as e:
        logging.critical("Route53Update: Invalid: " + str(e))
        return 1


def arg_params():
    parser = ArgumentParser(description="AWS Route53 A RR update script",
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('-z', dest='zone_name', help='route53 hosted zone', required=True)
    parser.add_argument('-a', dest='a_record', help='A resource record to be updated', required=True)
    args = parser.parse_args()
    zone_name = args.zone_name
    a_record = args.a_record

    if a_record and zone_name:
        logging.info("Route53Update: Gathering parameters. Zone: {zone} and A record: {a_rr}".format(
            zone=zone_name,
            a_rr=a_record
        ))
    return zone_name, a_record


def ec2_local_pub_ip():
    """

    :return:
    """
    try:
        response = requests.get(URL_META, timeout=URL_TMOUT)
        ipaddress = response.content.decode("utf-8")
        logging.info("Route53Update: Local Public IPv4 address: " + ipaddress)

        socket.inet_aton(ipaddress)
        return ipaddress

    except socket.error as e:
        logging.critical("Route53Update: EC2 metadata public ipv4 is unavailable or not IP address format")
        return 2


def get_dns_rrs(client, zone, a_record):
    """

    :param client:
    :return:
    """
    response_hosted_zone = client.list_hosted_zones_by_name(DNSName=zone)
    hosted_zone_id = str(response_hosted_zone['HostedZones'][0]['Id'])
    logging.info("Route53Update: Hosted Zone id: " + hosted_zone_id)

    dns_rrs = client.list_resource_record_sets(HostedZoneId=hosted_zone_id,
                                               StartRecordName=a_record,
                                               StartRecordType=DNS_RR_TYPE,
                                               MaxItems='1')
    return hosted_zone_id, dns_rrs


def change_dns_rr(client, hostedzoneid, dns_rrs, local_pub_ip, a_record):
    """

    :param client:
    :param hostedzoneid:
    :param dns_rrs:
    :return:
    """
    if dns_rrs['ResourceRecordSets']:
        for dns_rr in dns_rrs['ResourceRecordSets']:
            if dns_rr['Type'] == DNS_RR_TYPE and dns_rr['Name'] == (a_record + "."):
                rr_ip = dns_rr['ResourceRecords'][0]['Value']
                logging.info("Route53Update: Current Host zone RR: " + str(dns_rr))

                if rr_ip != local_pub_ip:
                    dns_rr['ResourceRecords'][0]['Value'] = local_pub_ip
                    client.change_resource_record_sets(
                        HostedZoneId=hostedzoneid,
                        ChangeBatch={'Changes': [
                            {'Action': 'UPSERT',
                             'ResourceRecordSet': dns_rr
                             }
                        ]})
                    logging.info("A record {a_rr} in zone {zone} update with new IP public ipv4: {local_pip}".format(
                        a_rr = a_record,
                        zone=hostedzoneid,
                        local_pip=local_pub_ip
                    ))
                else:
                    logging.info("Route53Update: DNS address is the same as the local public ipv4 address. "
                                 "Change is not required.")
            else:
                logging.info("Route53Update: A record {a_rr} "
                             "does not match any records in the hosted zone {zone}".format(a_rr=a_record,
                                                                                           zone=hostedzoneid
                                                                                           ))


if __name__ == '__main__':
    sys.exit(main())
