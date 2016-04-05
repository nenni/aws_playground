#!/usr/bin/env python3

import sys
import boto3
from pprint import pprint


DNS_RR_TYPE = 'A'
DNS_RR = 'neniko.eu.'
DNS_ZONE = DNS_RR
L_PUBLIC_IPv4 = '52.37.190.179'


def main():
    try:
        client = boto3.client('route53')

        response_hostedzone = client.list_hosted_zones_by_name(DNSName=DNS_ZONE)
        hostedzoneid = response_hostedzone['HostedZones'][0]['Id']
        print(hostedzoneid)

        dns_rrs = client.list_resource_record_sets(HostedZoneId=hostedzoneid,
                                                   StartRecordName=DNS_RR,
                                                   StartRecordType=DNS_RR_TYPE,
                                                   MaxItems='1')

        if dns_rrs['ResourceRecordSets']:
            for dns_rr in dns_rrs['ResourceRecordSets']:
                if dns_rr['Type'] == DNS_RR_TYPE and dns_rr['Name'] == DNS_RR:
                    rr = dns_rr
                    rr_ip = dns_rr['ResourceRecords'][0]['Value']
                    print("Host zone RR: " + str(rr))

                    if L_PUBLIC_IPv4 != rr_ip:
                        new_rr = rr
                        new_rr['ResourceRecords'][0]['Value'] = L_PUBLIC_IPv4
                        pprint(new_rr)
                        response = client.change_resource_record_sets(
                            HostedZoneId=hostedzoneid,
                            ChangeBatch={'Changes': [
                                {'Action': 'UPSERT',
                                 'ResourceRecordSet': new_rr
                                 }
                            ]})
                        pprint(response)

    except Exception as e:
        print("INVALID INPUT", str(e))
        return 1


if __name__ == '__main__':
    sys.exit(main())
