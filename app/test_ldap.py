import sys
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException
import config

print(f"Testing LDAP connection to {config.LDAP_HOST}:{config.LDAP_PORT}")
print(f"Bind User: {config.LDAP_BIND_USER}")
print(f"Base DN: {config.AD_BASE_DN}")

try:
    server = Server(config.LDAP_HOST, port=config.LDAP_PORT, use_ssl=config.LDAP_USE_SSL, get_info=ALL)
    conn = Connection(server, user=config.LDAP_BIND_USER, password=config.LDAP_BIND_PASSWORD, auto_bind=True, receive_timeout=5)
    
    print("BIND SUCCESSFUL")
    
    username = "tecnico.inventario"
    search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
    print(f"Searching for {search_filter}")
    
    conn.search(config.AD_BASE_DN, search_filter, search_scope=SUBTREE, attributes=['cn', 'mail', 'memberOf', 'distinguishedName', 'sAMAccountName'])
    
    if not conn.entries:
        print("USER NOT FOUND IN SEARCH")
    else:
        print(f"USER FOUND: {conn.entries[0]}")
        
    conn.unbind()
except Exception as e:
    print(f"EXCEPTION: {e}")
