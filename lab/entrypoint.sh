#!/usr/bin/env bash
set -euo pipefail

LIMITED_USER=ldapmod
LIMITED_PASS=ldapmodpass
WITNESS_PATH=/tmp/WEBMIN-H22-LDAP-MV
LDAP_HOST=ldap
LDAP_PORT=389
LDAP_BIND_DN="cn=admin,dc=lab,dc=invalid"
LDAP_BIND_PW=labldap
LDAP_USER_BASE="ou=People,dc=lab,dc=invalid"
LDAP_GROUP_BASE="ou=Groups,dc=lab,dc=invalid"
LDAP_USER_DN="uid=labuser,${LDAP_USER_BASE}"

install_gadgets() {
  if perl -MNet::LDAP -e 1 >/dev/null 2>&1 && command -v useradd >/dev/null; then
    echo "== gadgets present =="
    return 0
  fi
  echo "== apt-get install libnet-ldap-perl passwd =="
  apt-get update
  apt-get install -y --no-install-recommends libnet-ldap-perl passwd
  rm -rf /var/lib/apt/lists/*
  perl -MNet::LDAP -e 1
  command -v useradd >/dev/null
}

wait_ldap() {
  echo "== wait ldap ${LDAP_HOST}:${LDAP_PORT} ${LDAP_USER_DN} =="
  local i
  for i in $(seq 1 60); do
    if perl -e '
      use Net::LDAP;
      my $ldap = Net::LDAP->new($ARGV[0], port => $ARGV[1], timeout => 3) or exit 1;
      my $msg = $ldap->bind($ARGV[2], password => $ARGV[3]);
      exit 1 if $msg->code;
      my $rv = $ldap->search(base => $ARGV[4], scope => "base", filter => "(objectClass=posixAccount)");
      exit 1 if $rv->code || $rv->count < 1;
    ' "${LDAP_HOST}" "${LDAP_PORT}" "${LDAP_BIND_DN}" "${LDAP_BIND_PW}" "${LDAP_USER_DN}"; then
      echo "IOC ldap-ready attempt=${i}"
      return 0
    fi
    echo "IOC ldap-wait attempt=${i}"
    sleep 2
  done
  echo "ldap-not-ready" >&2
  return 1
}

write_ldap_client_conf() {
  cat >/etc/ldap.conf <<EOF
host ${LDAP_HOST}
port ${LDAP_PORT}
base dc=lab,dc=invalid
uri ldap://${LDAP_HOST}:${LDAP_PORT}
binddn ${LDAP_BIND_DN}
bindpw ${LDAP_BIND_PW}
nss_base_passwd ${LDAP_USER_BASE}
nss_base_group ${LDAP_GROUP_BASE}
ssl no
EOF
  chmod 644 /etc/ldap.conf
}

write_module_config() {
  local cfg=/etc/webmin/ldap-useradmin/config
  mkdir -p /etc/webmin/ldap-useradmin
  touch "${cfg}"
  local tmp
  tmp="$(mktemp)"
  grep -v -E '^(ldap_host|ldap_port|ldap_tls|login|pass|user_base|group_base|person|given|gecos|md5|samba_def|imap_def|other_class|secmode|home_base)=' \
    "${cfg}" >"${tmp}" || true
  cat >>"${tmp}" <<EOF
ldap_host=${LDAP_HOST}
ldap_port=${LDAP_PORT}
ldap_tls=0
login=${LDAP_BIND_DN}
pass=${LDAP_BIND_PW}
user_base=${LDAP_USER_BASE}
group_base=${LDAP_GROUP_BASE}
person=1
given=0
gecos=1
md5=0
samba_def=0
imap_def=0
other_class=inetOrgPerson
secmode=1
EOF
  mv "${tmp}" "${cfg}"
  chmod 600 "${cfg}"
}

write_acl() {
  local module="$1"
  local movehome="$2"
  local dest="/etc/webmin/${module}/${LIMITED_USER}.acl"
  mkdir -p "/etc/webmin/${module}"
  cat >"${dest}" <<EOF
noconfig=1
uedit_mode=0
gedit_mode=0
lowuid=0
lowgid=0
ucreate=0
gcreate=0
ugroups=*
logins=*
shells=*
home=/
umultiple=1
uuid=1
gmultiple=1
ggid=1
peopt=1
batch=0
batchdir=/
chuid=0
chgid=0
movehome=${movehome}
mothers=0
makehome=0
copy=0
cothers=0
dothers=0
export=0
calcuid=1
calcgid=1
autouid=1
autogid=1
useruid=1
usergid=1
delhome=0
udelete=0
urename=0
gdelete=0
grename=0
EOF
  chmod 600 "${dest}"
}

create_limited_user() {
  local users_file=/etc/webmin/miniserv.users
  local acl_file=/etc/webmin/webmin.acl
  local hash
  hash="$(perl -e 'print crypt($ARGV[0], q($6$webminh22salt$))' "${LIMITED_PASS}")"
  if ! grep -q "^${LIMITED_USER}:" "${users_file}"; then
    echo "${LIMITED_USER}:${hash}:0" >>"${users_file}"
  fi
  chmod 600 "${users_file}"
  if ! grep -q "^${LIMITED_USER}:" "${acl_file}"; then
    echo "${LIMITED_USER}: ldap-useradmin useradmin" >>"${acl_file}"
  fi
  chmod 600 "${acl_file}"
}

seed_homes() {
  mkdir -p /home/labuser /home/unixuser
  echo labkeep >/home/labuser/keep.txt
  echo unixkeep >/home/unixuser/keep.txt
  groupadd -g 1002 unixuser 2>/dev/null || true
  if ! id unixuser >/dev/null 2>&1; then
    useradd -u 1002 -g unixuser -d /home/unixuser -s /bin/sh -M unixuser
  fi
  chown -R 1001:1001 /home/labuser
  chown -R unixuser:unixuser /home/unixuser
  rm -f "${WITNESS_PATH}"
}

tweak_miniserv() {
  local conf=/etc/webmin/miniserv.conf
  grep -q '^ssl=0' "${conf}" || echo 'ssl=0' >>"${conf}"
  grep -q '^ipv6=' "${conf}" && sed -i 's/^ipv6=.*/ipv6=0/' "${conf}" || echo 'ipv6=0' >>"${conf}"
  grep -q '^nofork=1' "${conf}" || echo 'nofork=1' >>"${conf}"
}

install_gadgets
wait_ldap
write_ldap_client_conf
write_module_config
write_acl ldap-useradmin 2
write_acl useradmin 1
create_limited_user
seed_homes
tweak_miniserv

echo "== start miniserv =="
exec /usr/bin/perl /usr/share/webmin/miniserv.pl --nofork /etc/webmin/miniserv.conf
