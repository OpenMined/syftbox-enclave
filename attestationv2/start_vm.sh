#!/bin/bash -eux

FILE="$1"

if [ -z "$FILE" ]; then
  echo "Usage: $0 IMAGE_FILE"
fi

qemu-system-x86_64 \
  -nographic \
  -snapshot \
  -cpu host \
  -enable-kvm \
  -smp 4 \
  -m 4G \
  -drive if=virtio,format=raw,file="${FILE}" \
  -device virtio-net-pci,netdev=net0 --netdev user,id=net0,hostfwd=tcp::2222-:22 \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.fd