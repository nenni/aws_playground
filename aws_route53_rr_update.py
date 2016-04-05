#!/usr/bin/env python3

import sys
import boto3
from pprint import pprint
import requests


DNS_RR_TYPE = 'A'
DNS_RR = 'neniko.eu.'
DNS_ZONE = DNS_RR
URL_META = 'http://169.254.169.254/latest/meta-data/public-ipv4'
URL_TMOUT = 5


def main():
    try:
        client = boto3.client('route53')

        response_hostedzone = client.list_hosted_zones_by_name(DNSName=DNS_ZONE)
        hostedzoneid = response_hostedzone['HostedZones'][0]['Id']
        print("Hosted Zone id: " + hostedzoneid)

        response = requests.get(URL_META, timeout=URL_TMOUT)
        local_pub_ip = response.content.decode("utf-8")
        print("Local Public IPv4 address: " + local_pub_ip)

        dns_rrs = client.list_resource_record_sets(HostedZoneId=hostedzoneid,
                                                   StartRecordName=DNS_RR,
                                                   StartRecordType=DNS_RR_TYPE,
                                                   MaxItems='1')

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

    except Exception as e:
        print("INVALID INPUT", str(e))
        return 1


if __name__ == '__main__':
    sys.exit(main())
