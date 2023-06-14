# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
import requests
import base64
import math
import json
import os


class ResCompany(models.Model):
    _inherit = 'res.company'

    # BR-KSA-08
    license = fields.Selection([('CRN', 'Commercial Registration number'),
                                ('MOM', 'Momra license'), ('MLS', 'MLSD license'),
                                ('SAG', 'Sagia license'), ('OTH', 'Other OD')],
                               default='CRN', required=1, string="License",
                               help="In case multiple IDs exist then one of the above must be entered")
    license_no = fields.Char(string="License Number (Other seller ID)", required=1)

    building_no = fields.Integer('Building Number', help="https://splonline.com.sa/en/national-address-1/")
    additional_no = fields.Char('Additional Number', help="https://splonline.com.sa/en/national-address-1/")
    district = fields.Char('District')
    country_id_name = fields.Char(related="country_id.name")

    @api.constrains('building_no', 'additional_no', 'zip')
    def constrains_brksa64(self):
        for record in self:
            # if record._context.get('params', False) and record._context['params'].get('model', False) == 'res.company':
                # BR-KSA-37
                if len(str(record.building_no)) != 4:
                    raise exceptions.ValidationError('Building Number must be exactly 4 digits')
                # BR-KSA-64
                if len(str(record.additional_no)) != 4:
                    raise exceptions.ValidationError('Additional Number must be exactly 4 digits')
                # BR-KSA-66
                if len(str(record.zip)) != 5:
                    raise exceptions.ValidationError('zip must be exactly 5 digits')

    is_zatca = fields.Boolean()

    zatca_certificate_status = fields.Boolean()
    zatca_icv_counter = fields.Char(default=1, readonly=1)

    # zatca_sdk_path = fields.Char()
    zatca_status = fields.Char()
    zatca_onboarding_status = fields.Boolean()
    zatca_on_board_status_details = fields.Char()
    zatca_pih = fields.Char(default='NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ==')

    # Required fields
    zatca_link = fields.Char("Api Link", default="https://gw-apic-gov.gazt.gov.sa/e-invoicing/developer-portal")
    csr_common_name = fields.Char("Common Name")  # CN
    csr_serial_number = fields.Char("EGS Serial Number")  # SN
    # csr_organization_identifier = fields.Char("Organization Identifier", required="1")  # UID
    csr_organization_unit_name = fields.Char("Organization Unit Name")  # OU
    csr_organization_name = fields.Char("Organization Name")  # O
    # csr_country_name = fields.Char("Country Name", required="1")  # C
    csr_invoice_type = fields.Char("Invoice Type")  # title
    csr_location_address = fields.Char("Location")  # registeredAddress
    csr_industry_business_category = fields.Char("Industry")  # BusinessCategory

    csr_otp = fields.Char("Otp")
    csr_certificate = fields.Char("Certificate", required="0")
    zatca_send_from_pos = fields.Boolean('Send to zatca from pos')

    zatca_is_sandbox = fields.Boolean('Testing ?')
    zatca_private_key = fields.Char("Private key")

    # Never show these fields on front (Security and Integrity of zatca could be compromised.)
    zatca_sb_bsToken = fields.Char()
    zatca_sb_secret = fields.Char()
    zatca_sb_reqID = fields.Char()
    zatca_bsToken = fields.Char()
    zatca_secret = fields.Char()
    zatca_reqID = fields.Char()
    zatca_cert_sig_algo = fields.Char()
    zatca_prod_private_key = fields.Char()
    zatca_cert_public_key = fields.Char()
    zatca_csr_base64 = fields.Char()

    def generate_zatca_certificate(self):
        conf = self.sudo()
        if not conf.is_zatca:
            raise exceptions.AccessDenied("Zatca is not activated.")
        conf.zatca_onboarding_status = False
        if conf.csr_otp in [None, False]:
            raise exceptions.MissingError("OTP required")
        try:
            config_cnf = '''
                oid_section = OIDs
                [ OIDs ]
                certificateTemplateName= 1.3.6.1.4.1.311.20.2

                [ req ]
                default_bits = 2048
                emailAddress = myEmail@gmail.com
                req_extensions = v3_req
                x509_extensions = v3_ca
                prompt = no
                default_md = sha256
                req_extensions = req_ext
                distinguished_name = dn


                [ dn ]
                C = ''' + str(self.country_id.code) + '''
                OU = ''' + str(conf.csr_organization_unit_name) + '''
                O = ''' + str(conf.csr_organization_name) + '''
                CN = ''' + str(conf.csr_common_name) + '''

                [ v3_req ]
                basicConstraints = CA:FALSE
                keyUsage = digitalSignature, nonRepudiation, keyEncipherment

                [ req_ext ]
                certificateTemplateName = ASN1:PRINTABLESTRING:ZATCA-Code-Signing
                subjectAltName = dirName:alt_names            


                [ alt_names ]
                SN = ''' + str(conf.csr_serial_number) + '''
                UID = ''' + str(self.vat) + '''
                title = ''' + str(conf.csr_invoice_type) + '''
                registeredAddress = ''' + str(conf.csr_location_address) + '''
                businessCategory = ''' + str(conf.csr_industry_business_category) + '''
            '''

            f = open('/tmp/zatca.cnf', 'w+')
            f.write(config_cnf)
            f.close()

            # Certificate calculation moved to new function
            if self.zatca_is_sandbox:
                private_key = conf.zatca_private_key
                private_key = private_key.replace('-----BEGIN EC PRIVATE KEY-----', '') \
                                         .replace('-----END EC PRIVATE KEY-----', '')\
                                         .replace(' ', '').replace('\n', '')
                self.zatca_prod_private_key = private_key
            else:
                private_key = 'openssl ecparam -name secp256k1 -genkey -noout'
            public_key = 'openssl ec -in /tmp/zatcaprivatekey.pem -pubout -conv_form compressed -out /tmp/zatcapublickey.pem'
            public_key_bin = 'openssl base64 -d -in /tmp/zatcapublickey.pem -out /tmp/zatcapublickey.bin'
            csr = 'openssl req -new -sha256 -key /tmp/zatcaprivatekey.pem -extensions v3_req -config /tmp/zatca.cnf -out /tmp/zatca_taxpayper.csr'
            csr_base64 = "openssl base64 -in /tmp/zatca_taxpayper.csr"
            if not self.zatca_is_sandbox:
                private_key = os.popen(private_key).read()
                private_key = private_key.replace('-----BEGIN EC PRIVATE KEY-----', '') \
                                         .replace('-----END EC PRIVATE KEY-----', '')\
                                         .replace(' ', '')\
                                         .replace('\n', '')
                self.zatca_prod_private_key = private_key

            for x in range(1, math.ceil(len(private_key) / 64)):
                private_key = private_key[:64 * x + x - 1] + '\n' + private_key[64 * x + x - 1:]
            private_key = "-----BEGIN EC PRIVATE KEY-----\n" + private_key + "\n-----END EC PRIVATE KEY-----"

            f = open('/tmp/zatcaprivatekey.pem', 'w+')
            f.write(private_key)
            f.close()

            os.system(public_key)
            os.system(public_key_bin)
            os.system(csr)
            conf.zatca_csr_base64 = os.popen(csr_base64).read()
            conf.zatca_status = 'CSR, private & public key generated'
            csr_invoice_type = conf.csr_invoice_type

            qty = 3
            if csr_invoice_type == '1100':
                zatca_on_board_status_details = {
                    'standard': {
                        'credit': 0,
                        'debit': 0,
                        'invoice': 0,
                    },
                    'simplified': {
                        'credit': 0,
                        'debit': 0,
                        'invoice': 0,
                    }
                }
                message = "Standard & its associated invoices and Simplified & its associated invoices"
                message = "Standard: invoice, debit, credit, \nSimplified: invoice, debit, credit, "
                qty = 6
            elif csr_invoice_type == '1000':
                zatca_on_board_status_details = {
                    'standard': {
                        'credit': 0,
                        'debit': 0,
                        'invoice': 0,
                    }
                }
                message = "Standard & its associated invoices"
                message = "Standard: invoice, debit, credit, "
            elif csr_invoice_type == '0100':
                zatca_on_board_status_details = {
                    'simplified': {
                        'credit': 0,
                        'debit': 0,
                        'invoice': 0,
                    }
                }
                message = "Simplified & its associated invoices"
                message = "Simplified: invoice, debit, credit, "
            else:
                raise exceptions.ValidationError("Invalid Invoice Type defined.")
            conf.zatca_on_board_status_details = json.dumps(zatca_on_board_status_details)
            conf.zatca_status = 'Onboarding started, required ' + str(qty) + ' invoices' + "\n" + message

            # filepath = os.popen("find -name 'zatca_sdk'").read()
            # filepath = filepath.replace('zatca_sdk', '').replace('\n', '')
            # self.env['ir.config_parameter'].sudo().set_param("zatca_sdk_path", filepath)

        except Exception as e:
            # raise exceptions.MissingError(e)
            raise exceptions.MissingError('Server Error, Contact administrator.')
        finally:
            # For security purpose, files should not exist out of odoo
            os.system('''rm  /tmp/zatcaprivatekey.pem''')
            os.system('''rm  /tmp/zatca.cnf''')
            os.system('''rm  /tmp/zatcapublickey.pem''')
            os.system('''rm  /tmp/zatcapublickey.bin''')
            os.system('''rm  /tmp/zatca_taxpayper.csr''')
            os.system('''rm  /tmp/zatca_taxpayper_64.csr''')

        self.compliance_api()
        conf.csr_otp = None
        # self.compliance_api('/production/csids', 1)
        #     CNF, PEM, CSR created

    def compliance_api(self, endpoint='/compliance', renew=0):
        # link = "https://gw-apic-gov.gazt.gov.sa/e-invoicing/developer-portal"
        conf = self.sudo()
        link = conf.zatca_link

        if endpoint == '/compliance':
            zatca_otp = conf.csr_otp
            headers = {'accept': 'application/json',
                       'OTP': zatca_otp,
                       'Accept-Version': 'V2',
                       'Content-Type': 'application/json'}

            csr = conf.zatca_csr_base64
            data = {'csr': csr.replace('\n', '')}
        elif endpoint == '/production/csids' and not renew:
            user = conf.zatca_sb_bsToken
            password = conf.zatca_sb_secret
            compliance_request_id = conf.zatca_sb_reqID
            auth = base64.b64encode(('%s:%s' % (user, password)).encode('utf-8')).decode('utf-8')
            headers = {'accept': 'application/json',
                       'Accept-Version': 'V2',
                       'Authorization': 'Basic ' + auth,
                       'Content-Type': 'application/json'}

            data = {'compliance_request_id': compliance_request_id}
        elif endpoint == '/production/csids' and renew:
            user = conf.zatca_bsToken
            password = conf.zatca_secret
            auth = base64.b64encode(('%s:%s' % (user, password)).encode('utf-8')).decode('utf-8')
            zatca_otp = conf.csr_otp
            headers = {'accept': 'application/json',
                       'OTP': zatca_otp,
                       'Accept-Language': 'en',
                       'Accept-Version': 'V2',
                       'Authorization': 'Basic ' + auth,
                       'Content-Type': 'application/json'}
            csr = conf.zatca_csr_base64
            data = {'csr': csr.replace('\n', '')}
        try:
            req = requests.post(link + endpoint, headers=headers, data=json.dumps(data))
            if req.status_code == 500:
                if req.text:
                    response = json.loads(req.text)
                    raise exceptions.AccessError(self.error_message(response))
                raise exceptions.AccessError('Invalid Request, zatca, \ncontact system administer')
            elif req.status_code == 400:
                if req.text:
                    response = json.loads(req.text)
                    raise exceptions.AccessError(self.error_message(response))
                raise exceptions.AccessError('Invalid Request, odoo, \ncontact system administer')
            elif req.status_code == 401:
                if req.text:
                    response = json.loads(req.text)
                    raise exceptions.AccessError(self.error_message(response))
                raise exceptions.AccessError('Unauthorized, \ncontact system administer')
            elif req.status_code == 200:
                response = json.loads(req.text)
                if endpoint == '/compliance':
                    conf.zatca_sb_bsToken = response['binarySecurityToken']
                    conf.zatca_sb_reqID = response['requestID']
                    conf.zatca_sb_secret = response['secret']
                else:
                    conf.zatca_bsToken = response['binarySecurityToken']
                    conf.zatca_reqID = response['requestID']
                    conf.zatca_secret = response['secret']
                # if endpoint == '/compliance':
                #     self.compliance_api('/production/csids')
                # else:
                #     response['tokenType']
                #     response['dispositionMessage']
        except Exception as e:
            raise exceptions.AccessDenied(e)

    def production_credentials(self):
        conf = self.sudo()
        if not conf.is_zatca:
            raise exceptions.AccessDenied("Zatca is not activated.")
        if not conf.zatca_certificate_status:
            raise exceptions.MissingError("Register Certificate before proceeding.")
        if self.zatca_is_sandbox:
            zatca_bsToken = "TUlJRDFEQ0NBM21nQXdJQkFnSVRid0FBZTNVQVlWVTM0SS8rNVFBQkFBQjdkVEFLQmdncWhrak9QUVFEQWpCak1SVXdFd1lLQ1pJbWlaUHlMR1FCR1JZRmJHOWpZV3d4RXpBUkJnb0praWFKay9Jc1pBRVpGZ05uYjNZeEZ6QVZCZ29Ka2lhSmsvSXNaQUVaRmdkbGVIUm5ZWHAwTVJ3d0dnWURWUVFERXhOVVUxcEZTVTVXVDBsRFJTMVRkV0pEUVMweE1CNFhEVEl5TURZeE1qRTNOREExTWxvWERUSTBNRFl4TVRFM05EQTFNbG93U1RFTE1Ba0dBMVVFQmhNQ1UwRXhEakFNQmdOVkJBb1RCV0ZuYVd4bE1SWXdGQVlEVlFRTEV3MW9ZWGxoSUhsaFoyaHRiM1Z5TVJJd0VBWURWUVFERXdreE1qY3VNQzR3TGpFd1ZqQVFCZ2NxaGtqT1BRSUJCZ1VyZ1FRQUNnTkNBQVRUQUs5bHJUVmtvOXJrcTZaWWNjOUhEUlpQNGI5UzR6QTRLbTdZWEorc25UVmhMa3pVMEhzbVNYOVVuOGpEaFJUT0hES2FmdDhDL3V1VVk5MzR2dU1ObzRJQ0p6Q0NBaU13Z1lnR0ExVWRFUVNCZ0RCK3BId3dlakViTUJrR0ExVUVCQXdTTVMxb1lYbGhmREl0TWpNMGZETXRNVEV5TVI4d0hRWUtDWkltaVpQeUxHUUJBUXdQTXpBd01EYzFOVGc0TnpBd01EQXpNUTB3Q3dZRFZRUU1EQVF4TVRBd01SRXdEd1lEVlFRYURBaGFZWFJqWVNBeE1qRVlNQllHQTFVRUR3d1BSbTl2WkNCQ2RYTnphVzVsYzNNek1CMEdBMVVkRGdRV0JCU2dtSVdENmJQZmJiS2ttVHdPSlJYdkliSDlIakFmQmdOVkhTTUVHREFXZ0JSMllJejdCcUNzWjFjMW5jK2FyS2NybVRXMUx6Qk9CZ05WSFI4RVJ6QkZNRU9nUWFBL2hqMW9kSFJ3T2k4dmRITjBZM0pzTG5waGRHTmhMbWR2ZGk1ellTOURaWEowUlc1eWIyeHNMMVJUV2tWSlRsWlBTVU5GTFZOMVlrTkJMVEV1WTNKc01JR3RCZ2dyQmdFRkJRY0JBUVNCb0RDQm5UQnVCZ2dyQmdFRkJRY3dBWVppYUhSMGNEb3ZMM1J6ZEdOeWJDNTZZWFJqWVM1bmIzWXVjMkV2UTJWeWRFVnVjbTlzYkM5VVUxcEZhVzUyYjJsalpWTkRRVEV1WlhoMFoyRjZkQzVuYjNZdWJHOWpZV3hmVkZOYVJVbE9WazlKUTBVdFUzVmlRMEV0TVNneEtTNWpjblF3S3dZSUt3WUJCUVVITUFHR0gyaDBkSEE2THk5MGMzUmpjbXd1ZW1GMFkyRXVaMjkyTG5OaEwyOWpjM0F3RGdZRFZSMFBBUUgvQkFRREFnZUFNQjBHQTFVZEpRUVdNQlFHQ0NzR0FRVUZCd01DQmdnckJnRUZCUWNEQXpBbkJna3JCZ0VFQVlJM0ZRb0VHakFZTUFvR0NDc0dBUVVGQndNQ01Bb0dDQ3NHQVFVRkJ3TURNQW9HQ0NxR1NNNDlCQU1DQTBrQU1FWUNJUUNWd0RNY3E2UE8rTWNtc0JYVXovdjFHZGhHcDdycVNhMkF4VEtTdjgzOElBSWhBT0JOREJ0OSszRFNsaWpvVmZ4enJkRGg1MjhXQzM3c21FZG9HV1ZyU3BHMQ=="
            zatca_secret = "Xlj15LyMCgSC66ObnEO/qVPfhSbs3kDTjWnGheYhfSs="
            conf.zatca_bsToken = zatca_bsToken
            conf.zatca_reqID = 'N/A'
            conf.zatca_secret = zatca_secret
        else:
            self.compliance_api('/production/csids', 0)
        conf.zatca_status = 'production credentials received.'
        conf.csr_otp = None

    def production_credentials_renew(self):
        conf = self.sudo()
        if not conf.is_zatca:
            raise exceptions.AccessDenied("Zatca is not activated.")
        if not conf.zatca_certificate_status:
            raise exceptions.MissingError("Register Certificate before proceeding.")
        if conf.csr_otp in [None, False]:
            raise exceptions.MissingError("OTP required")
        if self.zatca_is_sandbox:
            zatca_bsToken = "TUlJRDFEQ0NBM21nQXdJQkFnSVRid0FBZTNVQVlWVTM0SS8rNVFBQkFBQjdkVEFLQmdncWhrak9QUVFEQWpCak1SVXdFd1lLQ1pJbWlaUHlMR1FCR1JZRmJHOWpZV3d4RXpBUkJnb0praWFKay9Jc1pBRVpGZ05uYjNZeEZ6QVZCZ29Ka2lhSmsvSXNaQUVaRmdkbGVIUm5ZWHAwTVJ3d0dnWURWUVFERXhOVVUxcEZTVTVXVDBsRFJTMVRkV0pEUVMweE1CNFhEVEl5TURZeE1qRTNOREExTWxvWERUSTBNRFl4TVRFM05EQTFNbG93U1RFTE1Ba0dBMVVFQmhNQ1UwRXhEakFNQmdOVkJBb1RCV0ZuYVd4bE1SWXdGQVlEVlFRTEV3MW9ZWGxoSUhsaFoyaHRiM1Z5TVJJd0VBWURWUVFERXdreE1qY3VNQzR3TGpFd1ZqQVFCZ2NxaGtqT1BRSUJCZ1VyZ1FRQUNnTkNBQVRUQUs5bHJUVmtvOXJrcTZaWWNjOUhEUlpQNGI5UzR6QTRLbTdZWEorc25UVmhMa3pVMEhzbVNYOVVuOGpEaFJUT0hES2FmdDhDL3V1VVk5MzR2dU1ObzRJQ0p6Q0NBaU13Z1lnR0ExVWRFUVNCZ0RCK3BId3dlakViTUJrR0ExVUVCQXdTTVMxb1lYbGhmREl0TWpNMGZETXRNVEV5TVI4d0hRWUtDWkltaVpQeUxHUUJBUXdQTXpBd01EYzFOVGc0TnpBd01EQXpNUTB3Q3dZRFZRUU1EQVF4TVRBd01SRXdEd1lEVlFRYURBaGFZWFJqWVNBeE1qRVlNQllHQTFVRUR3d1BSbTl2WkNCQ2RYTnphVzVsYzNNek1CMEdBMVVkRGdRV0JCU2dtSVdENmJQZmJiS2ttVHdPSlJYdkliSDlIakFmQmdOVkhTTUVHREFXZ0JSMllJejdCcUNzWjFjMW5jK2FyS2NybVRXMUx6Qk9CZ05WSFI4RVJ6QkZNRU9nUWFBL2hqMW9kSFJ3T2k4dmRITjBZM0pzTG5waGRHTmhMbWR2ZGk1ellTOURaWEowUlc1eWIyeHNMMVJUV2tWSlRsWlBTVU5GTFZOMVlrTkJMVEV1WTNKc01JR3RCZ2dyQmdFRkJRY0JBUVNCb0RDQm5UQnVCZ2dyQmdFRkJRY3dBWVppYUhSMGNEb3ZMM1J6ZEdOeWJDNTZZWFJqWVM1bmIzWXVjMkV2UTJWeWRFVnVjbTlzYkM5VVUxcEZhVzUyYjJsalpWTkRRVEV1WlhoMFoyRjZkQzVuYjNZdWJHOWpZV3hmVkZOYVJVbE9WazlKUTBVdFUzVmlRMEV0TVNneEtTNWpjblF3S3dZSUt3WUJCUVVITUFHR0gyaDBkSEE2THk5MGMzUmpjbXd1ZW1GMFkyRXVaMjkyTG5OaEwyOWpjM0F3RGdZRFZSMFBBUUgvQkFRREFnZUFNQjBHQTFVZEpRUVdNQlFHQ0NzR0FRVUZCd01DQmdnckJnRUZCUWNEQXpBbkJna3JCZ0VFQVlJM0ZRb0VHakFZTUFvR0NDc0dBUVVGQndNQ01Bb0dDQ3NHQVFVRkJ3TURNQW9HQ0NxR1NNNDlCQU1DQTBrQU1FWUNJUUNWd0RNY3E2UE8rTWNtc0JYVXovdjFHZGhHcDdycVNhMkF4VEtTdjgzOElBSWhBT0JOREJ0OSszRFNsaWpvVmZ4enJkRGg1MjhXQzM3c21FZG9HV1ZyU3BHMQ=="
            zatca_secret = "Xlj15LyMCgSC66ObnEO/qVPfhSbs3kDTjWnGheYhfSs="
            conf.zatca_bsToken = zatca_bsToken
            conf.zatca_reqID = 'N/A'
            conf.zatca_secret = zatca_secret
        else:
            self.compliance_api('/production/csids', 1)
        conf.zatca_status = 'production credentials renewed.'
        conf.csr_otp = None

    def register_certificate(self):
        conf = self.sudo()
        if not conf.is_zatca:
            raise exceptions.AccessDenied("Zatca is not activated.")
        certificate = conf.csr_certificate
        if not certificate:
            conf.zatca_certificate_status = 0
            raise exceptions.MissingError("Certificate not found.")
        certificate = certificate.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '')\
                                 .replace(' ', '').replace('\n', '')
        for x in range(1, math.ceil(len(certificate) / 64)):
            certificate = certificate[:64 * x + x - 1] + '\n' + certificate[64 * x + x - 1:]
        certificate = "-----BEGIN CERTIFICATE-----\n" + certificate + "\n-----END CERTIFICATE-----"

        f = open('/tmp/zatca_cert.pem', 'w+')
        f.write(certificate)
        f.close()

        certificate_public_key = "openssl x509 -pubkey -noout -in /tmp/zatca_cert.pem"

        certificate_signature_algorithm = "openssl x509 -in /tmp/zatca_cert.pem -text -noout"
        zatca_cert_public_key = os.popen(certificate_public_key).read()
        zatca_cert_public_key = zatca_cert_public_key.replace('-----BEGIN PUBLIC KEY-----', '')\
                                                     .replace('-----END PUBLIC KEY-----', '')\
                                                     .replace('\n', '').replace(' ', '')
        conf.zatca_cert_public_key = zatca_cert_public_key
        cert = os.popen(certificate_signature_algorithm).read()
        cert_find = cert.rfind("Signature Algorithm: ecdsa-with-SHA256")
        if cert_find > 0 and cert_find + 38 < len(cert):
            cert_sig_algo = cert[cert.rfind("Signature Algorithm: ecdsa-with-SHA256") + 38:].replace('\n', '')\
                                                                                            .replace(':', '')\
                                                                                            .replace(' ', '')
            conf.zatca_cert_sig_algo = cert_sig_algo
        else:
            raise exceptions.ValidationError("Invalid Certificate Provided.")

        conf.zatca_certificate_status = 1
        # For security purpose, files should not exist out of odoo
        os.system('''rm  /tmp/zatca_cert.pem''')
        os.system('''rm  /tmp/zatca_cert_publickey.pem''')
        os.system('''rm  /tmp/zatca_cert_publickey.bin''')

    def error_message(self, response):
        if response.get('messsage', False):
            return response['message']
        elif response.get('errors', False):
            return response['errors']
        else:
            return str(response)
