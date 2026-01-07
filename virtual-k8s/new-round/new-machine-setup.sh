#!/bin/bash
set -e
TEMPLATE_NO=9000
MACHINE_NO=104
MACHINE_NAME="colfax-2"
PUBKEY="/home/colfax/.ssh/macbook.pub"
MACHINE_IP="192.168.50.76"
MACHINE_IP="192.168.50.1"

sudo qm clone $TEMPLATE_NO $MACHINE_NO --name $MACHINE_NAME --full
sleep 10
sudo qm resize $MACHINE_NO scsi0 100G
sudo qm set $MACHINE_NO --sshkey $PUBKEY
sudo qm set $MACHINE_NO --ipconfig0 ip=$MACHINE_IP/24,gw=$GATEWAY_IP
sudo qm start $MACHINE_NO
