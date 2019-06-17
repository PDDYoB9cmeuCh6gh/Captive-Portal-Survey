#!/usr/bin/env bash

IFACE="wlan0"

service network-manager stop
# change hosts MAC address
ifconfig $IFACE down
macchanger -r $IFACE
ifconfig $IFACE up


# query all available wireless networks, filter out the relevant information (BSSID, ESSID, Encryption, Link Quality)
sudo iwlist $IFACE scan | grep -E "Address|Quality|Encryption|ESSID" \
						| sed -e "s/.*Address: \|.*Quality=\|\/[1-9].*$\|.*key:\|.*ESSID:\|\"//g" \
						> networks.txt


while read -r BSSID && read -r QUALITY && read -r ENC && read -r ESSID; do
	# set working directory
	DIR="./dumps/$BSSID $ESSID/"

	# ignore networks that are encrypted, weak, hidden or known
	if [ "$ENC" == "on" ] || [ $QUALITY -lt 10 ] || [ "$ESSID" == "" ] || [ -f "$DIR/traffic.pcap" ]
	then
		continue
	fi

	# create working dir for new open networks
	mkdir -p "$DIR"

	# connect to wifi network, start a traffic capture, request IP via DHCP
	ifconfig $IFACE up
	echo "Connecting to: $ESSID ($BSSID)"
	iwconfig $IFACE essid "$ESSID" key open
	tcpdump -i $IFACE -w "$DIR/traffic.pcap" &
	dhclient -v $IFACE

	# store DNS server addresses and execute retrieval script
	cat /etc/resolv.conf > "$DIR/resolv.conf"
	python3 probe.py "$DIR"
	echo "Script executed"

	# disconnect from network. tcpdump stops automatically
	dhclient -r $IFACE
	ifconfig $IFACE down
	echo "Disconnected from: $ESSID ($BSSID)"
	
done < networks.txt

rm networks.txt
